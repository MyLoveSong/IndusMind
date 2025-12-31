#!/usr/bin/env python3
"""
Run full deterministic generation (Qwen) over eval JSONL and evaluate.
Saves predictions to --out and runs evaluate_semantic_normalized.py to produce a report.
"""
import sys
from pathlib import Path
import json
import argparse
from time import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

def load_examples(path):
    exs = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            exs.append(json.loads(line))
    return exs

def extract_query(example):
    return example.get("input") or example.get("instruction") or example.get("question") or example.get("prompt") or example.get("query") or example.get("generation") or ""

def extract_ref(example):
    return example.get("label") or example.get("reference") or example.get("target") or example.get("answer") or ""

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model_path", required=True)
    p.add_argument("--index_path", default="./models/faiss")
    p.add_argument("--metadata_path", default="./models/faiss")
    p.add_argument("--input", required=True)
    p.add_argument("--out", default="./finetune/generation_results.jsonl")
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--max_examples", type=int, default=None)
    p.add_argument("--max_new_tokens", type=int, default=None, help="Explicit max_new_tokens for generation")
    args = p.parse_args()

    # lazy import RAGSystem
    from rag_service import RAGSystem

    print("Initializing RAGSystem (this will load the large model)...")
    rag = RAGSystem(
        model_path=args.model_path,
        index_path=args.index_path,
        metadata_path=args.metadata_path,
        use_gpu=True,
        use_reranker=False
    )

    examples = load_examples(args.input)
    if args.max_examples:
        examples = examples[: args.max_examples]

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    start = time()
    with outp.open("w", encoding="utf-8") as fh:
        for i, ex in enumerate(examples, 1):
            query = extract_query(ex)
            ref = extract_ref(ex)
            if not query:
                pred = ""
            else:
                try:
                    res = rag.query(query, k=args.k, deterministic=True, max_new_tokens=args.max_new_tokens)
                    pred = res.get("answer", "")
                except Exception as e:
                    pred = ""
                    print(f"[{i}] generation error: {e}")
            out = {"prediction": pred, "label": ref, "raw": ex}
            fh.write(json.dumps(out, ensure_ascii=False) + "\n")
            if i % 10 == 0:
                elapsed = time() - start
                print(f"Processed {i}/{len(examples)} in {elapsed:.1f}s")

    print("Generation complete. Running evaluation script...")
    eval_cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent.parent / "evaluate_semantic_normalized.py"),
        "--input", str(outp),
        "--pred-keys", "prediction",
        "--ref-keys", "label",
        "--output", str(outp.parent / "generation_eval_report.json"),
        "--mismatch-output", str(outp.parent / "generation_mismatches.jsonl"),
        "--top-k", "200"
    ]
    import subprocess
    r = subprocess.run(eval_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print("Evaluation failed:", r.stderr)
        raise SystemExit(1)
    print("Evaluation finished. Report and mismatches written.")

if __name__ == "__main__":
    main()


