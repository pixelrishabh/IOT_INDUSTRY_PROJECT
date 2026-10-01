"""
feature_importance.py - Compute and Visualize Top Feature Importances
Extracts feature importances from trained RandomForest models and saves:
- results/feature_importance.csv
- results/feature_importance.png
"""

import json
import os
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def compute_feature_importance(
    models_dir: str = "models",
    results_dir: str = "results",
    top_n: int = 20
):
    print("==================================================")
    print("PHASE 6: FEATURE IMPORTANCE ANALYSIS")
    print("==================================================")

    os.makedirs(results_dir, exist_ok=True)

    model_path = Path(models_dir) / "binary_fault_model.joblib"
    feature_cols_path = Path(models_dir) / "feature_columns.json"

    if not model_path.exists():
        # Fallback to multiclass model if binary is not present
        model_path = Path(models_dir) / "multiclass_fault_model.joblib"

    if not model_path.exists():
        raise FileNotFoundError("Trained model not found! Run train_binary.py or train_multiclass.py first.")

    model = joblib.load(model_path)
    with open(feature_cols_path, "r") as f:
        feature_names = json.load(f)

    if not hasattr(model, "feature_importances_"):
        raise ValueError("Model does not have feature_importances_ attribute.")

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]

    # Create DataFrame
    feat_df = pd.DataFrame({
        "Rank": range(1, len(feature_names) + 1),
        "Feature": [feature_names[i] for i in indices],
        "Importance": [importances[i] for i in indices]
    })

    # Save complete table
    csv_path = Path(results_dir) / "feature_importance.csv"
    feat_df.to_csv(csv_path, index=False)
    print(f"Saved complete feature importances to: {csv_path}")

    # Top N features
    top_df = feat_df.head(top_n).sort_values("Importance", ascending=True)

    # Plot
    plt.figure(figsize=(10, 8))
    plt.barh(top_df["Feature"], top_df["Importance"], color="#1f77b4", edgecolor="black", alpha=0.85)
    plt.title(f"Top {top_n} Most Important Sensor Features\n(Random Forest Fault Classifier)", fontsize=14, pad=15)
    plt.xlabel("Gini Feature Importance Score", fontsize=12)
    plt.ylabel("Sensor Statistical Feature (60s Window)", fontsize=12)
    plt.grid(axis="x", linestyle="--", alpha=0.6)
    plt.tight_layout()

    plot_path = Path(results_dir) / "feature_importance.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved feature importance chart to: {plot_path}")

    print("\nTop 15 Most Influential Features in Oil-Well Fault Detection:")
    for _, row in feat_df.head(15).iterrows():
        print(f"  {int(row['Rank']):2d}. {row['Feature']:25s} | Importance: {row['Importance']:.4f}")

    return feat_df


if __name__ == "__main__":
    compute_feature_importance()
