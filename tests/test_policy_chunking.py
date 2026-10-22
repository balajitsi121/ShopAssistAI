from pathlib import Path

from rag.ingest import POLICY_DIR, chunk_markdown


def test_splits_into_sections():
    text = "# Title\n\n## 1. One\nAlpha\n\n## 2. Two\nBeta\n"
    chunks = chunk_markdown(text, source="Test")
    assert [c["section"] for c in chunks] == ["1. One", "2. Two"]
    assert "Alpha" in chunks[0]["text"]


def test_real_policy_has_four_sections():
    path = Path(POLICY_DIR) / "return_policy.md"
    chunks = chunk_markdown(path.read_text(encoding="utf-8"), source="Return Policy")
    assert len(chunks) == 4
    assert any("Refund procedure" in c["section"] for c in chunks)
