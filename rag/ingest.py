"""Load the policy documents and split them into sections (the retrieval corpus).

The corpus is small (a few markdown policies), so it is built in memory on first use
and cached; there is no vector database, model download or index file to maintain.

Check the sections:  python -m rag.ingest
"""
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY_DIR = ROOT / "data" / "policies"


def chunk_markdown(text: str, source: str) -> list[dict]:
    """Split a markdown policy into one chunk per '## ' section."""
    chunks = []
    for part in re.split(r"(?m)^## ", text)[1:]:
        title, _, body = part.partition("\n")
        title, body = title.strip(), body.strip()
        if body:
            chunks.append({"source": source, "section": title, "text": f"{title}\n{body}"})
    return chunks


@lru_cache(maxsize=1)
def load_chunks() -> tuple[dict, ...]:
    """All policy sections from data/policies/*.md (cached for the life of the process)."""
    chunks: list[dict] = []
    for path in sorted(POLICY_DIR.glob("*.md")):
        source = path.stem.replace("_", " ").title()
        chunks += chunk_markdown(path.read_text(encoding="utf-8"), source=source)
    return tuple(chunks)


def ingest() -> int:
    """Reload the policy files (e.g. after editing them). Returns the number of sections."""
    load_chunks.cache_clear()
    return len(load_chunks())


if __name__ == "__main__":
    print(f"Loaded {ingest()} policy sections:")
    for c in load_chunks():
        print(f"  - [{c['source']}] {c['section']}")
