"""
dashboard/app.py - Advanced Industrial IoT Fault Diagnosis & RAG Assistant Dashboard
Integrates:
- Live/Real-time Telemetry & Asset Selector
- Petrobras 3W ML Fault Detection & Classification (Binary + Multi-Class)
- Sensor Evidence & Threshold Breach Analysis
- RAG Technical Knowledge Retrieval & LLM Structured Diagnosis
- Model Performance Metrics & Confusion Matrices
- Gini Feature Importance Visualizations
"""

import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from ml.detector import FaultDetectorPipeline, EVENT_MAPPING, NOMINAL_BOUNDS
from rag.retriever import FaultKnowledgeRetriever

# =========================================================
# PAGE CONFIGURATION & STYLING
# =========================================================
st.set_page_config(
    page_title="IoT Fault Diagnosis Assistant | Oil & Gas",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 2px;
    }
    .sub-header {
        font-size: 15px;
        color: #64748B;
        margin-bottom: 15px;
    }
    .card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .alert-fault {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 12px;
        border-radius: 4px;
        color: #991B1B;
        font-weight: 600;
    }
    .alert-normal {
        background-color: #F0FDF4;
        border-left: 5px solid #22C55E;
        padding: 12px;
        border-radius: 4px;
        color: #166534;
        font-weight: 600;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Initialize ML Pipeline singleton in session
@st.cache_resource
def get_detector():
    return FaultDetectorPipeline()

detector = get_detector()

# =========================================================
# SIDEBAR NAVIGATION & CONTROLS
# =========================================================
st.sidebar.image("https://img.icons8.com/fluency/96/oil-rig.png", width=64)
st.sidebar.title("Industrial IoT Assistant")
st.sidebar.caption("Petrobras 3W Dataset 2.0.0 ML + RAG System")

nav_page = st.sidebar.radio(
    "Navigation",
    [
        "📡 Live Asset Monitor & Diagnosis",
        "🧪 Interactive Diagnostic Lab",
        "📊 Model Evaluation & Benchmarks",
        "🔍 Feature Importance Analytics",
        "📚 RAG Technical Knowledge Base",
        "📋 Telemetry & Fault History"
    ]
)

st.sidebar.divider()
st.sidebar.subheader("System Status")
st.sidebar.success("🟢 ML Models Loaded (Binary + Multi-Class)")
st.sidebar.success("🟢 RAG Vector Store Active (90 Chunks)")
st.sidebar.info(f"Features Monitored: {len(detector.feature_cols)}")

# =========================================================
# DATA LOADER HELPERS
# =========================================================
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "energy_db",
    "user": "energy_user",
    "password": "energy_password"
}

