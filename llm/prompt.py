"""
prompt.py - Industrial IoT Fault Diagnosis Prompt Templates
Fuses real-time sensor metrics, ML classification probabilities, anomaly deviations,
and retrieved RAG domain knowledge chunks.
"""

from typing import Any, Dict, List, Optional


SYSTEM_DIAGNOSIS_PROMPT = """You are an expert Industrial IoT Diagnostic Assistant specializing in Offshore Oil & Gas Production Wells and Subsea Systems.
Your role is to explain machine learning fault predictions to production engineers and platform operators.

CRITICAL RULES:
1. The ML model prediction is the PRIMARY ground-truth classification. You MUST NOT silently override the ML prediction.
2. If the ML model confidence is below 0.65 (65%), explicitly state that the diagnosis is UNCERTAIN and suggest manual sensor verification.
3. Rely strictly on the provided sensor evidence and retrieved technical knowledge documents. Do NOT fabricate unsafe or non-standard operating procedures.
4. Always follow the EXACT structured format specified by the operator console.
"""


def build_diagnosis_prompt(
    status: str,
    predicted_event: str,
    confidence: float,
    sensor_evidence: List[Dict[str, Any]],
    rag_knowledge_chunks: List[Dict[str, Any]],
    well_id: Optional[str] = "WELL-01",
    binary_status: str = "FAULT",
    class_probabilities: Optional[Dict[str, float]] = None
) -> str:
    """Build formatted prompt for LLM diagnosis generation."""
    
    # Format sensor evidence list
    evidence_lines = []
    for ev in sensor_evidence:
        sensor = ev.get("sensor", "Unknown Sensor")
        val = ev.get("observed_value", "N/A")
        exp = ev.get("expected_behavior", "Nominal range")
        sig = ev.get("significance", "Monitored telemetry parameter")
        evidence_lines.append(f"- Sensor: {sensor} | Observed: {val} | Expected: {exp} | Significance: {sig}")
    
    sensor_text = "\n".join(evidence_lines) if evidence_lines else "- No severe individual sensor threshold breaches detected; multivariate statistical drift identified by ML model."

    # Format retrieved RAG knowledge
    rag_lines = []
    sources_list = []
    for idx, chunk in enumerate(rag_knowledge_chunks, 1):
        doc_name = chunk.get("doc_title") or chunk.get("doc_name", f"Source {idx}")
        sec_title = chunk.get("section_title", "General")
        sources_list.append(f"{doc_name} ({sec_title})")
        rag_lines.append(f"--- KNOWLEDGE EXCERPT {idx} [{doc_name} / {sec_title}] ---\n{chunk.get('content', '').strip()}\n")

    rag_text = "\n".join(rag_lines) if rag_lines else "No specific technical excerpts retrieved."
    sources_text = ", ".join(set(sources_list)) if sources_list else "Internal Oil & Gas System Baseline Rules"

    # Confidence note
    confidence_pct = round(confidence * 100, 1)
    uncertainty_note = ""
    if confidence < 0.65:
        uncertainty_note = "\nWARNING: Model confidence is low (<65%). Emphasize diagnostic uncertainty and recommend immediate manual field validation."

    prompt = f"""Generate a structured fault diagnosis report for offshore well {well_id} based on the following telemetry analysis and technical documentation:

=== ML MODEL PREDICTION ===
Primary Status: {status} ({binary_status})
Detected Event: {predicted_event}
Confidence: {confidence_pct}% ({confidence:.4f}){uncertainty_note}

=== SENSOR TELEMETRY EVIDENCE (60-SECOND WINDOW) ===
{sensor_text}

=== RETRIEVED DOMAIN KNOWLEDGE (RAG) ===
{rag_text}

=== INSTRUCTIONS ===
Produce the response adhering EXACTLY to the following structure and section headings:

FAULT DETECTION
----------------
Status: {status}
Detected Event: {predicted_event}
Confidence: {confidence_pct}% ({'High' if confidence >= 0.8 else 'Moderate' if confidence >= 0.65 else 'Low / Uncertain'})

SENSOR EVIDENCE
----------------
[Detail the key sensor anomalies, their observed values, expected nominal behavior, and physical significance in bullet points]

POSSIBLE CAUSES
----------------
1. [Root cause 1 derived from retrieved knowledge]
2. [Root cause 2]
3. [Root cause 3]

RECOMMENDED CHECKS
----------------
1. [Step 1 standard operator diagnostic check / SOP]
2. [Step 2 check]
3. [Step 3 check]

SAFETY NOTE
----------------
[Critical safety hazards, blowout/overpressure risks, flow assurance hazards, or PPE/operational precautions]

KNOWLEDGE SOURCES
----------------
{sources_text}
"""
    return prompt
