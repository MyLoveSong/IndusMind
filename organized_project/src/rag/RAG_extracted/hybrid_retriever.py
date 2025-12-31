#!/usr/bin/env python
"""
Hybrid retriever: FAISS vector search + lexical TF-IDF fallback and merging.
Provides a simple interface compatible with existing RAGSystem.search usage.
"""
from typing import List, Dict, Optional
import json
from pathlib import Path
import numpy as np
import faiss

try:
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except Exception:
    SentenceTransformer = None  # type: ignore
    _HAS_ST = False

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class HybridRetriever:
    def __init__(self, index_path: str, metadata_path: str, encoder_model: str = "BAAI/bge-large-zh-v1.5"):
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        # load metadata
        with open(self.metadata_path / "metadata.json", "r", encoding="utf-8") as fh:
            self.metadata = json.load(fh)

        # load FAISS index (CPU for safety; caller handles GPU conversion if desired)
        self.index = faiss.read_index(str(self.index_path / "faiss.index"))

        # prepare TF-IDF vectorizer fitted on chunk texts for lexical fallback
        texts = [c["text"] for c in self.metadata.get("chunks", [])]
        if texts:
            self.tfidf = TfidfVectorizer().fit(texts)
            self._tfidf_matrix = self.tfidf.transform(texts)
        else:
            self.tfidf = None
            self._tfidf_matrix = None

        # optionally load sentence-transformers model for semantic embeddings
        self.encoder_model_name = encoder_model
        self._st_model: Optional[SentenceTransformer] = None
        if _HAS_ST:
            try:
                self._st_model = SentenceTransformer(self.encoder_model_name)
            except Exception:
                self._st_model = None

    def encode_query(self, query: str) -> np.ndarray:
        """Return a vector usable for FAISS search; prefer sentence-transformers."""
        if self._st_model:
            vec = self._st_model.encode([query], normalize_embeddings=True)[0].astype("float32")
            return vec
        # fallback to TF-IDF dense vector
        if self.tfidf is not None:
            v = self.tfidf.transform([query]).toarray().astype("float32")[0]
            return v
        raise RuntimeError("No embedding or TF-IDF available for query encoding.")

    def faiss_search(self, query_vec: np.ndarray, k: int = 5):
        qv = query_vec.reshape(1, -1).astype("float32")
        try:
            distances, indices = self.index.search(qv, k)
        except Exception:
            # fallback: return empty
            return []
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < 0:
                continue
            chunk = self.metadata["chunks"][idx]
            results.append({"idx": idx, "text": chunk["text"], "score": float(dist)})
        return results

    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """Encode a list of texts using sentence-transformers if available, else TF-IDF dense vectors."""
        if self._st_model:
            embs = self._st_model.encode(texts, normalize_embeddings=True)
            return embs.astype("float32")
        if self.tfidf is not None:
            mat = self.tfidf.transform(texts).toarray().astype("float32")
            return mat
        raise RuntimeError("No encoder available to encode texts.")

    def lexical_search(self, query: str, k: int = 20):
        if self.tfidf is None or self._tfidf_matrix is None:
            return []
        qv = self.tfidf.transform([query])
        sims = cosine_similarity(qv, self._tfidf_matrix)[0]
        topk_idx = np.argsort(-sims)[:k]
        results = []
        for idx in topk_idx:
            chunk = self.metadata["chunks"][int(idx)]
            results.append({"idx": int(idx), "text": chunk["text"], "score": float(sims[int(idx)])})
        return results

    def hybrid_search(self, query: str, k: int = 5, alpha: float = 0.6, faiss_k: int = 50, lex_k: int = 50):
        """Hybrid search merging FAISS and lexical candidates.
        alpha: weight for semantic (faiss) score when combining; (1-alpha) for lexical.
        """
        qvec = self.encode_query(query)
        faiss_cands = self.faiss_search(qvec, k=faiss_k)
        lex_cands = self.lexical_search(query, k=lex_k)

        # combine by idx, normalize scores
        scores = {}
        for i, c in enumerate(faiss_cands):
            scores[c["idx"]] = {"sem": float(c["score"]), "lex": 0.0}
        for c in lex_cands:
            if c["idx"] in scores:
                scores[c["idx"]]["lex"] = float(c["score"])
            else:
                scores[c["idx"]] = {"sem": 0.0, "lex": float(c["score"])}

        combined = []
        for idx, sc in scores.items():
            sem = sc["sem"]
            lex = sc["lex"]
            # simple normalization: use raw values (FAISS may be distance); prefer higher
            combined_score = alpha * float(sem) + (1.0 - alpha) * float(lex)
            chunk = self.metadata["chunks"][int(idx)]
            combined.append({"idx": int(idx), "text": chunk["text"], "score": float(combined_score)})

        combined_sorted = sorted(combined, key=lambda x: x["score"], reverse=True)
        return combined_sorted[:k]


