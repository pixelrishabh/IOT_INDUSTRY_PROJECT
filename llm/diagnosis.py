"""
diagnosis.py - End-to-End Fault Diagnosis Synthesizer
Combines ML inference, RAG domain retrieval, and LLM reasoning into structured reports.
"""

from typing import Any, Dict, List, Optional
from llm.client import LLMClient
from llm.prompt import SYSTEM_DIAGNOSIS_PROMPT, build_diagnosis_prompt
from rag.retriever import FaultKnowledgeRetriever


class DiagnosisEngine:
    def __init__(
        self,
        retriever: Optional[FaultKnowledgeRetriever] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.retriever = retriever or FaultKnowledgeRetriever()
        self.llm_client = llm_client or LLMClient()

    def generate_diagnosis(
        self,
        status: str,
        predicted_event_id: int,
        predicted_event_name: str,
        confidence: float,
        sensor_evidence: List[Dict[str, Any]],
        well_id: str = "WELL-01",
        binary_status: str = "FAULT",
        class_probabilities: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive, structured fault diagnosis.
        """
        # 1. Retrieve relevant technical documents via RAG
        rag_chunks = []
        try:
            rag_chunks = self.retriever.retrieve_fault_knowledge(
                predicted_event_id=predicted_event_id,
                predicted_event_name=predicted_event_name,
                sensor_evidence=sensor_evidence,
                top_k=3
            )
        except Exception as e:
            print(f"[DiagnosisEngine] Warning during RAG retrieval: {e}")

        # 2. Build diagnosis prompt
        prompt = build_diagnosis_prompt(
            status=status,
            predicted_event=predicted_event_name,
            confidence=confidence,
            sensor_evidence=sensor_evidence,
            rag_knowledge_chunks=rag_chunks,
            well_id=well_id,
            binary_status=binary_status,
            class_probabilities=class_probabilities
        )

        # 3. Generate structured diagnosis text via LLM
        raw_diagnosis = self.llm_client.generate_diagnosis(
            prompt=prompt,
            system_instruction=SYSTEM_DIAGNOSIS_PROMPT
        )

        # 4. If using fallback synthesis, enrich template with RAG excerpts
        if "Expert System Synthesizer" in raw_diagnosis or not raw_diagnosis.strip():
            raw_diagnosis = self._format_deterministic_report(
                status=status,
                predicted_event=predicted_event_name,
                confidence=confidence,
                sensor_evidence=sensor_evidence,
                rag_chunks=rag_chunks
            )

        return {
            "status": status,
            "predicted_event_id": predicted_event_id,
            "predicted_event": predicted_event_name,
            "confidence": round(confidence, 4),
            "binary_status": binary_status,
            "raw_diagnosis": raw_diagnosis,
            "retrieved_sources": [
                c.get("doc_title") or c.get("doc_name", "") for c in rag_chunks
            ],
            "rag_chunks": rag_chunks
        }

    def _format_deterministic_report(
        self,
        status: str,
        predicted_event: str,
        confidence: float,
        sensor_evidence: List[Dict[str, Any]],
        rag_chunks: List[Dict[str, Any]]
    ) -> str:
        """Deterministic offline formatter matching exact required structure."""
        conf_label = "High" if confidence >= 0.8 else "Moderate" if confidence >= 0.65 else "Low / Uncertain"
        conf_str = f"{round(confidence * 100, 1)}% ({conf_label})"
        
        evidence_lines = []
        for ev in sensor_evidence:
            evidence_lines.append(
                f"- Sensor: {ev.get('sensor', 'N/A')}\n"
                f"  Observed Value: {ev.get('observed_value', 'N/A')}\n"
                f"  Expected Behavior: {ev.get('expected_behavior', 'Nominal Envelope')}\n"
                f"  Significance: {ev.get('significance', 'Monitored Parameter')}"
            )
        evidence_text = "\n".join(evidence_lines) if evidence_lines else "- Monitored sensor trends within operational bounds; multivariate statistical divergence detected."

        # Extract causes and checks from RAG chunks if available
        causes = [
            "Downhole hydraulic or multiphase thermodynamic transition.",
            "Subsea valve / choke trim restriction or mechanical deviation.",
            "Reservoir inflow condition shift or fluid density alteration."
        ]
        checks = [
            "Verify real-time pressure differential across production choke and downhole gauge.",
            "Cross-check gas lift injection rate and annulus pressure stability.",
            "Sample topside separator water-cut and review emergency shutdown interlocks."
        ]
        safety = "Maintain continuous monitoring of high-pressure trip alarms. Verify subsea valve hydraulic accumulator margins."
        sources = ", ".join(set([c.get("doc_title") or c.get("doc_name", "Technical Guide") for c in rag_chunks])) or "Petrobras 3W Domain Standards"

        # If RAG chunk contains specific sections, extract them
        for chunk in rag_chunks:
            content = chunk.get("content", "")
            if "Possible Root Causes" in content or "Root Causes" in content:
                extracted = [line.strip() for line in content.split("\n") if line.strip().startswith(("1.", "2.", "3."))]
                if extracted:
                    causes = extracted[:3]
            if "Recommended Operator Actions" in content or "Operator Actions" in content:
                extracted = [line.strip() for line in content.split("\n") if line.strip().startswith(("1.", "2.", "3.", "-"))]
                if extracted:
                    checks = [c.lstrip("- ") for c in extracted[:3]]
            if "Critical Safety Considerations" in content or "Safety Considerations" in content:
                extracted = [line.strip() for line in content.split("\n") if len(line.strip()) > 30 and not line.startswith("#")]
                if extracted:
                    safety = " ".join(extracted[:2])

        return f"""FAULT DETECTION
----------------
Status: {status}
Detected Event: {predicted_event}
Confidence: {conf_str}

SENSOR EVIDENCE
----------------
{evidence_text}

POSSIBLE CAUSES
----------------
1. {causes[0] if len(causes)>0 else 'Primary reservoir / hydraulic transition'}
2. {causes[1] if len(causes)>1 else 'Mechanical choke / valve trim deviation'}
3. {causes[2] if len(causes)>2 else 'Fluid property / flow assurance change'}

RECOMMENDED CHECKS
----------------
1. {checks[0] if len(checks)>0 else 'Inspect choke differential pressure and telemetry trends'}
2. {checks[1] if len(checks)>1 else 'Verify gas lift flow rate and separator inflow stability'}
3. {checks[2] if len(checks)>2 else 'Confirm ESD interlocks and verify subsea hydraulic lines'}

SAFETY NOTE
----------------
{safety}

KNOWLEDGE SOURCES
----------------
{sources}
"""