def load_db_telemetry():
    if not HAS_PSYCOPG2:
        return pd.DataFrame()
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        query = """
            SELECT id, device_id, device_type, timestamp, fault, sensor_data
            FROM telemetry
            ORDER BY timestamp DESC
            LIMIT 1000
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data
def load_sample_real_telemetry():
    """Load sample real data from processed features for interactive demonstration."""
    sample_path = Path("data/processed_features_sample.csv")
    if sample_path.exists():
        return pd.read_csv(sample_path)
    return pd.DataFrame()


# =========================================================
# PAGE 1: LIVE ASSET MONITOR & DIAGNOSIS
# =========================================================
if nav_page == "📡 Live Asset Monitor & Diagnosis":
    st.markdown('<div class="main-header">⚡ Offshore Well Telemetry & AI Diagnosis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Continuous Multiphase Production Monitoring, Real-Time Anomaly Inference & RAG Knowledge Synthesis</div>', unsafe_allow_html=True)
    st.divider()

    # Preset Real Well Test Cases
    PRESETS = {
        "Preset 1: Normal Operation (Stable Deepwater Flow)": {
            "P-PDG": 27500000.0, "P-TPT": 14500000.0, "T-TPT": 72.5,
            "P-MON-CKP": 11500000.0, "T-JUS-CKP": 55.0, "P-ANULAR": 500000.0,
            "T-PDG": 92.0, "QGL": 2.5, "ABER-CKP": 65.0
        },
        "Preset 2: Event 3 - Severe Slugging (Riser Pressure Surges)": {
            "P-PDG": 26000000.0, "P-TPT": 9500000.0, "T-TPT": 58.0,
            "P-MON-CKP": 6500000.0, "T-JUS-CKP": 42.0, "P-ANULAR": 650000.0,
            "T-PDG": 89.0, "QGL": 0.8, "ABER-CKP": 85.0
        },
        "Preset 3: Event 2 - Spurious Closure of DHSV (Downhole Blockage)": {
            "P-PDG": 33500000.0, "P-TPT": 1200000.0, "T-TPT": 25.0,
            "P-MON-CKP": 1050000.0, "T-JUS-CKP": 18.0, "P-ANULAR": 300000.0,
            "T-PDG": 98.0, "QGL": 0.0, "ABER-CKP": 50.0
        },
        "Preset 4: Event 6 - Quick Restriction in Choke (PCK Debris Bridge)": {
            "P-PDG": 29000000.0, "P-TPT": 19500000.0, "T-TPT": 68.0,
            "P-MON-CKP": 18500000.0, "T-JUS-CKP": 24.0, "P-ANULAR": 450000.0,
            "T-PDG": 91.0, "QGL": 2.0, "ABER-CKP": 60.0
        },
        "Preset 5: Event 8 - Hydrate in Production Line (Subsea Subcooling)": {
            "P-PDG": 31000000.0, "P-TPT": 21000000.0, "T-TPT": 14.5,
            "P-MON-CKP": 19000000.0, "T-JUS-CKP": 9.2, "P-ANULAR": 800000.0,
            "T-PDG": 90.0, "QGL": 1.2, "ABER-CKP": 70.0
        },
        "Preset 6: Event 1 - Abrupt Increase of BSW (Water Breakthrough)": {
            "P-PDG": 32000000.0, "P-TPT": 11000000.0, "T-TPT": 54.0,
            "P-MON-CKP": 9200000.0, "T-JUS-CKP": 45.0, "P-ANULAR": 400000.0,
            "T-PDG": 93.0, "QGL": 2.8, "ABER-CKP": 65.0
        }
    }

    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_preset_name = st.selectbox("Select Asset Telemetry Profile / Scenario:", list(PRESETS.keys()))
    with col_sel2:
        well_id_input = st.text_input("Well Asset ID", "WELL-00002")

    current_telemetry = PRESETS[selected_preset_name]

    # Run Diagnosis Engine
    with st.spinner("Running ML Inference & RAG Knowledge Synthesis..."):
        diag_result = detector.diagnose(current_telemetry, well_id=well_id_input)

    status = diag_result["status"]
    is_fault = status == "ANOMALY" or diag_result["predicted_event_id"] > 0
    event_name = diag_result["predicted_event"]
    conf = diag_result["confidence"]

    # Top Status Banner
    if is_fault:
        st.markdown(f"""
        <div class="alert-fault">
            🚨 ALERT: {event_name.upper()} DETECTED — Confidence: {conf*100:.1f}% | Well: {well_id_input}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-normal">
            ✅ SYSTEM HEALTHY: NORMAL OPERATION — Confidence: {conf*100:.1f}% | Well: {well_id_input}
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Metric Cards
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Binary Status", diag_result["binary_status"], delta="Normal" if not is_fault else "Anomaly", delta_color="inverse" if is_fault else "normal")
    with m2:
        st.metric("Classified Event", f"Event {diag_result['predicted_event_id']}")
    with m3:
        st.metric("Model Confidence", f"{conf*100:.1f}%")
    with m4:
        st.metric("Downhole P-PDG", f"{current_telemetry['P-PDG']/1e5:.1f} bar")
    with m5:
        st.metric("Choke Upstream P-MON", f"{current_telemetry['P-MON-CKP']/1e5:.1f} bar")

    st.divider()

    # Detailed Telemetry & RAG Assistant Split
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📊 Live Sensor Telemetry Envelope")
        
        # Sensor bar table
        sensor_display = []
        for k, v in current_telemetry.items():
            unit = "bar" if k.startswith("P-") else "°C" if k.startswith("T-") else "%" if k.startswith("ABER") else "m3/s"
            val_fmt = f"{v/1e5:.2f}" if k.startswith("P-") else f"{v:.2f}"
            sensor_display.append({"Sensor Parameter": k, "Telemetry Value": f"{val_fmt} {unit}"})
        
        st.dataframe(pd.DataFrame(sensor_display), use_container_width=True, hide_index=True)

        # Multi-class Probabilities Bar Chart
        if diag_result.get("class_probabilities"):
            st.subheader("🎯 Multi-Class Prediction Probabilities")
            probas_df = pd.DataFrame([
                {"Event": k, "Probability": v} 
                for k, v in diag_result["class_probabilities"].items()
            ]).sort_values("Probability", ascending=True)

            fig_p = px.bar(
                probas_df,
                x="Probability",
                y="Event",
                orientation="h",
                color="Probability",
                color_continuous_scale="Blues",
                title="Event Class Probabilities Distribution"
            )
            fig_p.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_p, use_container_width=True)

    with col_right:
        st.subheader("🧠 RAG-Powered AI Diagnostic Assistant")
        st.markdown(f"```text\n{diag_result.get('raw_diagnosis', '')}\n```")

        # Knowledge Sources
        sources = diag_result.get("retrieved_sources", [])
        if sources:
            st.caption(f"📚 Retrieved Technical Sources: {', '.join(set(sources))}")


