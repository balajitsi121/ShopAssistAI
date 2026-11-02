"""Policy search runs fully offline (no embedding model or vector DB)."""
import pytest

from agent.tool_registry import run_tool
from rag.retrieve import search_policy


@pytest.mark.parametrize(
    "question, expected_section",
    [
        ("How long do refunds take?", "4. Refund procedure"),
        ("How many days do I have to return something?", "2. Return window"),
        ("How do I start a return?", "3. How to start a return"),
        ("Can I return an opened item?", "1. Eligibility"),
        ("When will my refund arrive on my card?", "4. Refund procedure"),
    ],
)
def test_top_hit_is_relevant_section(question, expected_section):
    assert search_policy(question)[0]["section"] == expected_section


def test_returns_k_passages_with_metadata():
    hits = search_policy("final sale", k=3)
    assert len(hits) == 3
    assert hits[0]["section"] == "1. Eligibility"
    assert {"source", "section", "text", "score"} <= hits[0].keys()
    assert hits[0]["source"] == "Return Policy"


def test_unrelated_query_still_returns_passages():
    assert len(search_policy("what is the weather")) == 2


def test_search_policy_tool_end_to_end():
    result, trace = run_tool("search_policy", '{"query": "refund timing"}')
    assert "Refund procedure" in result
    assert trace["sources"][0]["section"] == "4. Refund procedure"
