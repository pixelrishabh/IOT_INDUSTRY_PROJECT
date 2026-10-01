"""
train_binary.py - Audited Binary Fault Detection Model (Normal vs Fault)
Features:
- Balanced Random Forest Classifier
- Separate performance evaluation on Transient (Incipient) vs Established Fault observations
- Detailed confusion matrix and classification reports saved to results/
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def train_binary_model(
    data_dir: str = "data",
    models_dir: str = "models",
    results_dir: str = "results",
    random_state: int = 42
):
    print("==================================================")
    print("PHASE 2 (AUDITED): BINARY FAULT DETECTION (NORMAL vs FAULT)")
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

    X_train = train_df[feature_cols].values
    y_train = train_df["binary_target"].values

    X_test = test_df[feature_cols].values
    y_test = test_df["binary_target"].values
    is_transient_test = test_df["is_transient"].values

    print(f"Features dimension: {len(feature_cols)}")
    print(f"Train samples: {len(X_train)} (Normal: {(y_train==0).sum()}, Fault: {(y_train==1).sum()})")
    print(f"Test samples : {len(X_test)} (Normal: {(y_test==0).sum()}, Fault: {(y_test==1).sum()})")

    # Train Random Forest Classifier with balanced class weights
    print("\nTraining RandomForestClassifier(n_estimators=80, class_weight='balanced', max_depth=14, n_jobs=-1)...", flush=True)
    t0 = time.time()
    model = RandomForestClassifier(
        n_estimators=80,
        max_depth=14,
        min_samples_split=5,
        max_features="sqrt",
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    train_time = time.time() - t0
    print(f"Training completed in {train_time:.2f} seconds.")

    # Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)
    clf_report = classification_report(y_test, y_pred, target_names=["Normal", "Fault"], digits=4)

    # Separate transient vs established fault breakdown
    transient_mask = (y_test == 1) & (is_transient_test == 1)
    established_mask = (y_test == 1) & (is_transient_test == 0)

    transient_recall = (y_pred[transient_mask] == 1).mean() if transient_mask.sum() > 0 else 0.0
    established_recall = (y_pred[established_mask] == 1).mean() if established_mask.sum() > 0 else 0.0

    print("\n==================================================")
    print("BINARY MODEL EVALUATION METRICS (TEST SET):")
    print(f"Accuracy         : {acc:.4f}")
    print(f"Fault Precision  : {prec:.4f}")
    print(f"Fault Recall     : {rec:.4f}")
    print(f"Fault F1-Score   : {f1:.4f}")
    print(f"ROC-AUC          : {roc_auc:.4f}")
    print("--------------------------------------------------")
    print("TRANSIENT VS ESTABLISHED FAULT RECALL BREAKDOWN:")
    print(f"Transient Windows Recall (Classes 101-109): {transient_recall*100:.2f}% (Support: {transient_mask.sum()})")
    print(f"Established Fault Recall (Classes 1-9)    : {established_recall*100:.2f}% (Support: {established_mask.sum()})")
    print("==================================================")
    print("\nClassification Report:\n", clf_report)
    print("Confusion Matrix:\n", cm)

    # Save Model
    model_save_path = Path(models_dir) / "binary_fault_model.joblib"
    joblib.dump(model, model_save_path)
    print(f"\nSaved trained binary model to: {model_save_path}")

    # Save Classification Report
    report_file = Path(results_dir) / "binary_classification_report.txt"
    with open(report_file, "w") as f:
        f.write("PETROBRAS 3W DATASET 2.0.0 - AUDITED BINARY FAULT DETECTION REPORT\n")
        f.write("="*70 + "\n\n")
        f.write(f"Model: RandomForestClassifier (class_weight='balanced', max_depth=14)\n")
        f.write(f"Training Time: {train_time:.2f}s\n")
        f.write(f"Accuracy         : {acc:.4f}\n")
        f.write(f"Precision (Fault): {prec:.4f}\n")
        f.write(f"Recall (Fault)   : {rec:.4f}\n")
        f.write(f"F1-Score (Fault) : {f1:.4f}\n")
        f.write(f"ROC-AUC          : {roc_auc:.4f}\n\n")
        f.write(f"Transient Recall (Classes 101-109): {transient_recall:.4f} (Support: {transient_mask.sum()})\n")
        f.write(f"Established Recall (Classes 1-9)  : {established_recall:.4f} (Support: {established_mask.sum()})\n\n")
        f.write("Classification Report:\n")
        f.write(clf_report)
        f.write("\nConfusion Matrix (Normal vs Fault):\n")
        f.write(np.array2string(cm))
    print(f"Saved report to: {report_file}")

    # Plot & Save Confusion Matrix
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Normal", "Fault"], yticklabels=["Normal", "Fault"])
    plt.title("Binary Fault Classification Confusion Matrix\n(Recording-Instance Test Split)")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    cm_plot_path = Path(results_dir) / "confusion_matrix_binary.png"
    plt.savefig(cm_plot_path, dpi=300)
    plt.close()
    print(f"Saved confusion matrix plot to: {cm_plot_path}")

    return {
        "model": model,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": roc_auc,
        "transient_recall": transient_recall,
        "established_recall": established_recall,
        "train_time": train_time
    }


if __name__ == "__main__":
    train_binary_model()
