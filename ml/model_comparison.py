"""
model_comparison.py - Compare Classification Models for IoT Fault Diagnosis
Models compared:
1. Random Forest (Balanced)
2. HistGradientBoosting (Fast Gradient Tree Boosting)
3. Logistic Regression (Linear baseline with standard scaling)

Saves comparison results to results/model_comparison.csv
"""

import os
import json
import time
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)


def run_model_comparison(
    data_dir: str = "data",
    models_dir: str = "models",
    results_dir: str = "results",
    random_state: int = 42
):
    print("==================================================")
    print("PHASE 5: MODEL COMPARISON BENCHMARK")
    print("==================================================")

    os.makedirs(results_dir, exist_ok=True)

    train_path = Path(data_dir) / "train_features.parquet"
    test_path = Path(data_dir) / "test_features.parquet"
    feature_cols_path = Path(models_dir) / "feature_columns.json"

    train_df = pd.read_parquet(train_path)
    test_df = pd.read_parquet(test_path)

    with open(feature_cols_path, "r") as f:
        feature_cols = json.load(f)

    X_train = train_df[feature_cols].values
    y_train_bin = train_df["binary_target"].values
    y_train_multi = train_df["multiclass"].values

    X_test = test_df[feature_cols].values
    y_test_bin = test_df["binary_target"].values
    y_test_multi = test_df["multiclass"].values

    # Models dictionary
    models = {
        "Random Forest (Balanced)": RandomForestClassifier(
            n_estimators=80,
            max_depth=14,
            min_samples_split=5,
            max_features="sqrt",
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=12,
            class_weight="balanced",
            random_state=random_state
        ),
        "Logistic Regression (Baseline)": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=100, class_weight="balanced", random_state=random_state)
        )
    }

    results = []

    print("\n--- Evaluating Models on Binary Fault Detection ---")
    for name, model in models.items():
        print(f"Training {name}...", flush=True)
        t0 = time.time()
        model.fit(X_train, y_train_bin)
        train_time = time.time() - t0

        y_pred = model.predict(X_test)
        
        # ROC AUC if available
        try:
            if hasattr(model, "predict_proba"):
                y_proba = model.predict_proba(X_test)[:, 1]
            elif hasattr(model, "decision_function"):
                y_proba = model.decision_function(X_test)
            else:
                y_proba = y_pred
            roc_auc = roc_auc_score(y_test_bin, y_proba)
        except Exception:
            roc_auc = np.nan

        acc = accuracy_score(y_test_bin, y_pred)
        prec = precision_score(y_test_bin, y_pred, zero_division=0)
        rec = recall_score(y_test_bin, y_pred, zero_division=0)
        f1 = f1_score(y_test_bin, y_pred, zero_division=0)
        macro_f1 = f1_score(y_test_bin, y_pred, average="macro", zero_division=0)

        print(f"  {name:30s} | Acc: {acc:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f} | F1: {f1:.4f} | Macro F1: {macro_f1:.4f} | Time: {train_time:.2f}s")

        results.append({
            "Task": "Binary (Normal vs Fault)",
            "Model": name,
            "Accuracy": round(acc, 4),
            "Precision": round(prec, 4),
            "Recall": round(rec, 4),
            "F1": round(f1, 4),
            "Macro F1": round(macro_f1, 4),
            "ROC-AUC": round(roc_auc, 4) if not np.isnan(roc_auc) else "N/A",
            "Training Time (s)": round(train_time, 2)
        })

    # Multi-Class comparison
    print("\n--- Evaluating Models on Multi-Class Fault Classification (Events 0-9) ---")
    multi_models = {
        "Random Forest (Balanced)": RandomForestClassifier(
            n_estimators=80,
            max_depth=14,
            min_samples_split=5,
            max_features="sqrt",
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=12,
            class_weight="balanced",
            random_state=random_state
        ),
        "Logistic Regression (Baseline)": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=100, class_weight="balanced", random_state=random_state)
        )
    }

    for name, model in multi_models.items():
        print(f"Training Multi-class {name}...", flush=True)
        t0 = time.time()
        model.fit(X_train, y_train_multi)
        train_time = time.time() - t0

        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test_multi, y_pred)
        prec = precision_score(y_test_multi, y_pred, average="macro", zero_division=0)
        rec = recall_score(y_test_multi, y_pred, average="macro", zero_division=0)
        f1 = f1_score(y_test_multi, y_pred, average="weighted", zero_division=0)
        macro_f1 = f1_score(y_test_multi, y_pred, average="macro", zero_division=0)

        print(f"  {name:30s} | Acc: {acc:.4f} | Macro Prec: {prec:.4f} | Macro Rec: {rec:.4f} | Macro F1: {macro_f1:.4f} | Time: {train_time:.2f}s")

        results.append({
            "Task": "Multi-Class (Events 0-9)",
            "Model": name,
            "Accuracy": round(acc, 4),
            "Precision": round(prec, 4),
            "Recall": round(rec, 4),
            "F1": round(f1, 4),
            "Macro F1": round(macro_f1, 4),
            "ROC-AUC": "N/A",
            "Training Time (s)": round(train_time, 2)
        })

    results_df = pd.DataFrame(results)
    out_csv = Path(results_dir) / "model_comparison.csv"
    results_df.to_csv(out_csv, index=False)
    print(f"\nSaved comprehensive model comparison table to: {out_csv}")
    print("\nModel Comparison Table:")
    print(results_df.to_string(index=False))

    return results_df


if __name__ == "__main__":
    run_model_comparison()
