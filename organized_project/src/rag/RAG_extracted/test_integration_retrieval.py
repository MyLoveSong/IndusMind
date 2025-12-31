#!/usr/bin/env python3
"""
Integration test: retrieval-only pipeline using HybridRetriever.
Reads first N examples from finetune/eval_full_results.jsonl, retrieves top-1 chunk as 'prediction',
and evaluates using evaluate_semantic_normalized.py.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # ensure RAG_extracted package path
from hybrid_retriever import HybridRetriever
import argparse
from subprocess import run, PIPE


def load_examples(path, n=100):
    examples = []
    with open(path, "r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i >= n:
                break
            if not line.strip():
                continue
            examples.append(json.loads(line))
    return examples


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--index_path", default="./models/faiss")
    p.add_argument("--metadata_path", default="./models/faiss")
    p.add_argument("--out", default="./finetune/integration_results.jsonl")
    p.add_argument("--n", type=int, default=100)
    args = p.parse_args()

    inpath = Path(args.input)
    outpath = Path(args.out)
    retriever = HybridRetriever(args.index_path, args.metadata_path)

    exs = load_examples(inpath, n=args.n)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with outpath.open("w", encoding="utf-8") as fh:
        for ex in exs:
            query = ex.get("input", ex.get("question", ex.get("prompt", "")))
            if not query:
                query = ex.get("query", "")
            try:
                cands = retriever.hybrid_search(query, k=1)
                pred = cands[0]["text"] if cands else ""
            except Exception as e:
                pred = ""
            ref = ex.get("label") or ex.get("reference") or ex.get("target") or ex.get("answer") or ""
            out = {"prediction": pred, "label": ref, "raw": ex}
            fh.write(json.dumps(out, ensure_ascii=False) + "\n")

    # run evaluation script
    cmd = [
        "python", str(Path(__file__).parent.parent / "evaluate_semantic_normalized.py"),
        "--input", str(outpath),
        "--pred-keys", "prediction",
        "--ref-keys", "label",
        "--output", str(outpath.parent / "integration_eval_report.json"),
        "--mismatch-output", str(outpath.parent / "integration_mismatches.jsonl"),
        "--top-k", "200"
    ]
    print("Running evaluation:", " ".join(cmd))
    r = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print("Evaluation failed:", r.stderr)


if __name__ == "__main__":
    main()


