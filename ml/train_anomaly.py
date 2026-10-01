"""
train_anomaly.py - Train and Evaluate Unsupervised Anomaly Detection (IsolationForest)
Trains strictly on Class 0 (Normal) operation windows to learn the normal operating envelope,
and evaluates against known fault events in the test partition.
"""

import os
import json
import time
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def train_anomaly_model(
    data_dir: str = "data",
    models_dir: str = "models",
    results_dir: str = "results",
    random_state: int = 42
):
    print("==================================================")
    print("PHASE 4: UNSUPERVISED ANOMALY DETECTION (ISOLATION FOREST)")
    print("==================================================")

    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    train_path = Path(data_dir) / "train_features.parquet"
    test_path = Path(data_dir) / "test_features.parquet"
    feature_cols_path = Path(models_dir) / "feature_columns.json"

    train_df = pd.read_parquet(train_path)
    test_df = pd.read_parquet(test_path)

    with open(feature_cols_path, "r") as f:
        feature_cols = json.load(f)

    # Train IsolationForest ONLY on normal (class 0) training samples
    normal_train = train_df[train_df["binary_target"] == 0]
    X_train_normal = normal_train[feature_cols].values

    X_test = test_df[feature_cols].values
    y_test = test_df["binary_target"].values # 0 = Normal, 1 = Fault

    print(f"Features dimension: {len(feature_cols)}")
    print(f"Normal training windows: {len(X_train_normal)}")
    print(f"Test windows: {len(X_test)} (Normal: {(y_test==0).sum()}, Fault: {(y_test==1).sum()})")

    # Fit IsolationForest
    # Note: contamination set to expected anomaly rate (or 'auto')
    print("\nTraining IsolationForest(n_estimators=100, contamination=0.15)...", flush=True)
    t0 = time.time()
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.15,
        max_samples="auto",
        random_state=random_state,
        n_jobs=-1
    )
    iso_forest.fit(X_train_normal)
    train_time = time.time() - t0
    print(f"Training completed in {train_time:.2f} seconds.")

    # IsolationForest outputs: 1 for normal, -1 for anomaly.
    # Map to: 0 for normal, 1 for anomaly (fault)
    raw_preds = iso_forest.predict(X_test)
    y_pred = np.where(raw_preds == -1, 1, 0)
    anomaly_scores = -iso_forest.score_samples(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    clf_report = classification_report(y_test, y_pred, target_names=["Normal", "Anomaly/Fault"], digits=4)

    print("\n==================================================")
    print("ISOLATION FOREST EVALUATION (TEST SET):")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")
    print(f"F1-Score : {f1:.4f}")
    print("==================================================")
    print("\nClassification Report:\n", clf_report)
    print("Confusion Matrix:\n", cm)

    # Save Model
    model_save_path = Path(models_dir) / "isolation_forest_model.joblib"
    joblib.dump(iso_forest, model_save_path)
    print(f"\nSaved Isolation Forest model to: {model_save_path}")

    # Plot Confusion Matrix
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Greens", xticklabels=["Normal", "Anomaly"], yticklabels=["Normal", "Fault"])
    plt.title("Isolation Forest Anomaly Detection Confusion Matrix\n(Unsupervised Baseline)")
    plt.xlabel("Predicted State")
    plt.ylabel("True State")
    plt.tight_layout()
    cm_plot_path = Path(results_dir) / "confusion_matrix_isolation_forest.png"
    plt.savefig(cm_plot_path, dpi=300)
    plt.close()
    print(f"Saved confusion matrix plot to: {cm_plot_path}")

    return {
        "model": iso_forest,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "train_time": train_time
    }


if __name__ == "__main__":
    train_anomaly_model()
