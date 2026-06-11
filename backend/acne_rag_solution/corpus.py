from __future__ import annotations

import json
from pathlib import Path

from .models import EvidenceChunk

COMMERCIAL_ALLOWED_USES = {"commercial_allowed", "public_domain", "cc0", "cc_by"}


def default_corpus_path() -> Path:
    return Path(__file__).with_name("evidence_corpus.json")


def load_corpus(path: Path | None = None) -> list[EvidenceChunk]:
    corpus_path = path or default_corpus_path()
    with corpus_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError("evidence corpus must be a JSON list")
    chunks = [EvidenceChunk.from_dict(item) for item in payload]
    ids = [chunk.id for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("evidence corpus has duplicate ids")
    return chunks


def generation_allowed(chunk: EvidenceChunk) -> bool:
    return chunk.allowed_use in COMMERCIAL_ALLOWED_USES