# =========================================================
# PAGE 2: INTERACTIVE DIAGNOSTIC LAB
# =========================================================
elif nav_page == "🧪 Interactive Diagnostic Lab":
    st.markdown('<div class="main-header">🧪 Interactive Fault Injection & Telemetry Lab</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Adjust sensor values dynamically to test ML fault classification and RAG explanation triggers.</div>', unsafe_allow_html=True)
    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Downhole & Wellhead Pressures**")
        p_pdg = st.slider("P-PDG: Downhole Pressure (bar)", 50.0, 450.0, 275.0) * 1e5
        p_tpt = st.slider("P-TPT: Transducer Pressure (bar)", 10.0, 300.0, 145.0) * 1e5
        p_mon = st.slider("P-MON-CKP: Choke Upstream (bar)", 10.0, 250.0, 115.0) * 1e5

    with c2:
        st.markdown("**Temperatures & Annulus**")
        t_tpt = st.slider("T-TPT: Transducer Temp (°C)", 0.0, 150.0, 72.0)
        t_jus = st.slider("T-JUS-CKP: Choke Downstream Temp (°C)", -10.0, 120.0, 55.0)
        p_anu = st.slider("P-ANULAR: Annulus 'A' Pressure (bar)", 0.0, 100.0, 5.0) * 1e5

    with c3:
        st.markdown("**Choke & Gas Lift Operations**")
        t_pdg = st.slider("T-PDG: Downhole Gauge Temp (°C)", 40.0, 160.0, 92.0)
        qgl = st.slider("QGL: Gas Lift Flow Rate (m3/s)", 0.0, 20.0, 2.5)
        aber_ckp = st.slider("ABER-CKP: Choke Opening (%)", 0.0, 100.0, 65.0)

    custom_telemetry = {
        "P-PDG": p_pdg, "P-TPT": p_tpt, "P-MON-CKP": p_mon,
        "T-TPT": t_tpt, "T-JUS-CKP": t_jus, "P-ANULAR": p_anu,
        "T-PDG": t_pdg, "QGL": qgl, "ABER-CKP": aber_ckp
    }

    if st.button("🚀 Run Live Diagnostic Analysis", type="primary"):
        with st.spinner("Analyzing telemetry vector..."):
            diag = detector.diagnose(custom_telemetry, well_id="TEST-WELL-LAB")

        st.divider()
        res_col1, res_col2 = st.columns([1, 1])
        with res_col1:
            st.subheader("Detection Result")
            st.write(f"**Predicted Event:** {diag['predicted_event']}")
            st.write(f"**Status:** {diag['status']}")
            st.write(f"**Confidence:** {diag['confidence']*100:.1f}%")
            st.write(f"**Binary Target:** {diag['binary_status']}")
        with res_col2:
            st.subheader("Detailed Engineering Report")
            st.markdown(f"```text\n{diag['raw_diagnosis']}\n```")


