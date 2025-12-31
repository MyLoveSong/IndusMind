#!/usr/bin/env python
"""
Pipeline for extracting, chunking, and embedding whitepaper PDFs.

Usage example:
    python rag_pipeline/whitepaper_pipeline.py \
        --input-dir "D:/ZJU/RAG/白皮书大礼包" \
        --output-dir "D:/ZJU/RAG/processed/whitepapers" \
        --model "BAAI/bge-large-zh-v1.5"
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import fitz  # PyMuPDF
from tqdm import tqdm

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - dependency optional at import time
    SentenceTransformer = None


YEAR_PATTERN = re.compile(r"(20\d{2})")


@dataclass
class ChunkRecord:
    chunk_id: str
    doc_id: str
    doc_title: str
    doc_year: str
    page_start: int
    page_end: int
    text: str
    char_length: int


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_paragraphs(page_text: str) -> List[str]:
    raw_parts = re.split(r"\n{2,}", page_text)
    return [part.strip() for part in raw_parts if part.strip()]


def slugify(value: str) -> str:
    slug = re.sub(r"[^0-9a-zA-Z]+", "-", value).strip("-").lower()
    return slug or "doc"


def guess_year(name: str) -> str:
    match = YEAR_PATTERN.search(name)
    return match.group(1) if match else "unknown"


def iter_pdf_pages(path: Path) -> Iterable[Tuple[int, str]]:
    doc = fitz.open(path)  # type: ignore[attr-defined]
    for page_no, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        yield page_no, normalize_text(text)


Paragraph = Dict[str, object]


def trim_buffer_for_overlap(buffer: List[Paragraph], overlap_chars: int) -> List[Paragraph]:
    if overlap_chars <= 0 or not buffer:
        return []
    keep: List[Dict[str, str]] = []
    acc_len = 0
    for para in reversed(buffer):
        keep.insert(0, para)
        acc_len += len(str(para["text"]))
        if acc_len >= overlap_chars:
            break
    return keep


def chunk_document_paragraphs(
    paragraphs: Sequence[Paragraph],
    chunk_chars: int,
    overlap_chars: int,
) -> Iterable[Tuple[str, int, int]]:
    buffer: List[Paragraph] = []
    buffer_len = 0

    for para in paragraphs:
        para_text = str(para["text"])
        if not para_text:
            continue
        para_len = len(para_text)
        buffered = buffer_len + para_len
        if buffer and buffered > chunk_chars:
            yield flush_chunk(buffer)
            buffer = trim_buffer_for_overlap(buffer, overlap_chars)
            buffer_len = sum(len(item["text"]) for item in buffer)
        buffer.append(para)
        buffer_len += para_len

    if buffer:
        yield flush_chunk(buffer)


def flush_chunk(buffer: Sequence[Paragraph]) -> Tuple[str, int, int]:
    text = "\n\n".join(str(item["text"]) for item in buffer)
    pages = [int(item["page"]) for item in buffer]
    return text, min(pages), max(pages)


def compute_embeddings(texts: Sequence[str], model_name: str, batch_size: int) -> np.ndarray:
    if SentenceTransformer is not None:
        model = SentenceTransformer(model_name)
        return model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
    # Fallback: TF-IDF dense vectors (not semantic but allows downstream indexing)
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer().fit_transform(texts).toarray().astype("float32")
    return vec


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Whitepaper PDF to chunk/embedding pipeline.")
    parser.add_argument("--input-dir", required=True, help="Directory containing PDF whitepapers.")
    parser.add_argument("--output-dir", required=True, help="Directory to store processed outputs.")
    parser.add_argument("--chunk-chars", type=int, default=900, help="Target characters per chunk.")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Characters to overlap between chunks.")
    parser.add_argument("--max-files", type=int, default=None, help="Optional cap for number of PDFs to process.")
    parser.add_argument("--model", default="BAAI/bge-large-zh-v1.5", help="SentenceTransformer model name.")
    parser.add_argument("--batch-size", type=int, default=32, help="Embedding batch size.")
    parser.add_argument("--skip-embeddings", action="store_true", help="Only export chunks, skip embeddings.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_paths = sorted(input_dir.glob("*.pdf"))
    if args.max_files:
        pdf_paths = pdf_paths[: args.max_files]

    all_chunks: List[ChunkRecord] = []
    empty_pages: Dict[str, List[int]] = {}

    for pdf_path in tqdm(pdf_paths, desc="Processing PDFs"):
        doc_id = slugify(pdf_path.stem)
        doc_title = pdf_path.stem
        doc_year = guess_year(pdf_path.stem)
        paragraphs: List[Dict[str, str]] = []

        for page_no, page_text in iter_pdf_pages(pdf_path):
            if not page_text:
                empty_pages.setdefault(pdf_path.name, []).append(page_no)
                continue
            for para in split_paragraphs(page_text):
                paragraphs.append({"page": page_no, "text": para})

        if not paragraphs:
            continue

        for idx, (chunk_text, page_start, page_end) in enumerate(
            chunk_document_paragraphs(paragraphs, args.chunk_chars, args.chunk_overlap), start=1
        ):
            chunk_id = f"{doc_id}-{idx:04d}"
            all_chunks.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    doc_title=doc_title,
                    doc_year=doc_year,
                    page_start=page_start,
                    page_end=page_end,
                    text=chunk_text,
                    char_length=len(chunk_text),
                )
            )

    if not all_chunks:
        print("No chunks were generated. Check input directory or OCR requirements.")
        return

    chunks_path = output_dir / "whitepaper_chunks.jsonl"
    with chunks_path.open("w", encoding="utf-8") as fh:
        for record in all_chunks:
            fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    embeddings_path = None
    if not args.skip_embeddings:
        texts = [record.text for record in all_chunks]
        embeddings = compute_embeddings(texts, args.model, args.batch_size)
        embeddings_path = output_dir / "whitepaper_embeddings.npy"
        np.save(embeddings_path, embeddings)

    manifest = {
        "source_dir": str(input_dir),
        "total_documents": len(pdf_paths),
        "total_chunks": len(all_chunks),
        "avg_chars_per_chunk": sum(r.char_length for r in all_chunks) / len(all_chunks),
        "chunk_chars": args.chunk_chars,
        "chunk_overlap": args.chunk_overlap,
        "model": None if args.skip_embeddings else args.model,
        "chunks_file": str(chunks_path),
        "embeddings_file": str(embeddings_path) if embeddings_path else None,
        "empty_pages": empty_pages,
    }

    manifest_path = output_dir / "whitepaper_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_chunks)} chunks to {chunks_path}")
    if embeddings_path:
        print(f"Wrote embeddings to {embeddings_path}")
    print(f"Manifest stored at {manifest_path}")


if __name__ == "__main__":
    main()

