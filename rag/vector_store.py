"""
vector_store.py - Lightweight, CPU-Friendly Persistent Vector Store for RAG
Uses TF-IDF + BM25-style sublinear term weighting with cosine similarity vector scoring.
Ensures 100% offline CPU execution with zero external GPU/Torch requirements,
ideal for fast edge/laptop deployment in B.Tech IoT projects.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class KnowledgeVectorStore:
    def __init__(self, store_dir: str = "rag/vector_store"):
        self.store_dir = Path(store_dir)
        self.vectorizer_path = self.store_dir / "tfidf_vectorizer.joblib"
        self.matrix_path = self.store_dir / "doc_matrix.joblib"
        self.chunks_path = self.store_dir / "chunks.json"

        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_matrix: Optional[np.ndarray] = None
        self.chunks: List[Dict[str, Any]] = []

    def build_store(self, chunks: List[Dict[str, Any]]) -> None:
        """Build and persist the vector store from document chunks."""
        self.chunks = chunks
        corpus = [c["content"] for c in chunks]

        # Use unigram + bigram TF-IDF with sublinear tf scaling
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
            stop_words="english"
        )
        self.doc_matrix = self.vectorizer.fit_transform(corpus)

        self.store_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.vectorizer, self.vectorizer_path)
        joblib.dump(self.doc_matrix, self.matrix_path)
        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)

        print(f"Knowledge Vector Store built: {len(self.chunks)} chunks indexed across {self.doc_matrix.shape[1]} vocabulary terms.")

    def load_store(self) -> bool:
        """Load persisted vector store from disk."""
        if not (self.vectorizer_path.exists() and self.matrix_path.exists() and self.chunks_path.exists()):
            return False

        self.vectorizer = joblib.load(self.vectorizer_path)
        self.doc_matrix = joblib.load(self.matrix_path)
        with open(self.chunks_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
        return True

    def search(self, query: str, top_k: int = 4, filter_event: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query the vector store and return top_k matching chunks with similarity scores.
        Optionally filter or boost by event_id.
        """
        if self.vectorizer is None or self.doc_matrix is None:
            if not self.load_store():
                raise RuntimeError("Vector store not initialized! Run rag/ingest.py first.")

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.doc_matrix).flatten()

        results = []
        for idx, score in enumerate(similarities):
            chunk = self.chunks[idx].copy()
            # Boost score if chunk matches target event id
            if filter_event is not None and chunk.get("event_id") == filter_event:
                score = score * 1.5 + 0.3
            chunk["score"] = float(score)
            results.append(chunk)

        # Sort descending by score
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:top_k]
