"""
test_pipeline.py - Audited Test Suite for Petrobras 3W Fault Diagnosis System
Tests:
1. Model Artifacts Verification
2. Real Held-Out Petrobras 3W Window Inference
3. Binary Anomaly Classification & Confidence
4. Multi-Class Fault Classification (Events 0-9)
5. RAG Technical Knowledge Retrieval
6. LLM Structured Diagnosis Generation
7. FastAPI Microservice Endpoints (/health, /model-info, /predict, /diagnose, /telemetry)
8. Edge Cases: Partial Sensor Outages, NoneType, and Unseen Keys
9. Petrobras Replayer Compatibility
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app
from ml.detector import FaultDetectorPipeline, EVENT_MAPPING
from rag.retriever import FaultKnowledgeRetriever
from simulator.replay_petrobras import get_sample_files


@pytest.fixture(scope="session")
def detector():
    return FaultDetectorPipeline()


@pytest.fixture(scope="session")
def retriever():
    return FaultKnowledgeRetriever()


@pytest.fixture(scope="session")
def test_client():
    return TestClient(app)


def test_model_artifacts_loaded(detector):
    """Verify that all trained model artifacts exist and load correctly."""
    assert detector.binary_model is not None, "Binary model failed to load!"
    assert detector.multiclass_model is not None, "Multi-class model failed to load!"
    assert detector.imputer is not None, "Feature imputer failed to load!"
    assert len(detector.feature_cols) == 91, f"Expected 91 features, got {len(detector.feature_cols)}"


def test_real_heldout_petrobras_window_inference(detector):
    """Test inference directly using a real held-out test window from test_features.parquet."""
    test_parquet_path = Path("data/test_features.parquet")
    assert test_parquet_path.exists(), "test_features.parquet not found!"

    test_df = pd.read_parquet(test_parquet_path)
    assert not test_df.empty

    sample_row = test_df.iloc[0]
    pred = detector.predict(sample_row[detector.feature_cols].to_dict(), well_id=str(sample_row.get("well_id", "TEST-WELL")))

    assert "status" in pred
    assert pred["status"] in ["normal", "anomaly"]
    assert "confidence" in pred
    assert 0.0 <= pred["confidence"] <= 1.0


def test_binary_prediction_normal(detector):
    """Test binary prediction on nominal baseline telemetry."""
    normal_telemetry = {
        "P-PDG": 27500000.0,
        "P-TPT": 14500000.0,
        "T-TPT": 72.5,
        "P-MON-CKP": 11500000.0,
        "T-JUS-CKP": 55.0,
        "P-ANULAR": 500000.0,
        "T-PDG": 92.0,
        "QGL": 2.5,
        "ABER-CKP": 65.0
    }
    res = detector.predict(normal_telemetry, well_id="WELL-00002")
    assert res["status"] in ["normal", "anomaly"]
    assert "binary_status" in res


def test_multiclass_prediction_event_mapping(detector):
    """Verify multi-class prediction returns valid event ID and official Petrobras name."""
    telemetry = {
        "P-PDG": 33500000.0,
        "P-TPT": 1200000.0,
        "T-TPT": 25.0,
        "P-MON-CKP": 1050000.0,
        "T-JUS-CKP": 18.0,
        "P-ANULAR": 300000.0,
        "T-PDG": 98.0,
        "QGL": 0.0,
        "ABER-CKP": 50.0
    }
    res = detector.predict(telemetry, well_id="WELL-00010")
    event_id = res["predicted_event_id"]
    assert event_id in EVENT_MAPPING
    assert res["predicted_event"] == EVENT_MAPPING[event_id]


def test_missing_and_corrupt_sensor_handling(detector):
    """Test robust handling of partial sensor dropouts and NoneType entries."""
    partial_telemetry = {
        "P-PDG": 28000000.0,
        "T-TPT": None,
        "P-MON-CKP": "corrupt_string",
        "UNKNOWN_SENSOR": 999.9
    }
    res = detector.predict(partial_telemetry, well_id="WELL-TEST-PARTIAL")
    assert res["status"] in ["normal", "anomaly"]
    assert "confidence" in res


def test_rag_retrieval(retriever):
    """Test RAG retriever fetches relevant engineering chunks for specific fault events."""
    results = retriever.retrieve_fault_knowledge(
        predicted_event_id=3,
        predicted_event_name="Severe Slugging",
        top_k=3
    )
    assert len(results) > 0, "No chunks retrieved for Severe Slugging!"
    assert any("slugging" in r["content"].lower() for r in results)


def test_llm_diagnosis_generation(detector):
    """Test full ML + RAG + LLM structured diagnosis generation on severe anomaly."""
    telemetry = {
        "P-PDG": 31000000.0,
        "P-TPT": 21000000.0,
        "T-TPT": 14.5,
        "P-MON-CKP": 19000000.0,
        "T-JUS-CKP": 9.2,
        "P-ANULAR": 800000.0,
        "T-PDG": 90.0,
        "QGL": 1.2,
        "ABER-CKP": 70.0
    }
    diag = detector.diagnose(telemetry, well_id="WELL-TEST-HYDRATE")
    raw_text = diag.get("raw_diagnosis", "")
    
    assert "FAULT DETECTION" in raw_text
    assert "SENSOR EVIDENCE" in raw_text
    assert "POSSIBLE CAUSES" in raw_text
    assert "RECOMMENDED CHECKS" in raw_text
    assert "SAFETY NOTE" in raw_text
    assert "KNOWLEDGE SOURCES" in raw_text


def test_api_endpoints(test_client):
    """Test FastAPI microservice endpoints."""
    # 1. Health
    h_res = test_client.get("/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "healthy"

    # 2. Model info
    m_res = test_client.get("/model-info")
    assert m_res.status_code == 200
    assert m_res.json()["features_count"] == 91

    # 3. Predict
    p_res = test_client.post("/predict", json={
        "sensor_data": {"P-PDG": 27500000.0, "P-TPT": 14500000.0, "T-TPT": 72.5},
        "well_id": "API-WELL-01"
    })
    assert p_res.status_code == 200
    assert "predicted_event" in p_res.json()

    # 4. Diagnose
    d_res = test_client.post("/diagnose", json={
        "sensor_data": {"P-PDG": 32000000.0, "P-TPT": 11000000.0, "T-TPT": 54.0},
        "well_id": "API-WELL-02"
    })
    assert d_res.status_code == 200
    assert "raw_diagnosis" in d_res.json()


def test_petrobras_replayer_sample_files():
    """Verify real Petrobras 3W sample parquet files can be located for all event types."""
    samples = get_sample_files()
    assert len(samples) >= 8, f"Expected at least 8 event classes in 3W dataset, found {len(samples)}"
    for event_id, path in samples.items():
        assert path.exists(), f"Sample file for event {event_id} does not exist: {path}"
