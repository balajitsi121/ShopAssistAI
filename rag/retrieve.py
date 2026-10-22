"""Semantic search over the indexed return policy.

Try it:  python -m rag.retrieve "How long do refunds take?"
"""
import sys

from rag.ingest import COLLECTION, get_client, get_embedding_function, ingest


def _get_collection():
    client = get_client()
    try:
        collection = client.get_collection(COLLECTION, embedding_function=get_embedding_function())
        if collection.count() > 0:
            return collection
    except Exception:
        pass
    ingest()  # first run: build the index automatically
    return client.get_collection(COLLECTION, embedding_function=get_embedding_function())


def search_policy(query: str, k: int = 2) -> list[dict]:
    """Return the top-k policy passages: [{source, section, text, distance}]."""
    result = _get_collection().query(query_texts=[query], n_results=k)
    return [
        {"source": meta["source"], "section": meta["section"], "text": doc, "distance": dist}
        for doc, meta, dist in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        )
    ]


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "How long do refunds take?"
    for hit in search_policy(question):
        print(f"[{hit['source']} - {hit['section']}] (distance {hit['distance']:.3f})")
        print(hit["text"], "\n")