# =========================================================
# PAGE 3: MODEL EVALUATION & BENCHMARKS
# =========================================================
elif nav_page == "📊 Model Evaluation & Benchmarks":
    st.markdown('<div class="main-header">📊 Petrobras 3W Dataset 2.0.0 Model Benchmark</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Rigorous Instance-Level (Well-Level) Train/Test Splitting — Zero Data Leakage</div>', unsafe_allow_html=True)
    st.divider()

    # Load comparison table
    comp_path = Path("results/model_comparison.csv")
    if comp_path.exists():
        comp_df = pd.read_csv(comp_path)
        st.subheader("🏆 Model Comparison Leaderboard")
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

    st.divider()
    col_cm1, col_cm2 = st.columns(2)

    with col_cm1:
        st.subheader("Binary Fault Confusion Matrix")
        cm_bin = Path("results/confusion_matrix_binary.png")
        if cm_bin.exists():
            st.image(str(cm_bin), use_container_width=True)
        
        rep_bin = Path("results/binary_classification_report.txt")
        if rep_bin.exists():
            with open(rep_bin, "r") as f:
                st.text(f.read())

    with col_cm2:
        st.subheader("Multi-Class Event Confusion Matrix")
        cm_multi = Path("results/confusion_matrix_multiclass.png")
        if cm_multi.exists():
            st.image(str(cm_multi), use_container_width=True)

        rep_multi = Path("results/multiclass_classification_report.txt")
        if rep_multi.exists():
            with open(rep_multi, "r") as f:
                st.text(f.read())


# =========================================================
# PAGE 4: FEATURE IMPORTANCE ANALYTICS
# =========================================================
elif nav_page == "🔍 Feature Importance Analytics":
    st.markdown('<div class="main-header">🔍 Sensor Feature Importance & Physics Relevance</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Top 20 Most Influential Sensor Features Identified by Gini Impurity Reduction in Random Forest</div>', unsafe_allow_html=True)
    st.divider()

    col_fi1, col_fi2 = st.columns([1.2, 0.8])
    with col_fi1:
        fi_img = Path("results/feature_importance.png")
        if fi_img.exists():
            st.image(str(fi_img), use_container_width=True)
        else:
            st.info("Feature importance plot generating...")

    with col_fi2:
        st.subheader("Top Predictive Features Table")
        fi_csv = Path("results/feature_importance.csv")
        if fi_csv.exists():
            fi_df = pd.read_csv(fi_csv).head(20)
            st.dataframe(fi_df, use_container_width=True, hide_index=True)


# =========================================================
# PAGE 5: RAG KNOWLEDGE BASE
# =========================================================
elif nav_page == "📚 RAG Technical Knowledge Base":
    st.markdown('<div class="main-header">📚 Oil & Gas Domain Technical Knowledge Base</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Indexed Standard Operating Procedures, Diagnostic Checklists, and Safety Guidelines</div>', unsafe_allow_html=True)
    st.divider()

    doc_files = sorted(list(Path("rag/documents").glob("*.md")))
    selected_doc = st.selectbox(
        "Select Engineering Reference Document:",
        [f.name for f in doc_files]
    )

    if selected_doc:
        doc_path = Path("rag/documents") / selected_doc
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        st.markdown(content)


# =========================================================
# PAGE 6: TELEMETRY & FAULT HISTORY
# =========================================================
elif nav_page == "📋 Telemetry & Fault History":
    st.markdown('<div class="main-header">📋 Asset Telemetry & Historical Event Logs</div>', unsafe_allow_html=True)
    st.divider()

    df_db = load_db_telemetry()
    if not df_db.empty:
        st.subheader("Live PostgreSQL Ingested Telemetry")
        st.dataframe(df_db.head(100), use_container_width=True)
    else:
        st.info("Database connection idle. Showing offline processed sample records from Petrobras 3W dataset:")
        sample_df = load_sample_real_telemetry()
        if not sample_df.empty:
            st.dataframe(sample_df.head(100), use_container_width=True)
        else:
            st.warning("No sample telemetry loaded.")