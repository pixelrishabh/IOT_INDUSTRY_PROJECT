"""
retriever.py - Retrieve Relevant Technical Domain Knowledge for Fault Diagnosis
Combines ML predicted event, observed sensor anomalies, and telemetry context
to query the persistent vector store.
"""

from typing import Any, Dict, List, Optional
from rag.vector_store import KnowledgeVectorStore


class FaultKnowledgeRetriever:
    def __init__(self, store_dir: str = "rag/vector_store"):
        self.store = KnowledgeVectorStore(store_dir=store_dir)
        self._initialized = False

    def _ensure_loaded(self):
        if not self._initialized:
            success = self.store.load_store()
            if not success:
                raise RuntimeError(
                    "RAG Vector store not found or empty! Please run 'python rag/ingest.py' first."
                )
            self._initialized = True

    def retrieve_fault_knowledge(
        self,
        predicted_event_id: int,
        predicted_event_name: str,
        sensor_evidence: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve structured technical knowledge corresponding to the predicted fault event
        and observed sensor symptoms.
        """
        self._ensure_loaded()

        # Construct a rich domain query from the predicted event and sensor anomalies
        query_parts = [
            f"Event {predicted_event_id}: {predicted_event_name}",
            "symptoms causes diagnostic checks recommended operator actions safety considerations"
        ]

        if sensor_evidence:
            symptoms_str = " ".join([
                f"{ev.get('sensor', '')} {ev.get('status', '')} {ev.get('significance', '')}"
                for ev in sensor_evidence
            ])
            query_parts.append(symptoms_str)

        query = " ".join(query_parts)
        
        # Search vector store with event filter boost
        results = self.store.search(
            query=query,
            top_k=top_k,
            filter_event=predicted_event_id
        )
        return results

    def retrieve_custom_query(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """General knowledge search for arbitrary operator queries."""
        self._ensure_loaded()
        return self.store.search(query=query, top_k=top_k)
