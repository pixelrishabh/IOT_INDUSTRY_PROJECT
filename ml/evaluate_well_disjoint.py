"""
evaluate_well_disjoint.py - Physical Well-Disjoint Generalization Evaluation
Evaluates model performance when trained on one set of physical wells and tested
on entirely unseen physical wells (zero asset overlap).

Highlights the distinction between:
1. Recording-Instance Level Generalization (same wells, new time windows)
2. Physical-Well Disjoint Generalization (zero-shot transfer to unseen wellbores)
"""

import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit


def run_well_disjoint_evaluation(
    data_dir: str = "data",
    results_dir: str = "results",
    random_state: int = 42
):
    print("==================================================")
    print("PHYSICAL WELL-DISJOINT GENERALIZATION EVALUATION")
    print("==================================================")

    os.makedirs(results_dir, exist_ok=True)
    full_path = Path(data_dir) / "processed_3w_features.parquet"
    feat_cols_path = Path("models/feature_columns.json")

    full_df = pd.read_parquet(full_path)
    with open(feat_cols_path, "r") as f:
        feature_cols = json.load(f)

    # Perform strict GroupShuffleSplit on physical well_id
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=random_state)
    train_idx, test_idx = next(gss.split(full_df, groups=full_df["well_id"]))

    train_df = full_df.iloc[train_idx].copy()
    test_df = full_df.iloc[test_idx].copy()

    train_wells = set(train_df["well_id"].unique())
    test_wells = set(test_df["well_id"].unique())
    overlap = train_wells.intersection(test_wells)

    print(f"Total physical wells: {full_df['well_id'].nunique()}")
    print(f"Train Wells ({len(train_wells)} wells): {sorted(list(train_wells))}")
    print(f"Test Wells  ({len(test_wells)} wells): {sorted(list(test_wells))}")
    print(f"Overlapping Wells: {len(overlap)} (Strictly Disjoint)")

    # Impute using train fit
    imputer = SimpleImputer(strategy="median")
    X_train = imputer.fit_transform(train_df[feature_cols]).astype(np.float32)
    X_test = imputer.transform(test_df[feature_cols]).astype(np.float32)

    y_train_bin = train_df["binary_target"].values
    y_test_bin = test_df["binary_target"].values

    y_train_multi = train_df["multiclass"].values
    y_test_multi = test_df["multiclass"].values

    # Train Binary Model
    print("\n1. Training Binary Model on Disjoint Wells...", flush=True)
    rf_bin = RandomForestClassifier(
        n_estimators=80,
        max_depth=14,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1
    )
    t0 = time.time()
    rf_bin.fit(X_train, y_train_bin)
    train_time_bin = time.time() - t0

    y_pred_bin = rf_bin.predict(X_test)
    acc_bin = accuracy_score(y_test_bin, y_pred_bin)
    prec_bin = precision_score(y_test_bin, y_pred_bin, zero_division=0)
    rec_bin = recall_score(y_test_bin, y_pred_bin, zero_division=0)
    f1_bin = f1_score(y_test_bin, y_pred_bin, zero_division=0)

    print(f"  Binary (Disjoint Wells) | Acc: {acc_bin:.4f} | Prec: {prec_bin:.4f} | Rec: {rec_bin:.4f} | F1: {f1_bin:.4f}")

    # Train Multi-Class Model
    print("\n2. Training Multi-Class Model on Disjoint Wells...", flush=True)
    rf_multi = RandomForestClassifier(
        n_estimators=80,
        max_depth=14,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1
    )
    t0 = time.time()
    rf_multi.fit(X_train, y_train_multi)
    train_time_multi = time.time() - t0

    y_pred_multi = rf_multi.predict(X_test)
    acc_multi = accuracy_score(y_test_multi, y_pred_multi)
    macro_f1_multi = f1_score(y_test_multi, y_pred_multi, average="macro", zero_division=0)
    weighted_f1_multi = f1_score(y_test_multi, y_pred_multi, average="weighted", zero_division=0)

    print(f"  Multi-Class (Disjoint Wells) | Acc: {acc_multi:.4f} | Macro F1: {macro_f1_multi:.4f} | Weighted F1: {weighted_f1_multi:.4f}")

    # Save summary report
    report_path = Path(results_dir) / "well_disjoint_evaluation.txt"
    with open(report_path, "w") as f:
        f.write("PETROBRAS 3W DATASET 2.0.0 — PHYSICAL WELL-DISJOINT GENERALIZATION REPORT\n")
        f.write("="*75 + "\n\n")
        f.write(f"Train Wells ({len(train_wells)}): {', '.join(sorted(train_wells))}\n")
        f.write(f"Test Wells  ({len(test_wells)}): {', '.join(sorted(test_wells))}\n")
        f.write(f"Physical Well Overlap: {len(overlap)} (Zero Overlap)\n\n")
        f.write("BINARY ANOMALY DETECTION (UNSEEN WELLS):\n")
        f.write(f"Accuracy : {acc_bin:.4f}\n")
        f.write(f"Precision: {prec_bin:.4f}\n")
        f.write(f"Recall   : {rec_bin:.4f}\n")
        f.write(f"F1-Score : {f1_bin:.4f}\n\n")
        f.write("MULTI-CLASS FAULT CLASSIFICATION (UNSEEN WELLS):\n")
        f.write(f"Accuracy   : {acc_multi:.4f}\n")
        f.write(f"Macro F1   : {macro_f1_multi:.4f}\n")
        f.write(f"Weighted F1: {weighted_f1_multi:.4f}\n\n")
        f.write("NOTE ON CROSS-WELL GENERALIZATION GAP:\n")
        f.write("In offshore oil wells, baseline pressure and thermal profiles vary with depth, reservoir pressure,\n")
        f.write("and completion geometry. Instance-level splitting evaluates monitoring of known field assets,\n")
        f.write("whereas physical well-disjoint splitting tests transferability to newly drilled/unmonitored assets.\n")

    print(f"\nSaved well-disjoint report to: {report_path}")


if __name__ == "__main__":
    run_well_disjoint_evaluation()
