"""Load the return policy, split it into sections and index them in ChromaDB.

Run once (or after editing the policy):  python -m rag.ingest
"""
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
POLICY_DIR = ROOT / "data" / "policies"
COLLECTION = "return_policy"


def chunk_markdown(text: str, source: str) -> list[dict]:
    """Split a markdown policy into one chunk per '## ' section."""
    chunks = []
    for part in re.split(r"(?m)^## ", text)[1:]:
        title, _, body = part.partition("\n")
        title, body = title.strip(), body.strip()
        if body:
            chunks.append({"source": source, "section": title, "text": f"{title}\n{body}"})
    return chunks


def get_embedding_function():
    """Sentence Transformers if installed, otherwise Chroma's built-in MiniLM."""
    from chromadb.utils import embedding_functions

    model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    try:
        return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)
    except Exception:
        return embedding_functions.DefaultEmbeddingFunction()


def get_client():
    import chromadb

    return chromadb.PersistentClient(path=str(ROOT / os.getenv("CHROMA_PATH", "chroma_db")))


def ingest() -> int:
    """(Re)build the policy index. Returns the number of chunks stored."""
    chunks = []
    for path in sorted(POLICY_DIR.glob("*.md")):
        chunks += chunk_markdown(path.read_text(encoding="utf-8"), source=path.stem.replace("_", " ").title())

    client = get_client()
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass  # collection did not exist yet
    collection = client.create_collection(COLLECTION, embedding_function=get_embedding_function())
    collection.add(
        ids=[f"{c['source']}-{i}" for i, c in enumerate(chunks)],
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["source"], "section": c["section"]} for c in chunks],
    )
    return len(chunks)


if __name__ == "__main__":
    print(f"Indexed {ingest()} policy sections.")
