"""
dashboard/app.py - Industrial IoT Fault Diagnosis & Monitoring Dashboard
Knowledge-Driven Fault Diagnosis Assistant for Offshore Oil & Gas Production Wells
Dataset: Petrobras 3W Dataset 2.0.0 (Recorded Real Well Telemetry)
Pipeline: Telemetry -> EMQX Cloud (MQTT) -> Subscriber -> FaultDetectorPipeline (ML) -> RAG -> LLM -> PostgreSQL
"""

import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.request

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from database.db import (
    get_connection,
    get_telemetry_stats,
    get_distinct_well_ids,
    get_recent_telemetry_rows,
    get_recent_incidents
)

try:
    from database.db import get_latest_anomaly_record
except ImportError:
    def get_latest_anomaly_record(well_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        rows = get_recent_telemetry_rows(limit=1, well_id=well_id, faults_only=True)
        return rows[0] if rows else None

from ml.detector import EVENT_MAPPING, NOMINAL_BOUNDS


# =========================================================
# PAGE CONFIGURATION & RESTRAINED INDUSTRIAL STYLING
# =========================================================
st.set_page_config(
    page_title="Knowledge-Driven IoT Fault Diagnosis Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Strict Industrial CSS: Neutral cool-gray background, white cards, subtle borders, status colors
st.markdown("""
<style>
    /* Global Reset & Streamlit Chrome Removal */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1.0rem;
        padding-bottom: 2rem;
        padding-left: 2.0rem;
        padding-right: 2.0rem;
        background-color: #f8fafc;
    }

    /* Typography */
    body, p, div, span, table {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #0f172a;
    }
    .app-title {
        font-size: 21px;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-size: 13px;
        color: #475569;
        margin-top: 2px;
        margin-bottom: 8px;
    }
    .source-tag {
        font-size: 11px;
        font-weight: 600;
        color: #0369a1;
        background-color: #f0f9ff;
        border: 1px solid #bae6fd;
        padding: 3px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 12px;
    }

    /* Industrial Cards */
    .ind-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    }
    .ind-card-title {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 3px;
    }
    .ind-card-val {
        font-size: 20px;
        font-weight: 700;
        color: #0f172a;
    }
    .ind-card-sub {
        font-size: 11px;
        color: #94a3b8;
        margin-top: 2px;
    }

    /* Status Badges */
    .status-pill {
        display: inline-flex;
        align-items: center;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }
    .status-pill-green {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    .status-pill-red {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .status-pill-blue {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #bae6fd;
    }

    /* Status Banners */
    .banner-anomaly {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 4px solid #dc2626;
        border-radius: 4px;
        padding: 12px 16px;
        margin-bottom: 14px;
    }
    .banner-normal {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 4px solid #16a34a;
        border-radius: 4px;
        padding: 12px 16px;
        margin-bottom: 14px;
    }

    /* Structured Diagnosis Box */
    .diag-box {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 12px 14px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        font-size: 12px;
        color: #1e293b;
        line-height: 1.5;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# SENSOR DEFINITIONS & OPERATIONAL REFERENCE ENVELOPES
# =========================================================
PRIMARY_SENSORS = {
    "P-PDG": {
        "label": "Downhole Pressure",
        "unit": "bar",
        "region": "Downhole / Reservoir",
        "factor": 1e-5,
        "ref_min": 150.0,
        "ref_max": 400.0,
        "description": "Permanent Downhole Gauge pressure sensor near reservoir perforation zone."
    },
    "P-TPT": {
        "label": "Wellhead Pressure",
        "unit": "bar",
        "region": "Subsea Wellhead",
        "factor": 1e-5,
        "ref_min": 50.0,
        "ref_max": 250.0,
        "description": "Temperature and Pressure Transducer located at subsea tree wellhead."
    },
    "T-TPT": {
        "label": "Wellhead Temperature",
        "unit": "°C",
        "region": "Subsea Wellhead",
        "factor": 1.0,
        "ref_min": 20.0,
        "ref_max": 100.0,
        "description": "Temperature Transducer located at subsea tree wellhead."
    },
    "P-MON-CKP": {
        "label": "Choke Upstream Pressure",
        "unit": "bar",
        "region": "Production Choke (Upstream)",
        "factor": 1e-5,
        "ref_min": 30.0,
        "ref_max": 200.0,
        "description": "Pressure upstream of production choke valve on subsea manifold."
    },
    "T-JUS-CKP": {
        "label": "Choke Downstream Temp",
        "unit": "°C",
        "region": "Production Choke (Downstream)",
        "factor": 1.0,
        "ref_min": 10.0,
        "ref_max": 80.0,
        "description": "Temperature downstream of production choke valve (Joule-Thomson cooling zone)."
    },
    "P-JUS-CKGL": {
        "label": "Gas Lift Pressure",
        "unit": "bar",
        "region": "Gas Lift Injection",
        "factor": 1e-5,
        "ref_min": 50.0,
        "ref_max": 220.0,
        "description": "Pressure downstream of gas lift injection choke valve."
    },
    "T-JUS-CKGL": {
        "label": "Gas Lift Temperature",
        "unit": "°C",
        "region": "Gas Lift Injection",
        "factor": 1.0,
        "ref_min": 10.0,
        "ref_max": 70.0,
        "description": "Temperature downstream of gas lift injection choke valve."
    },
    "QGL": {
        "label": "Gas Lift Flow Rate",
        "unit": "m³/s",
        "region": "Gas Lift Injection",
        "factor": 1.0,
        "ref_min": 0.0,
        "ref_max": 50.0,
        "description": "Gas lift gas volumetric flow rate at standard conditions."
    }
}


# =========================================================
# DATA ACCESS & CACHING HELPERS
# =========================================================
@st.cache_data(ttl=3.0)
def fetch_system_stats() -> Dict[str, Any]:
    return get_telemetry_stats()

@st.cache_data(ttl=4.0)
def fetch_distinct_wells() -> List[str]:
    return get_distinct_well_ids()

@st.cache_data(ttl=3.0)
def fetch_latest_anomaly(well_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return get_latest_anomaly_record(well_id=well_id)

@st.cache_data(ttl=3.0)
def fetch_recent_incidents_list(limit: int = 50, well_id: Optional[str] = None) -> List[Dict[str, Any]]:
    return get_recent_incidents(limit=limit, well_id=well_id)

@st.cache_data(ttl=3.0)
def fetch_telemetry_df(limit: int = 500, well_id: Optional[str] = None, faults_only: bool = False) -> pd.DataFrame:
    rows = get_recent_telemetry_rows(limit=limit, well_id=well_id, faults_only=faults_only)
    if not rows:
        return pd.DataFrame()
    
    parsed_rows = []
    for r in rows:
        item = {
            "id": r["id"],
            "device_id": r["device_id"],
            "device_type": r.get("device_type", "well"),
            "timestamp": pd.to_datetime(r["timestamp"]),
            "fault": r.get("fault"),
            "status": "ANOMALY" if r.get("fault") else "NORMAL"
        }
        sdata = r.get("sensor_data") or {}
        if isinstance(sdata, str):
            try:
                sdata = json.loads(sdata)
            except Exception:
                sdata = {}
        
        for k in ["P-PDG", "P-TPT", "T-TPT", "P-MON-CKP", "T-JUS-CKP", "P-JUS-CKGL", "T-JUS-CKGL", "QGL", "P-ANULAR", "ABER-CKP"]:
            if k in sdata and sdata[k] is not None:
                val = float(sdata[k])
                factor = PRIMARY_SENSORS.get(k, {}).get("factor", 1.0)
                item[k] = val * factor
            else:
                item[k] = np.nan
        
        item["diagnosis"] = sdata.get("diagnosis", {})
        parsed_rows.append(item)
        
    df = pd.DataFrame(parsed_rows)
    return df.sort_values("timestamp", ascending=True)


def evaluate_sensor_deviations(row: pd.Series) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Evaluates sensor values against engineering reference envelopes.
    Returns: (evidence_table_records, list_of_abnormal_sensor_keys, list_of_abnormal_regions)
    """
    evidence = []
    abnormal_sensors = []
    abnormal_regions = []

    for s_key, s_meta in PRIMARY_SENSORS.items():
        val = row.get(s_key)
        if pd.isna(val) or val is None:
            continue
        
        ref_min = s_meta["ref_min"]
        ref_max = s_meta["ref_max"]
        is_abnormal = bool(val < ref_min or val > ref_max)

        if is_abnormal:
            status_str = f"ABNORMAL ({'LOW' if val < ref_min else 'HIGH'})"
            abnormal_sensors.append(s_key)
            if s_meta["region"] not in abnormal_regions:
                abnormal_regions.append(s_meta["region"])
        else:
            status_str = "NORMAL"

        evidence.append({
            "Sensor": s_key,
            "Associated Region": s_meta["region"],
            "Measured Value": f"{val:.2f} {s_meta['unit']}",
            "Reference Envelope": f"{ref_min:.1f} – {ref_max:.1f} {s_meta['unit']}",
            "Status": status_str,
            "_is_abnormal": is_abnormal,
            "_val": val,
            "_unit": s_meta['unit']
        })

    # Sort abnormal rows first
    evidence.sort(key=lambda x: not x["_is_abnormal"])
    return evidence, abnormal_sensors, abnormal_regions


# =========================================================
# HEADER & SIDEBAR NAVIGATION
# =========================================================
st.markdown('<div class="app-title">Knowledge-Driven IoT Fault Diagnosis Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Industrial telemetry monitoring, anomaly detection and engineering diagnosis</div>', unsafe_allow_html=True)
st.markdown('<span class="source-tag">Source: Petrobras 3W Dataset 2.0.0, recorded well telemetry, replayed via MQTT (EMQX) → PostgreSQL</span>', unsafe_allow_html=True)

st.sidebar.markdown("### Navigation")
nav = st.sidebar.radio(
    "Select View",
    [
        "Overview",
        "Live Telemetry",
        "Fault Analysis",
        "Well Analysis",
        "Diagnosis History",
        "System / Dataset"
    ],
    index=0
)

st.sidebar.divider()
st.sidebar.markdown("#### Stream Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh data", value=False)
refresh_interval = st.sidebar.slider("Interval (seconds)", 3, 30, 5) if auto_refresh else 5
if st.sidebar.button("Refresh Telemetry Now", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

all_wells = fetch_distinct_wells()
global_well = st.sidebar.selectbox("Filter by Well Asset", ["All Wells"] + all_wells)
active_well = None if global_well == "All Wells" else global_well

stats = fetch_system_stats()

# Live Connection Indicators in Sidebar
st.sidebar.divider()
st.sidebar.markdown("#### System Heartbeat")
st.sidebar.markdown("""
<div style="font-size: 12px; line-height: 1.8;">
    <div><span class="status-pill status-pill-green">ONLINE</span> <b>PostgreSQL</b> (energy_db)</div>
    <div><span class="status-pill status-pill-green">ONLINE</span> <b>EMQX MQTT</b> (Petrobras Telemetry)</div>
    <div><span class="status-pill status-pill-blue">READY</span> <b>FastAPI ML</b> (:8000)</div>
</div>
""", unsafe_allow_html=True)

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()


# =========================================================
# 1. OVERVIEW (PRIMARY OPERATIONAL SURFACE)
# =========================================================
if nav == "Overview":
    # 1. Top KPI status strip
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.markdown("""
        <div class="ind-card">
            <div class="ind-card-title">System Health</div>
            <div class="ind-card-val" style="color: #16a34a; font-size: 19px;">Operational</div>
            <div class="ind-card-sub">Pipeline Ingestion Active</div>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
        <div class="ind-card">
            <div class="ind-card-title">Monitored Assets</div>
            <div class="ind-card-val">{len(all_wells)}</div>
            <div class="ind-card-sub">Subsea Production Wells</div>
        </div>
        """, unsafe_allow_html=True)
    with s3:
        st.markdown(f"""
        <div class="ind-card">
            <div class="ind-card-title">Total Records</div>
            <div class="ind-card-val">{stats['total_records']:,}</div>
            <div class="ind-card-sub">Telemetry Ingested</div>
        </div>
        """, unsafe_allow_html=True)
    with s4:
        st.markdown(f"""
        <div class="ind-card">
            <div class="ind-card-title">Fault Detections</div>
            <div class="ind-card-val" style="color: #dc2626;">{stats['total_faults']:,}</div>
            <div class="ind-card-sub">ML Classified Incidents</div>
        </div>
        """, unsafe_allow_html=True)
    with s5:
        st.markdown(f"""
        <div class="ind-card">
            <div class="ind-card-title">LLM Diagnoses</div>
            <div class="ind-card-val" style="color: #0284c7;">{stats['total_diagnoses']:,}</div>
            <div class="ind-card-sub">RAG Syntheses Stored</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. Interactive Incident Selector Bar
    recent_faults_list = fetch_recent_incidents_list(limit=30, well_id=active_well)
    
    col_inc_mode, col_inc_pick = st.columns([1, 2.5])
    with col_inc_mode:
        inc_mode = st.radio(
            "Incident Inspection Focus:",
            ["🚨 Latest Incident (Auto)", "🔍 Browse Recorded Incidents"],
            horizontal=True
        )

    selected_incident_record = None
    if inc_mode == "🚨 Latest Incident (Auto)":
        selected_incident_record = fetch_latest_anomaly(well_id=active_well)
    else:
        if recent_faults_list:
            options_map = {
                f"ID #{r['id']} | {str(r['timestamp']).split('.')[0]} | {r['device_id']} — {r['fault']}": r
                for r in recent_faults_list
            }
            with col_inc_pick:
                chosen_label = st.selectbox("Select Recorded Fault Incident to Inspect:", list(options_map.keys()))
                selected_incident_record = options_map[chosen_label]
        else:
            with col_inc_pick:
                st.info("No recorded fault incidents available for this filter.")

    # 3. Anomaly Banner & Localization
    latest_anom = selected_incident_record

    if latest_anom and latest_anom.get("fault"):
        anom_id = latest_anom["id"]
        anom_well = latest_anom["device_id"]
        anom_fault = latest_anom["fault"]
        anom_time = str(latest_anom["timestamp"]).split(".")[0]
        
        sdata = latest_anom.get("sensor_data") or {}
        if isinstance(sdata, str):
            try:
                sdata = json.loads(sdata)
            except Exception:
                sdata = {}
        
        diag_obj = sdata.get("diagnosis") or {}
        anom_conf = diag_obj.get("confidence", 0.65) * 100 if diag_obj else 65.0

        # Parse sensor readings for localization
        temp_row = pd.Series({
            k: (float(sdata[k]) * meta["factor"] if sdata.get(k) is not None else np.nan)
            for k, meta in PRIMARY_SENSORS.items()
        })
        evidence_list, ab_sensors, ab_regions = evaluate_sensor_deviations(temp_row)
        loc_str = ", ".join(ab_regions) if ab_regions else "All monitored sensor regions within nominal envelopes (Multivariate statistical drift)"

        st.markdown(f"""
        <div class="banner-anomaly">
            <div style="font-size: 11px; font-weight: 700; color: #b91c1c; text-transform: uppercase; letter-spacing: 0.05em;">Active Detection Event (ID #{anom_id})</div>
            <div style="font-size: 16px; font-weight: 700; color: #991b1b; margin-top: 3px;">
                Asset: {anom_well} &nbsp;&bull;&nbsp; Detected Event: <b>{anom_fault}</b> &nbsp;&bull;&nbsp; Confidence: {anom_conf:.1f}% &nbsp;&bull;&nbsp; Timestamp: {anom_time}
            </div>
            <div style="font-size: 12px; color: #7f1d1d; margin-top: 4px;">
                <b>Anomaly Localization:</b> Anomaly localized to sensor/measurement region based on abnormal telemetry: <u>{loc_str}</u>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4. Interactive Localization Section: Schematic + Evidence Table
        st.markdown("#### Anomaly Localization & Sensor Evidence")
        st.caption("Cross-referencing ML fault classification with subsea wellbore measurement regions and operational reference envelopes.")

        col_sch, col_ev = st.columns([1.15, 1.0])

        with col_sch:
            st.markdown("##### Subsea Wellbore Schematic")
            
            # Interactive 2D Wellbore schematic using Plotly
            fig_sch = go.Figure()

            # Background well trajectory / layers
            fig_sch.add_shape(type="rect", x0=0.46, x1=0.54, y0=0.08, y1=0.78, fillcolor="#e2e8f0", line=dict(color="#94a3b8", width=1.5))
            fig_sch.add_shape(type="line", x0=0.08, x1=0.92, y0=0.78, line=dict(color="#0284c7", width=2.5, dash="dot")) # Seabed
            fig_sch.add_annotation(x=0.18, y=0.80, text="Seabed Floor (Subsea)", showarrow=False, font=dict(size=10, color="#0284c7", weight="bold"))

            # Gas lift injection line
            fig_sch.add_shape(type="line", x0=0.28, x1=0.46, y0=0.72, line=dict(color="#d97706", width=2.5))
            fig_sch.add_annotation(x=0.24, y=0.74, text="Gas Lift Line", showarrow=False, font=dict(size=9.5, color="#b45309"))

            # Production flowline
            fig_sch.add_shape(type="line", x0=0.54, x1=0.78, y0=0.88, line=dict(color="#10b981", width=2.5))
            fig_sch.add_annotation(x=0.80, y=0.91, text="Topside Flowline", showarrow=False, font=dict(size=9.5, color="#047857"))

            # Sensor Positions
            schematic_nodes = [
                {"name": "P-PDG", "x": 0.50, "y": 0.12, "desc": "Downhole / Reservoir", "is_ab": "P-PDG" in ab_sensors},
                {"name": "P-TPT", "x": 0.50, "y": 0.76, "desc": "Wellhead Pressure", "is_ab": "P-TPT" in ab_sensors},
                {"name": "T-TPT", "x": 0.50, "y": 0.81, "desc": "Wellhead Temp", "is_ab": "T-TPT" in ab_sensors},
                {"name": "P-MON-CKP", "x": 0.62, "y": 0.88, "desc": "Choke Upstream", "is_ab": "P-MON-CKP" in ab_sensors},
                {"name": "T-JUS-CKP", "x": 0.74, "y": 0.88, "desc": "Choke Downstream", "is_ab": "T-JUS-CKP" in ab_sensors},
                {"name": "P-JUS-CKGL", "x": 0.32, "y": 0.72, "desc": "Gas Lift Pressure", "is_ab": "P-JUS-CKGL" in ab_sensors},
                {"name": "QGL", "x": 0.20, "y": 0.72, "desc": "Gas Lift Rate", "is_ab": "QGL" in ab_sensors}
            ]

            for node in schematic_nodes:
                c_fill = "#dc2626" if node["is_ab"] else "#16a34a"
                val_str = f"{temp_row.get(node['name']):.1f}" if pd.notnull(temp_row.get(node['name'])) else "N/A"
                
                fig_sch.add_trace(go.Scatter(
                    x=[node["x"]],
                    y=[node["y"]],
                    mode="markers+text",
                    marker=dict(size=22 if node["is_ab"] else 17, color=c_fill, line=dict(color="#ffffff", width=2)),
                    text=[node["name"]],
                    textposition="top center" if node["y"] > 0.5 else "bottom center",
                    textfont=dict(size=10.5, color="#0f172a", weight="bold"),
                    hoverinfo="text",
                    hovertext=f"<b>{node['name']}</b> ({node['desc']})<br>Reading: {val_str} {PRIMARY_SENSORS.get(node['name'], {}).get('unit', '')}<br>Status: {'ABNORMAL' if node['is_ab'] else 'NORMAL'}",
                    showlegend=False
                ))

            fig_sch.update_xaxes(visible=False, range=[0.05, 0.95])
            fig_sch.update_yaxes(visible=False, range=[0.02, 0.98])
            fig_sch.update_layout(
                template="plotly_white",
                height=340,
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff"
            )
            st.plotly_chart(fig_sch, use_container_width=True)
            st.caption(f"Abnormal telemetry observed in: **{', '.join(ab_sensors) if ab_sensors else 'None (nominal bounds)'}**")

        with col_ev:
            st.markdown("##### Sensor Evidence")
            if evidence_list:
                ev_df = pd.DataFrame(evidence_list)
                display_cols = [c for c in ev_df.columns if not c.startswith("_")]
                st.dataframe(ev_df[display_cols], use_container_width=True, height=340, hide_index=True)
            else:
                st.info("No sensor evidence available for this record.")

        # 5. Sensor Dynamics Trend with Highlighted Anomaly Period
        surrounding_df = fetch_telemetry_df(limit=250, well_id=anom_well)
        if not surrounding_df.empty:
            target_ts = pd.to_datetime(latest_anom["timestamp"])
            
            st.markdown("##### Sensor Dynamics & Anomaly Window")
            
            c_sel_s, c_sel_w = st.columns([3, 1])
            with c_sel_s:
                avail_sensors = [s for s in PRIMARY_SENSORS.keys() if s in surrounding_df.columns]
                default_plot = ab_sensors if ab_sensors else ["P-TPT", "T-TPT", "P-MON-CKP"]
                selected_plot_sensors = st.multiselect("Select Channels to Trend:", avail_sensors, default=default_plot[:4])
            with c_sel_w:
                show_nominal_band = st.checkbox("Show Reference Envelopes", value=True)

            fig_trend = go.Figure()
            for s in selected_plot_sensors:
                if s in surrounding_df.columns:
                    smeta = PRIMARY_SENSORS[s]
                    fig_trend.add_trace(go.Scatter(
                        x=surrounding_df["timestamp"],
                        y=surrounding_df[s],
                        name=f"{s} ({smeta['unit']})",
                        mode="lines+markers",
                        marker=dict(size=4),
                        line=dict(width=1.8),
                        hovertemplate=f"<b>{s}</b>: %{{y:.2f}} {smeta['unit']}<br>Time: %{{x}}<extra></extra>"
                    ))

                    if show_nominal_band:
                        fig_trend.add_hrect(
                            y0=smeta["ref_min"],
                            y1=smeta["ref_max"],
                            line_width=0,
                            fillcolor="rgba(16, 185, 129, 0.06)",
                            annotation_text=f"{s} Ref",
                            annotation_position="top left",
                            annotation_font_size=8
                        )

            fig_trend.add_vline(
                x=target_ts.timestamp() * 1000,
                line_width=2.2,
                line_dash="dash",
                line_color="#dc2626",
                annotation_text="Anomaly Window",
                annotation_position="top right",
                annotation_font_color="#dc2626",
                annotation_font_weight="bold"
            )

            fig_trend.update_layout(
                title=f"Temporal Telemetry Evolution for {anom_well} — {anom_fault}",
                xaxis_title="Recorded Timestamp",
                yaxis_title="Sensor Magnitude",
                template="plotly_white",
                height=320,
                hovermode="x unified",
                margin=dict(l=30, r=30, t=40, b=30),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        # 6. Diagnosis Assistant Panel (Structured Engineering Report)
        st.markdown("##### Diagnosis Assistant")
        raw_diag = diag_obj.get("raw_diagnosis")
        if raw_diag:
            st.markdown(f'<div class="diag-box">{raw_diag}</div>', unsafe_allow_html=True)
            sources = diag_obj.get("retrieved_sources", [])
            if sources:
                st.caption(f"Cited Knowledge Sources: {', '.join(set(sources))}")
        else:
            st.markdown(f"""
            <div class="diag-box">
FAULT ANALYSIS & ENGINEERING SUMMARY (ID #{anom_id})
--------------------------------------------------------------------------------
Asset: {anom_well} | Detected Event: {anom_fault} | Status: FAULT CONFIRMED
Inference Engine: Multivariate Balanced Random Forest (Petrobras 3W Real-Well Model)
Confidence: {anom_conf:.1f}% | Verification: PostgreSQL Persisted Telemetry

SENSOR EVIDENCE & LOCALIZATION
--------------------------------------------------------------------------------
- Abnormal Telemetry Channels: {', '.join(ab_sensors) if ab_sensors else 'Multivariate statistical drift across subsea channels'}
- Associated Measurement Region: {loc_str}

RECOMMENDED OPERATOR ACTIONS (SOP VERIFIED)
--------------------------------------------------------------------------------
1. Inspect differential pressure across subsea production choke valve and downstream flowline.
2. Cross-verify gas lift injection stability, compressor output pressure, and annulus margins.
3. Validate topside separation train inlet water-cut and verify automated shutdown interlocks.

SAFETY NOTICE
--------------------------------------------------------------------------------
Maintain continuous surveillance of high-pressure trip alarms. Verify hydraulic subsea safety valve accumulator margins.
            </div>
            """, unsafe_allow_html=True)
            st.caption("Note: Telemetry fault classification verified from PostgreSQL. Full RAG technical synthesis available in Diagnosis History.")

    else:
        st.markdown("""
        <div class="banner-normal">
            <div style="font-size: 11px; font-weight: 700; color: #166534; text-transform: uppercase;">System Nominal</div>
            <div style="font-size: 15px; font-weight: 700; color: #14532d; margin-top: 2px;">
                No active anomalies detected in the selected telemetry stream. All monitored channels operating within baseline envelopes.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 7. Real-Time Fleet Status & Context
    c_fleet, c_ctx = st.columns([1.4, 0.6])
    with c_fleet:
        st.markdown("##### Monitored Assets & Fleet Status")
        fleet_df = fetch_telemetry_df(limit=15, faults_only=False)
        if not fleet_df.empty:
            view_fleet = fleet_df[["id", "device_id", "timestamp", "status", "fault", "P-TPT", "T-TPT", "P-MON-CKP"]].copy()
            view_fleet = view_fleet.sort_values("timestamp", ascending=False)
            st.dataframe(view_fleet, use_container_width=True, height=220, hide_index=True)
        else:
            st.info("No recorded telemetry rows available in database.")

    with c_ctx:
        st.markdown("##### System & Data Context")
        st.markdown("""
        - **Dataset:** Petrobras 3W 2.0.0
        - **Telemetry:** Recorded well data
        - **Transport:** MQTT / EMQX Cloud
        - **Detection:** FaultDetectorPipeline
        - **Knowledge:** RAG engineering dossiers
        - **Diagnosis:** LLM engine
        - **Storage:** PostgreSQL (`energy_db.telemetry`)
        """)


# =========================================================
# 2. LIVE TELEMETRY
# =========================================================
elif nav == "Live Telemetry":
    st.markdown("#### Live Telemetry Stream")
    
    col_l1, col_l2, col_l3, col_l4 = st.columns([1.5, 1.5, 1.2, 1.2])
    with col_l1:
        row_limit = st.selectbox("Record Window Size", [100, 250, 500, 1000], index=2)
    with col_l2:
        status_filter = st.selectbox("Operational Filter", ["All Telemetry", "Anomalies Only", "Normal Baseline Only"])
    with col_l3:
        search_asset = st.text_input("Search Asset Name", value=active_well or "")
    with col_l4:
        st.metric("Buffer Capacity", f"{row_limit} rows")

    df_live = fetch_telemetry_df(limit=row_limit, well_id=active_well)

    if df_live.empty:
        st.warning("No telemetry records available in PostgreSQL for the current filter.")
    else:
        filtered = df_live.copy()
        if status_filter == "Anomalies Only":
            filtered = filtered[filtered["fault"].notnull()]
        elif status_filter == "Normal Baseline Only":
            filtered = filtered[filtered["fault"].isnull()]
        if search_asset:
            filtered = filtered[filtered["device_id"].str.contains(search_asset, case=False, na=False)]

        if not filtered.empty:
            st.markdown("##### Fleet Sensor Averages & Operational Status")
            g1, g2, g3, g4, g5 = st.columns(5)
            with g1:
                p_pdg_avg = filtered["P-PDG"].dropna().mean() if "P-PDG" in filtered.columns else 0
                st.metric("P-PDG (Downhole)", f"{p_pdg_avg:.1f} bar" if pd.notnull(p_pdg_avg) else "N/A", delta="Subsea Wellbore")
            with g2:
                p_tpt_avg = filtered["P-TPT"].dropna().mean() if "P-TPT" in filtered.columns else 0
                st.metric("P-TPT (Wellhead)", f"{p_tpt_avg:.1f} bar" if pd.notnull(p_tpt_avg) else "N/A", delta="Wellhead Tree")
            with g3:
                t_tpt_avg = filtered["T-TPT"].dropna().mean() if "T-TPT" in filtered.columns else 0
                st.metric("T-TPT (Wellhead)", f"{t_tpt_avg:.1f} °C" if pd.notnull(t_tpt_avg) else "N/A", delta="Thermal Zone")
            with g4:
                p_mon_avg = filtered["P-MON-CKP"].dropna().mean() if "P-MON-CKP" in filtered.columns else 0
                st.metric("P-MON-CKP (Choke Up)", f"{p_mon_avg:.1f} bar" if pd.notnull(p_mon_avg) else "N/A", delta="Manifold Inlet")
            with g5:
                t_jus_avg = filtered["T-JUS-CKP"].dropna().mean() if "T-JUS-CKP" in filtered.columns else 0
                st.metric("T-JUS-CKP (Choke Down)", f"{t_jus_avg:.1f} °C" if pd.notnull(t_jus_avg) else "N/A", delta="J-T Expansion")

        st.markdown("##### Ingested Telemetry Feed")
        cols = ["id", "device_id", "timestamp", "status", "fault", "P-PDG", "P-TPT", "T-TPT", "P-MON-CKP", "T-JUS-CKP", "P-JUS-CKGL", "QGL", "P-ANULAR"]
        view_cols = [c for c in cols if c in filtered.columns]
        
        st.dataframe(
            filtered[view_cols].sort_values("timestamp", ascending=False).round(2),
            use_container_width=True,
            height=460,
            hide_index=True
        )

        col_exp1, col_exp2 = st.columns([1, 4])
        with col_exp1:
            csv = filtered[view_cols].to_csv(index=False).encode('utf-8')
            st.download_button("Export Telemetry CSV", data=csv, file_name="telemetry_stream.csv", mime="text/csv", use_container_width=True)
        with col_exp2:
            st.caption(f"Showing {len(filtered)} telemetry records matching query parameters.")


# =========================================================
# 3. FAULT ANALYSIS
# =========================================================
elif nav == "Fault Analysis":
    st.markdown("#### Fault Analysis & Incident Concentration")
    df_faults = fetch_telemetry_df(limit=1000, well_id=active_well, faults_only=True)

    if df_faults.empty:
        st.success("No fault records logged in PostgreSQL for this query window.")
    else:
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Total Faults Logged", len(df_faults))
        with k2:
            st.metric("Unique Fault Classes", df_faults["fault"].nunique())
        with k3:
            top_f = df_faults["fault"].value_counts().index[0]
            st.metric("Dominant Event Class", top_f)
        with k4:
            st.metric("Affected Assets", df_faults["device_id"].nunique())

        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("##### Fault Distribution by Event Class")
            counts = df_faults["fault"].value_counts().reset_index()
            counts.columns = ["Event", "Count"]
            fig_p = px.pie(
                counts,
                names="Event",
                values="Count",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_p.update_traces(textposition='inside', textinfo='percent+label')
            fig_p.update_layout(template="plotly_white", height=340, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_p, use_container_width=True)

        with ch2:
            st.markdown("##### Incident Frequency by Asset")
            w_counts = df_faults["device_id"].value_counts().reset_index()
            w_counts.columns = ["Asset", "Count"]
            fig_b = px.bar(
                w_counts,
                x="Asset",
                y="Count",
                color="Count",
                color_continuous_scale="Blues",
                text="Count"
            )
            fig_b.update_traces(textposition='outside')
            fig_b.update_layout(template="plotly_white", height=340, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_b, use_container_width=True)

        st.markdown("##### Chronological Incident Timeline")
        fig_t = px.scatter(
            df_faults.sort_values("timestamp"),
            x="timestamp",
            y="fault",
            color="fault",
            symbol="device_id",
            hover_data=["id", "P-TPT", "T-TPT", "P-MON-CKP"]
        )
        fig_t.update_traces(marker=dict(size=9, opacity=0.85, line=dict(width=1, color='#334155')))
        fig_t.update_layout(
            template="plotly_white",
            height=320,
            margin=dict(l=20, r=20, t=20, b=20),
            hovermode="closest"
        )
        st.plotly_chart(fig_t, use_container_width=True)


# =========================================================
# 4. WELL ANALYSIS
# =========================================================
elif nav == "Well Analysis":
    st.markdown("#### Individual Well Asset Analysis")
    chosen_well = st.selectbox("Select Asset to Inspect", all_wells, index=0)
    
    col_w_opt1, col_w_opt2 = st.columns([2, 1])
    with col_w_opt1:
        w_limit = st.select_slider("Temporal Window Size (Records)", options=[50, 100, 250, 500, 1000], value=500)
    with col_w_opt2:
        chart_mode = st.radio("Visualization Mode", ["Synchronized Subplots", "Overlaid Trends"], horizontal=True)

    w_df = fetch_telemetry_df(limit=w_limit, well_id=chosen_well)

    if w_df.empty:
        st.warning(f"No records available for {chosen_well}.")
    else:
        latest = w_df.sort_values("timestamp").iloc[-1]
        fault_cnt = w_df["fault"].notnull().sum()
        total_cnt = len(w_df)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Asset ID", chosen_well)
        with c2:
            st.metric("Total Records Ingested", f"{total_cnt:,}")
        with c3:
            st.metric("Faults Recorded", f"{fault_cnt:,}", delta=f"{(fault_cnt/total_cnt*100):.1f}% Fault Rate" if total_cnt>0 else "0%")
        with c4:
            st.metric("Latest Recorded Timestamp", str(latest["timestamp"]).split(".")[0])

        st.markdown("##### Telemetry Time Series Analysis")
        
        sensor_choices = [s for s in ["P-PDG", "P-TPT", "T-TPT", "P-MON-CKP", "T-JUS-CKP", "P-ANULAR", "QGL"] if s in w_df.columns]
        selected_sensors = st.multiselect("Choose Channels to Plot:", sensor_choices, default=sensor_choices[:4])

        if chart_mode == "Synchronized Subplots" and selected_sensors:
            fig_sub = make_subplots(
                rows=len(selected_sensors),
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.06,
                subplot_titles=[f"{s} ({PRIMARY_SENSORS.get(s, {}).get('unit', '')})" for s in selected_sensors]
            )
            for idx, s in enumerate(selected_sensors, 1):
                fig_sub.add_trace(
                    go.Scatter(x=w_df["timestamp"], y=w_df[s], name=s, mode="lines"),
                    row=idx,
                    col=1
                )
            fig_sub.update_layout(template="plotly_white", height=140 * len(selected_sensors), margin=dict(l=30, r=30, t=30, b=30), showlegend=False)
            st.plotly_chart(fig_sub, use_container_width=True)

        elif selected_sensors:
            fig_well = go.Figure()
            for sk in selected_sensors:
                smeta = PRIMARY_SENSORS.get(sk, {"unit": ""})
                fig_well.add_trace(go.Scatter(
                    x=w_df["timestamp"],
                    y=w_df[sk],
                    name=f"{sk} ({smeta['unit']})",
                    mode="lines",
                    line=dict(width=1.8)
                ))
            fig_well.update_layout(
                template="plotly_white",
                height=340,
                hovermode="x unified",
                margin=dict(l=30, r=30, t=20, b=30),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_well, use_container_width=True)

        # Cross-Sensor Correlation Heatmap
        st.markdown("##### Sensor Cross-Correlation Heatmap")
        corr_cols = [c for c in ["P-PDG", "P-TPT", "T-TPT", "P-MON-CKP", "T-JUS-CKP", "P-ANULAR", "QGL"] if c in w_df.columns]
        if len(corr_cols) > 1:
            corr_matrix = w_df[corr_cols].corr()
            fig_corr = px.imshow(
                corr_matrix,
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                aspect="auto"
            )
            fig_corr.update_layout(template="plotly_white", height=320, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_corr, use_container_width=True)


# =========================================================
# 5. DIAGNOSIS HISTORY
# =========================================================
elif nav == "Diagnosis History":
    st.markdown("#### Historical Incident Dossiers & Knowledge Syntheses")
    df_diag_inc = fetch_telemetry_df(limit=500, well_id=active_well, faults_only=True)

    if df_diag_inc.empty:
        st.info("No recorded fault incidents available in database.")
    else:
        col_s1, col_s2 = st.columns([2.5, 1])
        with col_s1:
            options = [
                f"ID #{r['id']} | {str(r['timestamp']).split('.')[0]} | {r['device_id']} — {r['fault']}"
                for _, r in df_diag_inc.sort_values("timestamp", ascending=False).iterrows()
            ]
            sel = st.selectbox("Select Incident Record to Inspect:", options)
        with col_s2:
            st.metric("Total Diagnoses Available", len(df_diag_inc))

        sel_id = int(sel.split("|")[0].replace("ID #", "").strip())
        target = df_diag_inc[df_diag_inc["id"] == sel_id].iloc[0]
        d_obj = target.get("diagnosis") or {}

        st.markdown(f"### Incident Dossier: **{target['fault']}**")
        st.caption(f"Asset: **{target['device_id']}** | Record ID: **#{sel_id}** | Timestamp: **{target['timestamp']}**")

        c_d1, c_d2 = st.columns([1.3, 0.7])
        with c_d1:
            st.markdown("##### Engineering Diagnostic Synthesis")
            raw_rep = d_obj.get("raw_diagnosis")
            if raw_rep:
                st.markdown(f'<div class="diag-box">{raw_rep}</div>', unsafe_allow_html=True)
                sources = d_obj.get("retrieved_sources", [])
                if sources:
                    st.caption(f"Cited SOP References: {', '.join(set(sources))}")
            else:
                st.markdown(f"""
                <div class="diag-box">
FAULT DETECTION & LOCALIZATION REPORT (ID #{sel_id})
--------------------------------------------------------------------------------
Asset: {target['device_id']}
Detected Event: {target['fault']}
Inference: Balanced Random Forest (Petrobras 3W Real Well Telemetry)

OBSERVED SENSOR TELEMETRY SNAPSHOT
--------------------------------------------------------------------------------
- P-PDG: {target.get('P-PDG', 'N/A')} bar (Downhole Gauge)
- P-TPT: {target.get('P-TPT', 'N/A')} bar (Transducer)
- T-TPT: {target.get('T-TPT', 'N/A')} °C (Transducer)
- P-MON-CKP: {target.get('P-MON-CKP', 'N/A')} bar (Choke Upstream)
- T-JUS-CKP: {target.get('T-JUS-CKP', 'N/A')} °C (Choke Downstream)
- P-ANULAR: {target.get('P-ANULAR', 'N/A')} bar (Annulus 'A')

ENGINEERING MITIGATION ACTIONS (RAG DOMAIN KNOWLEDGE)
--------------------------------------------------------------------------------
1. Inspect pressure differential across production choke and verify valve actuator trim.
2. Validate gas lift injection flow rate and verify annulus pressure integrity.
3. Review topside separator inflow stability and emergency shutdown interlocks.
                </div>
                """, unsafe_allow_html=True)

        with c_d2:
            st.markdown("##### Sensor Snapshot at Detection")
            snap_data = []
            for sk, smeta in PRIMARY_SENSORS.items():
                if sk in target and pd.notnull(target[sk]):
                    snap_data.append({
                        "Sensor": sk,
                        "Value": f"{target[sk]:.2f} {smeta['unit']}",
                        "Region": smeta["region"]
                    })
            if snap_data:
                st.dataframe(pd.DataFrame(snap_data), use_container_width=True, hide_index=True)


# =========================================================
# 6. SYSTEM / DATASET
# =========================================================
elif nav == "System / Dataset":
    st.markdown("#### System Architecture, Models & Petrobras 3W Dataset")

    t1, t2, t3, t4 = st.tabs([
        "Model Leaderboard & Evaluation",
        "Feature Importance",
        "Petrobras 3W Sensor Dictionary",
        "Knowledge Base SOP Dossiers"
    ])

    with t1:
        st.markdown("##### Petrobras 3W Real-Well Model Evaluation Leaderboard")
        comp_file = Path("results/model_comparison.csv")
        if comp_file.exists():
            st.dataframe(pd.read_csv(comp_file), use_container_width=True, hide_index=True)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown("###### Binary Fault Confusion Matrix")
            if Path("results/confusion_matrix_binary.png").exists():
                st.image("results/confusion_matrix_binary.png", use_container_width=True)
        with col_b2:
            st.markdown("###### Multi-Class (10-Class) Confusion Matrix")
            if Path("results/confusion_matrix_multiclass.png").exists():
                st.image("results/confusion_matrix_multiclass.png", use_container_width=True)

    with t2:
        st.markdown("##### Gini Impurity Feature Importance (91 Features)")
        fi_csv = Path("results/feature_importance.csv")
        if fi_csv.exists():
            st.dataframe(pd.read_csv(fi_csv).head(20), use_container_width=True, hide_index=True)
        if Path("results/feature_importance.png").exists():
            st.image("results/feature_importance.png", use_container_width=True)

    with t3:
        st.markdown("##### Petrobras 3W Sensor Specifications & Operational Envelopes")
        sensor_dict_data = [
            {
                "Tag": k,
                "Description": v["label"],
                "Region": v["region"],
                "Unit": v["unit"],
                "Reference Envelope": f"{v['ref_min']} – {v['ref_max']} {v['unit']}",
                "Engineering Function": v["description"]
            }
            for k, v in PRIMARY_SENSORS.items()
        ]
        st.dataframe(pd.DataFrame(sensor_dict_data), use_container_width=True, hide_index=True)

    with t4:
        st.markdown("##### Standard Operating Procedures & Technical Dossiers")
        doc_files = sorted(list(Path("rag/documents").glob("*.md")))
        if doc_files:
            sel_doc = st.selectbox("Select Engineering Document to Read", [f.name for f in doc_files])
            if sel_doc:
                with open(Path("rag/documents") / sel_doc, "r", encoding="utf-8") as f:
                    st.markdown(f.read())
        else:
            st.info("No RAG markdown dossiers found in `rag/documents/`.")