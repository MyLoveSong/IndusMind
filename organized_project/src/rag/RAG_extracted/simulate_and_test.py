#!/usr/bin/env python3
"""
simulate_and_test.py

Lightweight RAG extraction simulator and local-model test harness.
This file is a best-effort reconstruction to restore workflow for:
- extracting simple passages (simulated)
- building a small in-memory index (TF-IDF)
- querying the index and calling a local model wrapper
Adjust paths and model call code to match your environment.
"""
import json
import os
from pathlib import Path
from typing import List, Dict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "documents"
INDEX_FILE = BASE / "sim_index.json"


def load_documents(dirpath: Path) -> List[Dict]:
    docs = []
    if not dirpath.exists():
        return docs
    for p in sorted(dirpath.glob("*.txt")):
        docs.append({"id": p.stem, "text": p.read_text(encoding="utf-8")})
    return docs


def build_index(docs: List[Dict]):
    texts = [d["text"] for d in docs]
    vect = TfidfVectorizer(max_features=4096)
    X = vect.fit_transform(texts)
    meta = {"ids": [d["id"] for d in docs], "vocab": vect.get_feature_names_out().tolist()}
    np.savez_compressed(str(INDEX_FILE), data=X.astype(float).toarray())
    with open(str(INDEX_FILE) + ".meta", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Built index for {len(docs)} docs")


def load_index():
    arr_path = str(INDEX_FILE)
    meta_path = arr_path + ".meta"
    if not Path(meta_path).exists():
        return None
    meta = json.load(open(meta_path, "r", encoding="utf-8"))
    data = np.load(arr_path + ".npz")["data"]
    return meta, data


def retrieve(query: str, docs: List[Dict], topk: int = 3):
    # simple TF-IDF retrieval using vectorizer built from docs
    texts = [d["text"] for d in docs]
    vect = TfidfVectorizer(max_features=4096)
    X = vect.fit_transform(texts)
    qv = vect.transform([query])
    sims = cosine_similarity(qv, X)[0]
    idx = np.argsort(sims)[::-1][:topk]
    return [{"id": docs[i]["id"], "text": docs[i]["text"], "score": float(sims[i])} for i in idx]


def call_local_model(prompt: str, context: str = "") -> str:
    """
    Placeholder wrapper to call your local Qwen model.
    Replace this with actual generation call (transformers / qwen sdk).
    """
    # For recovery purposes we return a deterministic mocked answer
    if context:
        return f"(RAG) Based on retrieved evidence: {context[:240]} ...\nAnswer: {prompt}"
    return f"(RAW) Simulated model answer for: {prompt}"


def simulate_run(prompts_path: Path, out_path: Path):
    prompts = json.load(open(prompts_path, "r", encoding="utf-8"))
    docs = load_documents(DATA_DIR)
    results = []
    for i, p in enumerate(prompts):
        q = p.get("prompt") if isinstance(p, dict) else str(p)
        retrieved = retrieve(q, docs, topk=2) if docs else []
        context = "\n\n".join([r["text"] for r in retrieved])
        raw = call_local_model(q, context="")  # before RAG
        rag = call_local_model(q, context=context)  # with RAG
        results.append({"id": i, "prompt": q, "raw": raw, "rag": rag, "retrieved": retrieved})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(results)} results to {out_path}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", default=BASE / "prompts.json", help="json file with prompts (list)")
    ap.add_argument("--out", default=BASE / "simulate_results.json", help="output jsonl")
    args = ap.parse_args()
    simulate_run(Path(args.prompts), Path(args.out))


