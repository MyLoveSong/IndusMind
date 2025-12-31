#!/usr/bin/env python3
"""
Evaluate predictions vs references with:
- normalized Exact Match (lowercase, strip punctuation/extra spaces)
- ROUGE-L (F1)
- sacreBLEU (corpus BLEU)
- SentenceTransformer mean cosine similarity (per-example + mean)

Saves a JSON report and a JSONL file of top mismatches (norm mismatch but high/low cosine).
"""
from pathlib import Path
import argparse
import json
import re
from typing import List, Tuple

import numpy as np
from tqdm import tqdm
from rouge_score import rouge_scorer
import sacrebleu
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

NORMALIZE_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)

def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).lower().strip()
    s = NORMALIZE_RE.sub("", s)
    s = re.sub(r"\s+", " ", s)
    return s

def extract_field(obj: dict, keys: List[str]):
    for k in keys:
        if k in obj:
            return obj[k]
    return None

def load_jsonl(path: Path, pred_keys: List[str], ref_keys: List[str]) -> Tuple[List[str], List[str], List[dict]]:
    preds = []
    refs = []
    raws = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            j = json.loads(line)
            p = extract_field(j, pred_keys)
            r = extract_field(j, ref_keys)
            if isinstance(p, list):
                p = p[0] if p else ""
            if isinstance(r, list):
                r = r[0] if r else ""
            preds.append("" if p is None else str(p))
            refs.append("" if r is None else str(r))
            raws.append(j)
    return preds, refs, raws

def compute_metrics(preds: List[str], refs: List[str], model_name="all-MiniLM-L6-v2", batch_size=128):
    n = len(preds)
    norm_preds = [normalize_text(p) for p in preds]
    norm_refs = [normalize_text(r) for r in refs]
    em_flags = [1 if a == b and a != "" else 0 for a,b in zip(norm_preds, norm_refs)]
    normalized_em = float(sum(em_flags)) / n if n else 0.0

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    rouge_fs = []
    for p, r in zip(preds, refs):
        score = scorer.score(r, p)["rougeL"].fmeasure
        rouge_fs.append(score)
    mean_rouge_l = float(np.mean(rouge_fs)) if rouge_fs else 0.0

    bleu = sacrebleu.corpus_bleu(preds, [refs])
    bleu_score = float(bleu.score)

    # Try to use SentenceTransformer for semantic embeddings; if unavailable or importing it fails
    # (common when torch/torchvision versions mismatch), fall back to TF-IDF vectors.
    all_texts = preds + refs
    pred_emb = None
    ref_emb = None
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        embeddings = model.encode(all_texts, batch_size=batch_size, show_progress_bar=True)
        pred_emb = embeddings[:n]
        ref_emb = embeddings[n:]
        used_embedding = f"sentence-transformers:{model_name}"
    except Exception:
        # Fallback: TF-IDF (not semantic but robust)
        vectorizer = TfidfVectorizer().fit(all_texts)
        all_vecs = vectorizer.transform(all_texts).toarray()
        pred_emb = all_vecs[:n]
        ref_emb = all_vecs[n:]
        used_embedding = "tfidf:fallback"

    sims = []
    for i in range(n):
        a = pred_emb[i].reshape(1, -1)
        b = ref_emb[i].reshape(1, -1)
        sims.append(float(cosine_similarity(a, b)[0][0]))
    mean_cosine = float(np.mean(sims)) if sims else 0.0

    return {
        "used_embedding": used_embedding,
        "n": n,
        "normalized_em": normalized_em,
        "normalized_em_count": int(sum(em_flags)),
        "mean_rouge_l": mean_rouge_l,
        "bleu": bleu_score,
        "mean_cosine": mean_cosine,
        "per_example_sims": sims,
        "norm_preds": norm_preds,
        "norm_refs": norm_refs,
        "em_flags": em_flags,
    }

def make_mismatch_list(preds, refs, raws, metrics, top_k=100):
    n = metrics["n"]
    mismatches = []
    for i in range(n):
        if metrics["norm_preds"][i] != metrics["norm_refs"][i]:
            mismatches.append({
                "idx": i,
                "prediction": preds[i],
                "reference": refs[i],
                "norm_prediction": metrics["norm_preds"][i],
                "norm_reference": metrics["norm_refs"][i],
                "cosine": metrics["per_example_sims"][i],
                "raw": raws[i],
            })
    # sort by cosine descending (high-semantic similarity but surface mismatch) and return top_k
    mismatches_sorted = sorted(mismatches, key=lambda x: x["cosine"], reverse=True)
    return mismatches_sorted[:top_k]

def save_report(report: dict, path: Path):
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

def save_mismatches(mismatches: List[dict], path: Path):
    with path.open("w", encoding="utf-8") as f:
        for m in mismatches:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

def parse_comma_keys(s: str):
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", required=True, help="Path to eval JSONL (one JSON per line)")
    p.add_argument("--pred-keys", default="prediction,pred", help="Comma-separated candidate keys to search for prediction")
    p.add_argument("--ref-keys", default="label,reference,ref", help="Comma-separated candidate keys to search for reference")
    p.add_argument("--model", default="all-MiniLM-L6-v2", help="SentenceTransformer model name")
    p.add_argument("--batch-size", type=int, default=128)
    p.add_argument("--output", "-o", default="eval_report.json", help="JSON report path")
    p.add_argument("--mismatch-output", default="mismatches.jsonl", help="JSONL of mismatches")
    p.add_argument("--top-k", type=int, default=200, help="Max mismatches to save")
    args = p.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        raise SystemExit(f"Input file not found: {inp}")

    pred_keys = parse_comma_keys(args.pred_keys)
    ref_keys = parse_comma_keys(args.ref_keys)
    preds, refs, raws = load_jsonl(inp, pred_keys, ref_keys)

    metrics = compute_metrics(preds, refs, model_name=args.model, batch_size=args.batch_size)

    mismatches = make_mismatch_list(preds, refs, raws, metrics, top_k=args.top_k)

    report = {
        "input_path": str(inp),
        "n_examples": metrics["n"],
        "normalized_em": metrics["normalized_em"],
        "normalized_em_count": metrics["normalized_em_count"],
        "mean_rouge_l": metrics["mean_rouge_l"],
        "bleu": metrics["bleu"],
        "mean_cosine": metrics["mean_cosine"],
        "mismatches_saved": len(mismatches),
    }

    save_report(report, Path(args.output))
    save_mismatches(mismatches, Path(args.mismatch_output))

    print(f"Report saved to {args.output}")
    print(f"Mismatches saved to {args.mismatch_output} ({len(mismatches)} entries)")
    # also print short metrics
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()


