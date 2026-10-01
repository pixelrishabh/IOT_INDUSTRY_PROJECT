# Petrobras 3W Dataset 2.0.0 — Machine Learning Audit & Experimental Results

## 1. Executive Summary
This document provides the comprehensive, audited experimental evaluation for the **Knowledge-Driven IoT Fault Diagnosis Assistant for Offshore Oil & Gas Wells**.

All machine learning models were trained and evaluated exclusively on the **1,119 real well recordings** (`WELL-*.parquet`) from the benchmark **Petrobras 3W Dataset (Version 2.0.0)** released by Petróleo Brasileiro S.A. (Petrobras). No synthetic simulator data was used for model training or evaluation.

---

## 2. Dataset Overview & Audited Characteristics

| Dataset Parameter | Value / Specification |
| :--- | :--- |
| **Dataset Source** | Petrobras 3W Dataset (Version 2.0.0, July 2024 Release) |
| **Industry Domain** | Offshore Deepwater Oil & Gas Production Wells |
| **Total Real Parquet Files** | 1,119 Real Well Recordings (Folders 0 to 9) |
| **Physical Well Coverage** | 40 Distinct Physical Offshore Wells (`WELL-00001` through `WELL-00042`) |
| **Raw Sampling Frequency** | 1 Hz (1-second continuous telemetry) |
| **Window Resampling Interval** | 60-second non-overlapping statistical time windows |
| **Total Annotated Windows** | **481,883 window observations** (Unannotated buffer periods excluded) |
| **Engineered Features** | 91 statistical & dynamic features across 13 sensor tags |

---

## 3. Audited Preprocessing & Label Aggregation Policies

### 3.1 Strictly Causal Missing-Value Imputation
- **Elimination of Lookahead Bias:** Backward-fill (`bfill`) was strictly removed from the preprocessing pipeline. In continuous real-time IoT monitoring, looking into future sensor states is physically impossible.
- **Causal Forward-Fill:** Applied `ffill(limit=60)` within each recording file to carry forward valid readings across short sensor dropouts (< 60 seconds).
- **Training-Fitted Imputation:** A `SimpleImputer(strategy='median')` was fitted **exclusively on the training partition** and persisted to `models/feature_imputer.joblib` for online inference.

### 3.2 Principled Class Label Aggregation
- **Unannotated Windows (NA Handling):** In 3W Dataset 2.0.0, certain initial recording periods contain `<NA>` in the `class` column (expert annotation buffer). All windows consisting entirely of unannotated `<NA>` observations are **explicitly dropped** rather than silently filled.
- **Mixed-Label Transition Windows:** For 60-second windows containing operational transitions (e.g. Normal $\rightarrow$ Transient), the window label is determined by the most critical active fault/transient state present: $\text{label} = \max(\text{valid\_annotations})$.

### 3.3 Transient vs Established Fault Dynamics
In accordance with `dataset.ini` (`TRANSIENT_OFFSET = 100`):
- **Classes 101–109:** Transient / incipient phase where fault symptoms begin developing (76.9% of fault observations).
- **Classes 1–9:** Established steady-state fault phase (23.1% of fault observations).

---

## 4. Train / Test Split Terminology & Well Overlap Audit

### 4.1 Primary Split: Stratified Recording-Instance Level
- **Mechanism:** Split performed on `instance_file` stratified by event folder (`event_folder`).
- **Data Leakage Prevention:** Every 60-second window belonging to a given file recording is strictly isolated to either Train or Test (zero temporal overlap).
- **Partition Sizes:**
  - **Train Instances:** 895 recordings $\rightarrow$ **365,867 windows (75.9%)**
  - **Test Instances:** 224 recordings $\rightarrow$ **116,016 windows (24.1%)**
- **Physical Well Overlap:** 24 physical wells appear with different temporal recording files in both train and test partitions. This evaluates the model's ability to detect faults across new operating periods of monitored assets.

### 4.2 Secondary Evaluation: Physical Well-Disjoint Split
To evaluate zero-shot generalization to an entirely unmonitored physical well, a separate `GroupShuffleSplit` on `well_id` was evaluated (Train: 32 physical wells, Test: 8 physical wells, 0 well overlap).

---

## 5. Audited Model Evaluation Results

### 5.1 Binary Fault Detection (Normal vs Fault)
- **Model:** `RandomForestClassifier(n_estimators=80, max_depth=14, class_weight='balanced')`

| Metric | Overall Test Score | Transient Windows (101-109) | Established Faults (1-9) |
| :--- | :---: | :---: | :---: |
| **Accuracy** | **74.17%** | — | — |
| **Fault Precision** | **90.72%** | — | — |
| **Fault Recall** | **61.23%** | **54.81%** (Support: 54,934) | **91.57%** (Support: 11,625) |
| **Fault F1-Score** | **73.12%** | — | — |
| **ROC-AUC** | **0.9210** | — | — |

**Binary Classification Report (Held-Out Test Set):**
```text
               precision    recall  f1-score   support

      Normal     0.6370    0.9157    0.7514     49457
       Fault     0.9072    0.6123    0.7312     66559

    accuracy                         0.7417    116016
   macro avg     0.7721    0.7640    0.7413    116016
weighted avg     0.7921    0.7417    0.7398    116016
```

---

### 5.2 Multi-Class Fault Classification (Events 0–9)
- **Model:** `RandomForestClassifier(n_estimators=80, max_depth=14, class_weight='balanced')`

