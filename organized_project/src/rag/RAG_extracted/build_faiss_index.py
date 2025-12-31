#!/usr/bin/env python
"""
Build FAISS index from embeddings.npy and save faiss.index + metadata.json into target directory.
"""
import argparse
from pathlib import Path
import numpy as np
import faiss
import json


def build_index(emb_path: Path, metadata_path: Path, out_dir: Path, metric: str = "ip"):
    out_dir.mkdir(parents=True, exist_ok=True)
    emb = np.load(str(emb_path))
    n, dim = emb.shape
    print(f"Loaded embeddings: {emb.shape}")

    if metric == "ip":
        index = faiss.IndexFlatIP(dim)
    else:
        index = faiss.IndexFlatL2(dim)

    index.add(emb.astype("float32"))
    faiss.write_index(index, str(out_dir / "faiss.index"))
    print(f"Wrote FAISS index to {out_dir / 'faiss.index'}")

    # copy metadata
    md = json.load(open(metadata_path, "r", encoding="utf-8"))
    with open(out_dir / "metadata.json", "w", encoding="utf-8") as fh:
        json.dump(md, fh, ensure_ascii=False, indent=2)
    print(f"Wrote metadata to {out_dir / 'metadata.json'}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--embeddings", required=True, help="Path to embeddings.npy")
    p.add_argument("--metadata", required=True, help="Path to metadata.json")
    p.add_argument("--out", required=True, help="Output directory for faiss.index & metadata")
    p.add_argument("--metric", choices=("ip", "l2"), default="ip")
    args = p.parse_args()

    build_index(Path(args.embeddings), Path(args.metadata), Path(args.out), metric=args.metric)


if __name__ == "__main__":
    main()


