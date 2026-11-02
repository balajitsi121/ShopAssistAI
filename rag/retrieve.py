"""Keyword (BM25) search over the policy sections.

Pure Python: no embedding model, vector database or network access, so it behaves the same
locally, in tests and on Render. Light stemming and a small synonym map let everyday wording
("money back", "how long", "send back") match the policy's terms.

Try it:  python -m rag.retrieve "How long do refunds take?"
"""
import math
import re
import sys
from collections import Counter

from rag.ingest import load_chunks

K1, B = 1.5, 0.75  # standard BM25 parameters

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for", "from", "get",
    "how", "i", "if", "in", "is", "it", "my", "of", "on", "or", "the", "this", "to", "what",
    "when", "will", "with", "you", "your",
}

# Customer wording -> policy wording (applied to queries only).
SYNONYMS = {
    "money": ["refund"], "reimburse": ["refund"], "repay": ["refund"], "back": ["refund", "return"],
    "long": ["window", "day"], "days": ["day", "window"], "deadline": ["window", "day"],
    "late": ["window", "day"], "time": ["window", "day"], "period": ["window"],
    "send": ["return"], "exchange": ["return"],
    "start": ["contact", "support"], "begin": ["start", "contact"], "initiate": ["start", "contact"],
    "used": ["unused"], "opened": ["original", "packaging"], "box": ["packaging"],
    "sale": ["final"], "clearance": ["final", "sale"], "eligible": ["eligibility"],
    "card": ["payment", "method"], "inspect": ["inspected"],
}


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def tokenize(text: str) -> list[str]:
    return [_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]


SYNONYM_WEIGHT = 0.5  # synonyms help recall but count less than the customer's own words


def _expand(query: str) -> dict[str, float]:
    """Query terms with weights: 1.0 for the customer's words, SYNONYM_WEIGHT for synonyms."""
    words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if w not in STOPWORDS]
    terms: dict[str, float] = {}
    for w in words:
        for syn in SYNONYMS.get(w, []):
            terms.setdefault(_stem(syn), SYNONYM_WEIGHT)
    for w in words:
        terms[_stem(w)] = 1.0
    return terms


def search_policy(query: str, k: int = 2) -> list[dict]:
    """Return the top-k policy passages: [{source, section, text, score}], best first.

    Always returns up to k passages (the model is told to answer only from them),
    falling back to document order when nothing matches.
    """
    chunks = load_chunks()
    if not chunks:
        return []
    docs = [Counter(tokenize(c["text"])) for c in chunks]
    lengths = [sum(d.values()) for d in docs]
    avg_len = sum(lengths) / len(lengths)
    n = len(docs)
    terms = _expand(query)

    scores = []
    for doc, length in zip(docs, lengths):
        score = 0.0
        for term, weight in terms.items():
            tf = doc.get(term, 0)
            if tf:
                df = sum(1 for d in docs if term in d)
                idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                score += weight * idf * tf * (K1 + 1) / (tf + K1 * (1 - B + B * length / avg_len))
        scores.append(score)

    ranked = sorted(range(n), key=lambda i: (-scores[i], i))[:k]
    return [{**chunks[i], "score": round(scores[i], 3)} for i in ranked]


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "How long do refunds take?"
    for hit in search_policy(question):
        print(f"[{hit['source']} - {hit['section']}] (score {hit['score']:.3f})")
        print(hit["text"], "\n")
