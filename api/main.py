"""
api/main.py - FastAPI Service for IoT Fault Diagnosis & RAG Assistant
Endpoints:
- GET /health
- GET /model-info
- POST /predict
- POST /diagnose
- POST /telemetry
"""

import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ml.detector import FaultDetectorPipeline

app = FastAPI(
    title="Knowledge-Driven IoT Fault Diagnosis API",
    description="Real-time ML, RAG, and LLM-powered fault diagnosis for Offshore Oil & Gas wells using Petrobras 3W Dataset models.",
    version="2.0.0"
)

# Enable CORS for dashboard and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML + RAG Pipeline
detector = FaultDetectorPipeline()


class TelemetryInput(BaseModel):
    sensor_data: Dict[str, Any] = Field(..., description="Key-value dictionary of sensor telemetry parameters (e.g., P-PDG, P-TPT, T-TPT, etc.)")
    well_id: Optional[str] = Field("WELL-01", description="Identifier of the well or industrial asset")


class PredictionResponse(BaseModel):
    status: str
    predicted_event: str
    confidence: float
    binary_status: str
    binary_confidence: float
    multiclass_confidence: float
    class_probabilities: Dict[str, float]
    well_id: str


class DiagnosisResponse(BaseModel):
    status: str
    predicted_event_id: int
    predicted_event: str
    confidence: float
    binary_status: str
    raw_diagnosis: str
    retrieved_sources: List[str]
    sensor_evidence: Optional[List[Dict[str, Any]]] = None
    well_id: str


@app.get("/health")
def health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "IoT Fault Diagnosis API",
        "models_loaded": {
            "binary_model": detector.binary_model is not None,
            "multiclass_model": detector.multiclass_model is not None,
            "anomaly_model": detector.anomaly_model is not None,
            "imputer": detector.imputer is not None,
            "rag_vector_store": detector.retriever is not None
        }
    }


@app.get("/model-info")
def model_info():
    """Retrieve model metadata, architecture details, and feature count."""
    return {
        "dataset": "Petrobras 3W Dataset 2.0.0 (Real Well Parquet Files)",
        "features_count": len(detector.feature_cols),
        "primary_sensors": [
            "P-PDG", "P-TPT", "T-TPT", "P-MON-CKP", "T-JUS-CKP", 
            "P-ANULAR", "T-PDG", "P-JUS-CKGL", "QGL", "ABER-CKP"
        ],
        "classes_supported": [
            "0: Normal Operation",
            "1: Abrupt Increase of BSW",
            "2: Spurious Closure of DHSV",
            "3: Severe Slugging",
            "4: Flow Instability",
            "5: Rapid Productivity Loss",
            "6: Quick Restriction in PCK",
            "7: Scaling in PCK",
            "8: Hydrate in Production Line",
            "9: Hydrate in Service Line"
        ],
        "models": {
            "binary": "RandomForestClassifier (Balanced, max_depth=15)",
            "multiclass": "RandomForestClassifier (Balanced, max_depth=14)",
            "anomaly": "IsolationForest (Unsupervised baseline on Normal envelope)"
        },
        "rag_knowledge_base": "Indexed Oil & Gas Engineering SOP & Technical Documentation"
    }


@app.post("/predict", response_model=PredictionResponse)
def predict_fault(telemetry: TelemetryInput):
    """
    Predict whether sensor telemetry is normal or anomalous, and classify the specific fault event.
    """
    try:
        result = detector.predict(telemetry.sensor_data, well_id=telemetry.well_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/diagnose", response_model=DiagnosisResponse)
def diagnose_fault(telemetry: TelemetryInput):
    """
    Perform full ML prediction + RAG Technical Knowledge Retrieval + LLM structured fault diagnosis.
    """
    try:
        result = detector.diagnose(telemetry.sensor_data, well_id=telemetry.well_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis error: {str(e)}")


@app.post("/telemetry")
def ingest_telemetry(telemetry: TelemetryInput):
    """
    Ingest live telemetry snapshot, evaluate ML status, and return immediate alert flags.
    """
    try:
        res = detector.predict(telemetry.sensor_data, well_id=telemetry.well_id)
        alert = res["status"] == "anomaly"
        return {
            "acknowledged": True,
            "well_id": telemetry.well_id,
            "alert": alert,
            "status": res["status"],
            "event": res["predicted_event"],
            "confidence": res["confidence"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Telemetry ingestion error: {str(e)}")


@app.get("/stats")
def get_stats():
    """Retrieve high-level telemetry and fault statistics from PostgreSQL database."""
    from database.db import get_telemetry_stats
    return get_telemetry_stats()


@app.get("/wells")
def get_wells():
    """Retrieve list of distinct monitored well identifiers."""
    from database.db import get_distinct_well_ids
    return {"wells": get_distinct_well_ids()}


@app.get("/incidents")
def get_incidents(limit: int = 50, well_id: Optional[str] = None):
    """Retrieve recent fault incidents logged in PostgreSQL."""
    from database.db import get_recent_incidents
    return {"incidents": get_recent_incidents(limit=limit, well_id=well_id)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

