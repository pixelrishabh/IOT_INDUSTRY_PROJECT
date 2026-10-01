"""
train_multiclass.py - Audited Multi-Class Fault Classification Model (Events 0-9)
Features:
- Balanced Random Forest Classifier on classes 0-9
- Breakdown of classification accuracy on Transient vs Established Fault windows
- Detailed per-class classification report & confusion matrix
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
)

CLASS_NAMES = [
    "Normal",
    "Abrupt BSW Inc",
    "Spurious DHSV",
    "Severe Slugging",
    "Flow Instability",
    "Rapid Prod Loss",
    "Quick PCK Restr",
    "Scaling in PCK",
    "Hydrate Prod Line",
    "Hydrate Serv Line"
]


def train_multiclass_model(
    data_dir: str = "data",
    models_dir: str = "models",
    results_dir: str = "results",
    random_state: int = 42
):
    print("==================================================")
    print("PHASE 3 (AUDITED): MULTI-CLASS FAULT CLASSIFIER (EVENTS 0-9)")
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
    y_train = train_df["multiclass"].values

    X_test = test_df[feature_cols].values
    y_test = test_df["multiclass"].values
    is_transient_test = test_df["is_transient"].values

    present_classes = sorted(np.unique(np.concatenate([y_train, y_test])))
    target_names = [CLASS_NAMES[c] if c < len(CLASS_NAMES) else f"Class_{c}" for c in present_classes]

    print(f"Features dimension: {len(feature_cols)}")
    print(f"Unique classes present: {present_classes}")
    print(f"Train samples: {len(X_train)}")
    print(f"Test samples : {len(X_test)}")

    # Train Random Forest with balanced class weights
    print("\nTraining Multi-Class RandomForestClassifier(n_estimators=80, class_weight='balanced', max_depth=14, n_jobs=-1)...", flush=True)
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

    acc = accuracy_score(y_test, y_pred)
    macro_prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
    macro_rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=present_classes)
    clf_report = classification_report(
        y_test, y_pred, labels=present_classes, target_names=target_names, digits=4, zero_division=0
    )

    # Transient vs Established fault multi-class accuracy
    fault_mask = (y_test > 0)
    transient_mask = fault_mask & (is_transient_test == 1)
    established_mask = fault_mask & (is_transient_test == 0)

    transient_correct = (y_pred[transient_mask] == y_test[transient_mask]).mean() if transient_mask.sum() > 0 else 0.0
    established_correct = (y_pred[established_mask] == y_test[established_mask]).mean() if established_mask.sum() > 0 else 0.0

    print("\n==================================================")
    print("MULTI-CLASS FAULT EVALUATION METRICS (TEST SET):")
    print(f"Accuracy   : {acc:.4f}")
    print(f"Macro Prec : {macro_prec:.4f}")
    print(f"Macro Rec  : {macro_rec:.4f}")
    print(f"Macro F1   : {macro_f1:.4f} (Crucial under severe class imbalance)")
    print(f"Weighted F1: {weighted_f1:.4f}")
    print("--------------------------------------------------")
    print("TRANSIENT VS ESTABLISHED FAULT EVENT ACCURACY:")
    print(f"Transient Event Accuracy  : {transient_correct*100:.2f}% (Support: {transient_mask.sum()})")
    print(f"Established Event Accuracy: {established_correct*100:.2f}% (Support: {established_mask.sum()})")
    print("==================================================")
    print("\nPer-Class Classification Report:\n", clf_report)

    # Save Model
    model_save_path = Path(models_dir) / "multiclass_fault_model.joblib"
    joblib.dump(model, model_save_path)
    print(f"\nSaved trained multi-class model to: {model_save_path}")

    # Save Classification Report
    report_file = Path(results_dir) / "multiclass_classification_report.txt"
    with open(report_file, "w") as f:
        f.write("PETROBRAS 3W DATASET 2.0.0 - AUDITED MULTI-CLASS FAULT CLASSIFICATION REPORT\n")
        f.write("="*75 + "\n\n")
        f.write(f"Model: RandomForestClassifier (class_weight='balanced', max_depth=14)\n")
        f.write(f"Training Time: {train_time:.2f}s\n")
        f.write(f"Accuracy   : {acc:.4f}\n")
        f.write(f"Macro Prec : {macro_prec:.4f}\n")
        f.write(f"Macro Rec  : {macro_rec:.4f}\n")
        f.write(f"Macro F1   : {macro_f1:.4f}\n")
        f.write(f"Weighted F1: {weighted_f1:.4f}\n\n")
        f.write(f"Transient Event Accuracy  : {transient_correct:.4f} (Support: {transient_mask.sum()})\n")
        f.write(f"Established Event Accuracy: {established_correct:.4f} (Support: {established_mask.sum()})\n\n")
        f.write("Per-Class Classification Report:\n")
        f.write(clf_report)
        f.write("\nConfusion Matrix (Events 0-9):\n")
        f.write(np.array2string(cm))
    print(f"Saved report to: {report_file}")

    # Plot Confusion Matrix
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Purples",
        xticklabels=target_names,
        yticklabels=target_names
    )
    plt.title("Multi-Class Fault Confusion Matrix\n(Recording-Instance Test Split)")
    plt.xlabel("Predicted Event")
    plt.ylabel("True Event")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    cm_plot_path = Path(results_dir) / "confusion_matrix_multiclass.png"
    plt.savefig(cm_plot_path, dpi=300)
    plt.close()
    print(f"Saved multi-class confusion matrix plot to: {cm_plot_path}")

    return {
        "model": model,
        "accuracy": acc,
        "macro_prec": macro_prec,
        "macro_rec": macro_rec,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "transient_accuracy": transient_correct,
        "established_accuracy": established_correct,
        "train_time": train_time
    }


if __name__ == "__main__":
    train_multiclass_model()
