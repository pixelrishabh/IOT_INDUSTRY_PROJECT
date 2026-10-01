"""
detector.py - Real-Time End-to-End Fault Detection & Diagnosis Pipeline
Performs:
1. Raw Sensor Ingestion & 60s Window Feature Generation
2. Missing Feature Imputation
3. Unsupervised Anomaly Detection (IsolationForest)
4. Binary Fault Classification (Normal vs Fault)
5. Multi-Class Fault Classification (Events 0-9)
6. Physical Sensor Evidence Extraction
7. RAG Technical Knowledge Retrieval
8. LLM Structured Fault Diagnosis Generation
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd

from llm.diagnosis import DiagnosisEngine
from rag.retriever import FaultKnowledgeRetriever

# Standard 3W Event Label Descriptions
EVENT_MAPPING = {
    0: "Normal Operation",
    1: "Abrupt Increase of BSW",
    2: "Spurious Closure of DHSV",
    3: "Severe Slugging",
    4: "Flow Instability",
    5: "Rapid Productivity Loss",
    6: "Quick Restriction in PCK",
    7: "Scaling in PCK",
    8: "Hydrate in Production Line",
    9: "Hydrate in Service Line",
}

# Nominal operating envelopes for standard offshore sensors (for evidence detection)
NOMINAL_BOUNDS = {
    "P-PDG": (200e5, 350e5, "200 - 350 bar (Downhole Pressure)"),
    "P-TPT": (100e5, 200e5, "100 - 200 bar (Transducer Pressure)"),
    "T-TPT": (50.0, 95.0, "50 - 95 °C (Transducer Temperature)"),
    "P-MON-CKP": (80e5, 180e5, "80 - 180 bar (Upstream Choke Pressure)"),
    "T-JUS-CKP": (30.0, 80.0, "30 - 80 °C (Downstream Choke Temperature)"),
    "P-ANULAR": (0.0, 40e5, "0 - 40 bar (Annulus 'A' Pressure)"),
    "T-PDG": (60.0, 120.0, "60 - 120 °C (Downhole Gauge Temperature)"),
    "QGL": (0.0, 50.0, "Nominal Gas Lift Injection Rate"),
    "ABER-CKP": (10.0, 100.0, "10 - 100% Choke Opening"),
}


class FaultDetectorPipeline:
    def __init__(
        self,
        models_dir: str = "models",
        rag_store_dir: str = "rag/vector_store"
    ):
        self.models_dir = Path(models_dir)
        self.rag_store_dir = rag_store_dir

        self.feature_cols: List[str] = []
        self.imputer = None
        self.binary_model = None
        self.multiclass_model = None
        self.anomaly_model = None
        
        self.retriever: Optional[FaultKnowledgeRetriever] = None
        self.diagnosis_engine: Optional[DiagnosisEngine] = None
        
        self._load_artifacts()

    def _load_artifacts(self):
        """Load trained models, feature definitions, and RAG/LLM engines."""
        feat_path = self.models_dir / "feature_columns.json"
        imputer_path = self.models_dir / "feature_imputer.joblib"
        binary_path = self.models_dir / "binary_fault_model.joblib"
        multi_path = self.models_dir / "multiclass_fault_model.joblib"
        anomaly_path = self.models_dir / "isolation_forest_model.joblib"

        if feat_path.exists():
            with open(feat_path, "r") as f:
                self.feature_cols = json.load(f)

        if imputer_path.exists():
            self.imputer = joblib.load(imputer_path)

        if binary_path.exists():
            self.binary_model = joblib.load(binary_path)

        if multi_path.exists():
            self.multiclass_model = joblib.load(multi_path)

        if anomaly_path.exists():
            self.anomaly_model = joblib.load(anomaly_path)

        try:
            self.retriever = FaultKnowledgeRetriever(store_dir=self.rag_store_dir)
            self.diagnosis_engine = DiagnosisEngine(retriever=self.retriever)
        except Exception as e:
            print(f"[FaultDetectorPipeline] Note initializing RAG/LLM: {e}")

    def prepare_features(self, sensor_data: Union[Dict[str, float], pd.DataFrame, List[Dict[str, float]]]) -> np.ndarray:
        """
        Convert raw sensor dictionary or time series window into the expected 91 feature vector.
        """
        if isinstance(sensor_data, dict):
            # Single telemetry snapshot or precomputed features
            # If precomputed keys match feature_cols
            row_dict = {}
            for col in self.feature_cols:
                if col in sensor_data and sensor_data[col] is not None:
                    try:
                        row_dict[col] = float(sensor_data[col])
                    except (ValueError, TypeError):
                        row_dict[col] = np.nan
                else:
                    # If base sensor name given (e.g. 'P-PDG'), map to stats
                    base_sensor = col.split("_")[0]
                    stat = col.split("_")[1] if "_" in col else "mean"
                    if base_sensor in sensor_data and sensor_data[base_sensor] is not None:
                        try:
                            val = float(sensor_data[base_sensor])
                            if stat in ["mean", "min", "max", "median"]:
                                row_dict[col] = val
                            elif stat in ["std", "range", "trend"]:
                                row_dict[col] = 0.0
                            else:
                                row_dict[col] = val
                        except (ValueError, TypeError):
                            row_dict[col] = np.nan
                    else:
                        row_dict[col] = np.nan

            df = pd.DataFrame([row_dict], columns=self.feature_cols)

        elif isinstance(sensor_data, pd.DataFrame):
            # Time-series dataframe over 60 seconds
            if len(sensor_data) > 1:
                # 1. Sanitize SCADA sentinels
                clean_df = sensor_data.copy()
                for col in clean_df.columns:
                    if col.startswith("P-") or col.startswith("PT-"):
                        mask = (clean_df[col] < -1e4) | (clean_df[col] > 2e8)
                        clean_df.loc[mask, col] = np.nan
                    elif col.startswith("T-"):
                        mask = (clean_df[col] < -50) | (clean_df[col] > 400)
                        clean_df.loc[mask, col] = np.nan
                    elif col.startswith("ABER-"):
                        mask = (clean_df[col] < 0) | (clean_df[col] > 100)
                        clean_df.loc[mask, col] = np.nan
                    elif col.startswith("Q"):
                        mask = (clean_df[col] < 0) | (clean_df[col] > 1e4)
                        clean_df.loc[mask, col] = np.nan

                # 2. Causal forward-fill with 60s limit (NO lookahead bfill)
                clean_df = clean_df.ffill(limit=60)

                # 3. Compute statistical features across window
                feature_dict = {}
                for col in self.feature_cols:
                    base_sensor = col.split("_")[0]
                    stat = col.split("_")[1] if "_" in col else "mean"
                    if base_sensor in clean_df.columns:
                        series = clean_df[base_sensor].dropna()
                        if not series.empty:
                            if stat == "mean":
                                feature_dict[col] = series.mean()
                            elif stat == "std":
                                feature_dict[col] = series.std() if len(series) > 1 else 0.0
                            elif stat == "min":
                                feature_dict[col] = series.min()
                            elif stat == "max":
                                feature_dict[col] = series.max()
                            elif stat == "median":
                                feature_dict[col] = series.median()
                            elif stat == "range":
                                feature_dict[col] = series.max() - series.min()
                            elif stat == "trend":
                                feature_dict[col] = series.iloc[-1] - series.iloc[0]
                        else:
                            feature_dict[col] = np.nan
                    else:
                        feature_dict[col] = np.nan
                df = pd.DataFrame([feature_dict], columns=self.feature_cols)
            else:
                # Single row dataframe
                df = sensor_data.reindex(columns=self.feature_cols)
        else:
            df = pd.DataFrame(sensor_data).reindex(columns=self.feature_cols)

        # Apply imputer
        if self.imputer is not None:
            features_imputed = self.imputer.transform(df)
        else:
            features_imputed = df.fillna(0.0).values

        return features_imputed.astype(np.float32)

    def extract_sensor_evidence(self, sensor_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify which sensor readings deviate from nominal baseline boundaries."""
        evidence = []
        for sensor, (low, high, desc) in NOMINAL_BOUNDS.items():
            if sensor in sensor_data and sensor_data[sensor] is not None:
                try:
                    val = float(sensor_data[sensor])
                    if val < low:
                        diff_pct = ((low - val) / (low if low != 0 else 1)) * 100
                        evidence.append({
                            "sensor": sensor,
                            "observed_value": f"{val:.2f}",
                            "expected_behavior": f">= {low:.1f} (Nominal: {desc})",
                            "status": "ABNORMALLY LOW",
                            "significance": f"Deficit of {diff_pct:.1f}% below minimum nominal threshold"
                        })
                    elif val > high:
                        diff_pct = ((val - high) / (high if high != 0 else 1)) * 100
                        evidence.append({
                            "sensor": sensor,
                            "observed_value": f"{val:.2f}",
                            "expected_behavior": f"<= {high:.1f} (Nominal: {desc})",
                            "status": "ABNORMALLY HIGH",
                            "significance": f"Surge of {diff_pct:.1f}% above maximum nominal threshold"
                        })
                except (ValueError, TypeError):
                    continue
        return evidence

    def predict(
        self,
        sensor_data: Union[Dict[str, float], pd.DataFrame],
        well_id: str = "WELL-01"
    ) -> Dict[str, Any]:
        """
        Fast ML inference endpoint returning status, predicted event, and confidence.
        """
        X = self.prepare_features(sensor_data)

        # Binary Model
        is_anomaly = False
        binary_confidence = 0.5
        if self.binary_model is not None:
            bin_pred = self.binary_model.predict(X)[0]
            bin_proba = self.binary_model.predict_proba(X)[0]
            is_anomaly = bool(bin_pred == 1)
            binary_confidence = float(bin_proba[1] if is_anomaly else bin_proba[0])

        # Multi-Class Model
        event_id = 0
        event_name = "Normal Operation"
        multi_confidence = 0.5
        class_probas = {}

        if self.multiclass_model is not None:
            multi_pred = self.multiclass_model.predict(X)[0]
            multi_proba = self.multiclass_model.predict_proba(X)[0]
            event_id = int(multi_pred)
            event_name = EVENT_MAPPING.get(event_id, f"Event {event_id}")
            
            # Map probabilities to class names
            if hasattr(self.multiclass_model, "classes_"):
                for cls, prob in zip(self.multiclass_model.classes_, multi_proba):
                    class_probas[EVENT_MAPPING.get(int(cls), f"Class {cls}")] = round(float(prob), 4)

            multi_confidence = float(np.max(multi_proba))

        # Overall Status
        if is_anomaly or event_id > 0:
            status = "anomaly"
            overall_confidence = max(binary_confidence, multi_confidence) if event_id > 0 else binary_confidence
        else:
            status = "normal"
            overall_confidence = binary_confidence

        return {
            "status": status,
            "predicted_event_id": event_id,
            "predicted_event": event_name if status == "anomaly" else "Normal Operation",
            "confidence": round(overall_confidence, 4),
            "binary_status": "FAULT" if is_anomaly else "NORMAL",
            "binary_confidence": round(binary_confidence, 4),
            "multiclass_confidence": round(multi_confidence, 4),
            "class_probabilities": class_probas,
            "well_id": well_id
        }

    def diagnose(
        self,
        sensor_data: Union[Dict[str, float], pd.DataFrame],
        well_id: str = "WELL-01"
    ) -> Dict[str, Any]:
        """
        Full ML + RAG + LLM Diagnosis pipeline.
        """
        # 1. Run ML prediction
        prediction = self.predict(sensor_data, well_id=well_id)

        # 2. Extract sensor evidence
        raw_dict = sensor_data if isinstance(sensor_data, dict) else sensor_data.iloc[-1].to_dict()
        sensor_evidence = self.extract_sensor_evidence(raw_dict)

        # 3. Synthesize structured diagnosis with RAG + LLM
        if self.diagnosis_engine is not None:
            diagnosis_res = self.diagnosis_engine.generate_diagnosis(
                status=prediction["status"].upper(),
                predicted_event_id=prediction["predicted_event_id"],
                predicted_event_name=prediction["predicted_event"],
                confidence=prediction["confidence"],
                sensor_evidence=sensor_evidence,
                well_id=well_id,
                binary_status=prediction["binary_status"],
                class_probabilities=prediction["class_probabilities"]
            )
            prediction.update(diagnosis_res)
        else:
            prediction["raw_diagnosis"] = "RAG & LLM diagnosis engine initializing."
            prediction["sensor_evidence"] = sensor_evidence

        return prediction
