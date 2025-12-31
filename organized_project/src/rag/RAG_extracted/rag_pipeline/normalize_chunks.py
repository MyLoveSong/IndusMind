#!/usr/bin/env python
"""
Normalize chunk jsonl files into a metadata.json compatible format:
{
  "chunks": [
    {"text": "...", "file_name": "...", "page": 1, "chunk_index": 0, ...},
    ...
  ]
}
"""
import argparse
import json
from pathlib import Path


def normalize(input_jsonl: Path, output_metadata: Path):
    chunks = []
    with input_jsonl.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            obj = json.loads(line)
            # map common fields
            text = obj.get("text") or obj.get("chunk_text") or obj.get("content") or ""
            file_name = obj.get("doc_title") or obj.get("file_name") or obj.get("doc_id") or "unknown"
            page = obj.get("page_start") or obj.get("page") or obj.get("page_start", -1)
            chunk_index = obj.get("chunk_index") or obj.get("chunk_id") or None
            chunks.append({
                "text": text,
                "file_name": file_name,
                "page": page,
                "chunk_index": chunk_index
            })
    meta = {"chunks": chunks, "source": str(input_jsonl)}
    output_metadata.parent.mkdir(parents=True, exist_ok=True)
    with output_metadata.open("w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print(f"Wrote metadata with {len(chunks)} chunks to {output_metadata}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Input chunks jsonl")
    p.add_argument("--output", required=True, help="Output metadata.json")
    args = p.parse_args()
    normalize(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()