| Metric | Overall Test Score | Transient Phase (101-109) | Established Phase (1-9) |
| :--- | :---: | :---: | :---: |
| **Accuracy** | **72.76%** | **50.80%** (Support: 54,934) | **90.56%** (Support: 11,625) |
| **Macro Precision** | **58.27%** | — | — |
| **Macro Recall** | **59.05%** | — | — |
| **Macro F1-Score** | **56.57%** | — | — |
| **Weighted F1-Score** | **71.08%** | — | — |

**Per-Class Classification Report (Held-Out Test Set):**

| Class | Event Description | Precision | Recall | F1-Score | Test Support |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **0** | Normal Operation | 0.6336 | 0.9298 | 0.7536 | 49,457 |
| **1** | Abrupt Increase of BSW | 0.0000 | 0.0000 | 0.0000 | 242 |
| **2** | Spurious Closure of DHSV | 0.9982 | 0.9859 | **0.9920** | 566 |
| **3** | Severe Slugging | 0.5117 | 0.9435 | **0.6635** | 1,788 |
| **4** | Flow Instability | 0.9010 | 0.9781 | **0.9380** | 8,359 |
| **5** | Rapid Productivity Loss | 0.9176 | 0.9914 | **0.9530** | 696 |
| **6** | Quick Restriction in PCK | 0.0000 | 0.0000 | 0.0000 | 15 |
| **7** | Scaling in PCK | 0.8662 | 0.4166 | **0.5626** | 33,444 |
| **8** | Hydrate in Production Line | 0.9986 | 0.6598 | **0.7946** | 20,290 |
| **9** | Hydrate in Service Line | 0.0000 | 0.0000 | 0.0000 | 1,159 |

---

### 5.3 Model Comparison Benchmark (Exact Audited Metrics)

All models evaluated under identical causal preprocessing and recording-instance partitions:

| Task | Model Architecture | Accuracy | Precision | Recall | F1 | Macro F1 | ROC-AUC | Training Time |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Binary** | **Random Forest (Balanced)** | **0.7417** | **0.9072** | **0.6123** | **0.7312** | **0.7413** | **0.9210** | 8.24s |
| **Binary** | HistGradientBoosting | 0.7378 | 0.9473 | 0.5749 | 0.7155 | 0.7361 | 0.9301 | 6.46s |
| **Binary** | Logistic Regression (Scaled) | 0.8442 | 0.8840 | 0.8384 | 0.8606 | 0.8420 | 0.8766 | 4.76s |
| **Multi-Class** | **Random Forest (Balanced)** | **0.7276** | **0.5827** | **0.5905** | **0.7108** | **0.5657** | N/A | 6.88s |
| **Multi-Class** | HistGradientBoosting | 0.7458 | 0.6544 | 0.6201 | 0.7253 | 0.6172 | N/A | 20.26s |
| **Multi-Class** | Logistic Regression (Baseline) | 0.6713 | 0.5097 | 0.6022 | 0.6883 | 0.5057 | N/A | 20.03s |

---

### 5.4 Physical Well-Disjoint Generalization Gap

| Evaluation Protocol | Split Unit | Well Overlap | Binary F1 | Multi-Class Weighted F1 |
| :--- | :--- | :---: | :---: | :---: |
| **Recording-Instance Split** | Recording File | Yes (Different times) | **73.12%** | **71.08%** |
| **Physical Well-Disjoint Split** | Physical Well ID | **Zero (0 Wells)** | **51.18%** | **24.30%** |

**Engineering Rationale:**
In deepwater petroleum systems, geothermal gradients, completion depth (3,000m vs 5,000m), reservoir drive pressure, and choke sizing vary significantly across physical wells. While recording-level models effectively monitor known assets, cross-well deployment requires well-specific baseline normalization or asset fine-tuning.

---

## 6. Top Sensor Feature Importances

Top 10 features identified by Gini Impurity reduction:
1. `T-TPT_min` (Transducer Temperature Minimum): 0.0690
2. `T-TPT_mean` (Transducer Temperature Mean): 0.0687
3. `T-TPT_median` (Transducer Temperature Median): 0.0520
4. `T-TPT_max` (Transducer Temperature Maximum): 0.0495
5. `T-JUS-CKP_median` (Choke Downstream Temperature Median): 0.0446
6. `T-JUS-CKP_max` (Choke Downstream Temperature Maximum): 0.0416
7. `T-JUS-CKP_mean` (Choke Downstream Temperature Mean): 0.0350
8. `P-ANULAR_mean` (Annulus Pressure Mean): 0.0282
9. `P-TPT_range` (Transducer Pressure Amplitude Range): 0.0279
10. `P-TPT_max` (Transducer Pressure Maximum): 0.0255

---

## 7. Reproducible Execution Commands

All commands run with Windows PowerShell and `.venv`:

```powershell
# 1. Audited Preprocessing & Feature Extraction
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe ml/prepare_dataset.py

# 2. Binary Fault Model Training & Evaluation
.\.venv\Scripts\python.exe ml/train_binary.py

# 3. Multi-Class Fault Classification (Events 0-9)
.\.venv\Scripts\python.exe ml/train_multiclass.py

# 4. Model Comparison Benchmark
.\.venv\Scripts\python.exe ml/model_comparison.py

# 5. Physical Well-Disjoint Generalization Evaluation
.\.venv\Scripts\python.exe ml/evaluate_well_disjoint.py

# 6. Stream Genuine Real-Well Telemetry via MQTT
.\.venv\Scripts\python.exe simulator/replay_petrobras.py --event 3 --max-rows 60

# 7. Run Comprehensive Automated Pytest Suite
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline.py -v
```
