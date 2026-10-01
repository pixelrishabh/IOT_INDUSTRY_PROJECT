"""
prepare_dataset.py - Audited Preprocessing & Feature Extraction Pipeline
for Petrobras 3W Dataset 2.0.0 (Real Well Parquet Files).

Audited Pipeline Enhancements:
1. Causal Imputation: Uses strictly causal forward-fill with limit=60s (NO backward-fill).
2. Defensible Class Label Policy: Unannotated windows (all NaN labels in raw file) are explicitly dropped.
   Mixed-label transition windows prioritize active fault/transient annotations (max non-null).
3. Transient Tracking: Preserves raw transient labels (101-109) and flags transient windows for separate evaluation.
4. Leakage Prevention: Splitting is performed at the Recording-Instance level (instance_file),
   ensuring complete temporal isolation of continuous recordings.
5. Physical Well Tracking: Tracks well_id across partitions to analyze and document cross-well vs instance-level generalization.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
import joblib

# Core continuous sensor variables present in 3W Dataset
PRIMARY_SENSORS = [
    "P-PDG",       # Pressure at Permanent Downhole Gauge (Pa)
    "P-TPT",       # Pressure at Temperature & Pressure Transducer (Pa)
    "T-TPT",       # Temperature at Temperature & Pressure Transducer (°C)
    "P-MON-CKP",   # Upstream Pressure of Production Choke (Pa)
    "T-JUS-CKP",   # Downstream Temperature of Production Choke (°C)
    "P-ANULAR",    # Annulus Pressure (Pa)
    "T-PDG",       # Temperature at Permanent Downhole Gauge (°C)
    "P-JUS-CKGL",  # Downstream Pressure of Gas Lift Choke (Pa)
    "QGL",         # Gas Lift Flow Rate (m3/s)
    "ABER-CKP",    # Production Choke Opening (%)
    "ABER-CKGL",   # Gas Lift Choke Opening (%)
    "T-MON-CKP",   # Upstream Temperature of Production Choke (°C)
    "P-JUS-CKP",   # Downstream Pressure of Production Choke (Pa)
]

# Official Petrobras 3W 2.0.0 Event Descriptions
EVENT_DESCRIPTIONS = {
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
    101: "Transient - Abrupt Increase of BSW",
    102: "Transient - Spurious Closure of DHSV",
    105: "Transient - Rapid Productivity Loss",
    106: "Transient - Quick Restriction in PCK",
    107: "Transient - Scaling in PCK",
    108: "Transient - Hydrate in Production Line",
    109: "Transient - Hydrate in Service Line",
}


def sanitize_sensor_readings(df: pd.DataFrame, sensors: List[str]) -> pd.DataFrame:
    """
    Filter out SCADA sentinel errors (e.g. disconnected tags sending -1e38)
    and replace non-physical measurements with NaN for causal imputation.
    """
    for col in sensors:
        if col not in df.columns:
            continue
        series = df[col]
        if col.startswith("P-") or col.startswith("PT-"):
            # Valid offshore pressure: 0 to 1.5e8 Pa (0 to 1500 bar)
            mask = (series < -1e4) | (series > 2e8)
        elif col.startswith("T-"):
            # Valid offshore temperature: -40 to 350 °C
            mask = (series < -50) | (series > 400)
        elif col.startswith("ABER-"):
            # Valve choke opening: 0 to 100%
            mask = (series < 0) | (series > 100)
        elif col.startswith("Q"):
            # Gas / liquid volumetric flowrate
            mask = (series < 0) | (series > 1e4)
        else:
            mask = (series < -1e6) | (series > 1e10)

        if mask.any():
            df.loc[mask, col] = np.nan
    return df


def extract_window_features_from_file(
    file_path: Path,
    window_sec: int = 60,
    ffill_limit: int = 60
) -> pd.DataFrame:
    """
    Extract 60-second window statistical features from a single real WELL parquet file
    using strictly causal forward-fill and principled window label aggregation.
    """
    try:
        df = pd.read_parquet(file_path)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    # Identify numeric sensor columns available in this file
    available_sensors = [
        c for c in PRIMARY_SENSORS if c in df.columns and pd.api.types.is_numeric_dtype(df[c])
    ]
    if not available_sensors:
        available_sensors = [
            c for c in df.columns 
            if c not in ["class", "state"] and pd.api.types.is_numeric_dtype(df[c])
        ]

    # Ensure timestamp datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
        else:
            df.index = pd.to_datetime(df.index)

    # Sanitize physical sensor sentinels
    df = sanitize_sensor_readings(df, available_sensors)
    
    # Strictly CAUSAL forward-fill with limit (NO backward-fill to prevent lookahead bias)
    sensor_df = df[available_sensors].ffill(limit=ffill_limit)

    # Resample to 60-second non-overlapping windows
    rule = f"{window_sec}s"
    resampled = sensor_df.resample(rule)

    mean_df = resampled.mean().add_suffix("_mean")
    std_df = resampled.std().fillna(0.0).add_suffix("_std")
    min_df = resampled.min().add_suffix("_min")
    max_df = resampled.max().add_suffix("_max")
    median_df = resampled.median().add_suffix("_median")
    
    # Range = max - min
    range_df = (max_df.values - min_df.values)
    range_cols = [f"{s}_range" for s in available_sensors]
    range_df = pd.DataFrame(range_df, index=mean_df.index, columns=range_cols)

    # Trend = last value - first value in window (rate of rise / fall)
    first_df = resampled.first()
    last_df = resampled.last()
    trend_df = (last_df - first_df).fillna(0.0).add_suffix("_trend")

    # Combine all statistical features
    features = pd.concat([mean_df, std_df, min_df, max_df, median_df, range_df, trend_df], axis=1)

    # ---------------------------------------------------------
    # PRINCIPLED CLASS LABEL AGGREGATION
    # ---------------------------------------------------------
    # In 3W 2.0.0, the 'class' column contains expert ground-truth annotations:
    # 0 = Normal, 1..9 = Fault events, 101..109 = Incipient transients.
    # Unannotated buffer periods are stored as <NA>.
    if "class" in df.columns:
        def aggregate_window_label(window_series):
            valid = window_series.dropna()
            if valid.empty:
                return np.nan # Entire 60s window has no expert ground truth -> Exclude
            # Prioritize active fault/transient annotations (max non-null integer)
            return int(valid.max())

        class_resampled = df["class"].resample(rule).apply(aggregate_window_label)
    else:
        folder_name = file_path.parent.name
        default_folder_label = int(folder_name) if folder_name.isdigit() else 0
        class_resampled = pd.Series(default_folder_label, index=features.index)

    features["raw_class"] = class_resampled

    # Filter out unannotated windows (where class is NaN)
    features = features[features["raw_class"].notna()].copy()
    if features.empty:
        return pd.DataFrame()

    features["raw_class"] = features["raw_class"].astype(int)

    # Flag transient windows (classes 101-109) for separate evaluation
    features["is_transient"] = (features["raw_class"] >= 100).astype(int)

    # Map transient classes (100 + k) to their base event class (k) for multi-class classification
    def map_multiclass(c):
        if c >= 100:
            return c - 100
        return c

    features["multiclass"] = features["raw_class"].apply(map_multiclass)
    
    # Binary target: 0 = Normal, 1 = Fault / Transient
    features["binary_target"] = (features["raw_class"] > 0).astype(int)

    # Track metadata
    features["instance_file"] = file_path.name
    features["well_id"] = file_path.name.split("_")[0]
    features["event_folder"] = file_path.parent.name

    # Drop windows where all sensor measurements are NaN
    valid_mask = mean_df.loc[features.index].notna().any(axis=1)
    features = features[valid_mask]

    return features


def build_dataset(
    dataset_root: str = "Dstaset/3w_dataset_2.0.0",
    output_dir: str = "data",
    models_dir: str = "models",
    window_sec: int = 60,
    test_size: float = 0.20,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process all real WELL files in Petrobras 3W dataset, extract features,
    perform recording-instance split, impute missing features, and save processed datasets.
    """
    dataset_path = Path(dataset_root)
    real_files = sorted(list(dataset_path.glob("*/WELL-*.parquet")))
    print("==================================================")
    print(f"AUDITED FEATURE PIPELINE: PETROBRAS 3W DATASET 2.0.0")
    print(f"Found {len(real_files)} real WELL parquet files.")
    print(f"Window size: {window_sec}s | Causal ffill limit: {window_sec}s (NO lookahead bfill)")
    print("==================================================")

    start_time = time.time()
    all_instances = []

    for idx, file_path in enumerate(real_files):
        inst_df = extract_window_features_from_file(file_path, window_sec=window_sec, ffill_limit=window_sec)
        if not inst_df.empty:
            all_instances.append(inst_df)
        
        if (idx + 1) % 100 == 0 or (idx + 1) == len(real_files):
            elapsed = time.time() - start_time
            print(f"[{idx+1}/{len(real_files)}] files processed ({elapsed:.1f}s)...", flush=True)

    if not all_instances:
        raise ValueError("No valid features extracted from dataset files!")

    full_df = pd.concat(all_instances, ignore_index=True)
    print(f"\nExtracted total {len(full_df)} annotated window feature records from {len(real_files)} files.")

    # Metadata and label columns to exclude from feature matrix
    meta_cols = ["raw_class", "multiclass", "binary_target", "is_transient", "instance_file", "well_id", "event_folder"]
    feature_cols = [c for c in full_df.columns if c not in meta_cols]
    
    # Clip any residual extreme numeric artifacts to valid float32 boundaries
    full_df[feature_cols] = full_df[feature_cols].clip(-1e9, 1e9)

    # Save feature columns definition
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    with open(Path(models_dir) / "feature_columns.json", "w") as f:
        json.dump(feature_cols, f, indent=2)
    print(f"Saved {len(feature_cols)} feature column names to {models_dir}/feature_columns.json")

    # Display class distribution
    print("\nAnnotated Window Counts by Multi-Class Event:")
    for c, count in full_df["multiclass"].value_counts().sort_index().items():
        desc = EVENT_DESCRIPTIONS.get(c, "Unknown")
        pct = (count / len(full_df)) * 100
        print(f"  Class {c:2d} ({desc:30s}): {count:7d} windows ({pct:5.2f}%)")

    print("\nTransient vs Established Fault Breakdown:")
    transient_cnt = full_df["is_transient"].sum()
    established_fault_cnt = (full_df["binary_target"] == 1).sum() - transient_cnt
    print(f"  Normal (Class 0)         : {(full_df['binary_target'] == 0).sum():7d} windows")
    print(f"  Transient (Classes 101+) : {transient_cnt:7d} windows ({transient_cnt/(transient_cnt+established_fault_cnt)*100:.1f}% of faults)")
    print(f"  Established Faults (1-9) : {established_fault_cnt:7d} windows")

    # =========================================================================
    # RECORDING-INSTANCE-LEVEL SPLITTING (DATA LEAKAGE PREVENTION)
    # =========================================================================
    unique_instances = full_df[["instance_file", "event_folder", "well_id"]].drop_duplicates(subset=["instance_file"])
    
    train_inst, test_inst = train_test_split(
        unique_instances["instance_file"],
        test_size=test_size,
        random_state=random_state,
        stratify=unique_instances["event_folder"]
    )

    train_mask = full_df["instance_file"].isin(train_inst)
    test_mask = full_df["instance_file"].isin(test_inst)

    train_df = full_df[train_mask].copy()
    test_df = full_df[test_mask].copy()

    # Physical Well Overlap Analysis
    train_wells = set(train_df["well_id"].unique())
    test_wells = set(test_df["well_id"].unique())
    overlap_wells = train_wells.intersection(test_wells)

    print(f"\n==================================================")
    print(f"RECORDING-INSTANCE SPLIT AUDIT:")
    print(f"Train Instances: {len(train_inst)} recordings -> {len(train_df)} windows ({len(train_df)/len(full_df)*100:.1f}%)")
    print(f"Test Instances : {len(test_inst)} recordings -> {len(test_df)} windows ({len(test_df)/len(full_df)*100:.1f}%)")
    print(f"Physical Wells in Train: {len(train_wells)} | Physical Wells in Test: {len(test_wells)}")
    print(f"Overlapping Physical Wells: {len(overlap_wells)} (Different temporal recordings from same assets)")
    print(f"==================================================")

    # =========================================================================
    # IMPUTATION (FITTED ONLY ON TRAIN FEATURES)
    # =========================================================================
    print("Fitting SimpleImputer(strategy='median') strictly on Training set features...", flush=True)
    imputer = SimpleImputer(strategy="median")
    imputer.fit(train_df[feature_cols])

    # Apply imputation & convert to float32
    train_df[feature_cols] = imputer.transform(train_df[feature_cols]).astype(np.float32)
    test_df[feature_cols] = imputer.transform(test_df[feature_cols]).astype(np.float32)
    full_df[feature_cols] = imputer.transform(full_df[feature_cols]).astype(np.float32)

    # Save Imputer
    imputer_path = Path(models_dir) / "feature_imputer.joblib"
    joblib.dump(imputer, imputer_path)
    print(f"Saved feature imputer to {imputer_path}")

    # =========================================================================
    # SAVE PROCESSED DATASETS
    # =========================================================================
    full_parquet_path = Path(output_dir) / "processed_3w_features.parquet"
    train_parquet_path = Path(output_dir) / "train_features.parquet"
    test_parquet_path = Path(output_dir) / "test_features.parquet"

    full_df.to_parquet(full_parquet_path, index=False)
    train_df.to_parquet(train_parquet_path, index=False)
    test_df.to_parquet(test_parquet_path, index=False)

    print(f"Saved full feature dataset to:  {full_parquet_path}")
    print(f"Saved train feature dataset to: {train_parquet_path}")
    print(f"Saved test feature dataset to:  {test_parquet_path}")

    # Save a sample CSV for verification
    sample_csv_path = Path(output_dir) / "processed_features_sample.csv"
    full_df.head(500).to_csv(sample_csv_path, index=False)
    print(f"Saved sample CSV to:            {sample_csv_path}")

    return train_df, test_df


if __name__ == "__main__":
    build_dataset()
