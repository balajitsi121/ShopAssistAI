from types import SimpleNamespace

import pytest

pytest.importorskip("langgraph")

from agent.agent import run_agent


def _reply(content=None, tool_calls=None):
    msg = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def _tool_call(name, arguments):
    return SimpleNamespace(id="call_1", function=SimpleNamespace(name=name, arguments=arguments))


class FakeClient:
    """Pretends to be the OpenAI client: first asks for a tool, then answers."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return self.replies.pop(0)


def test_agent_calls_tool_then_answers():
    client = FakeClient([
        _reply(tool_calls=[_tool_call("get_order_details", '{"order_id": "ORD-1001"}')]),
        _reply(content="Your desk lamp has shipped."),
    ])
    result = run_agent([], "Where is ORD-1001?", client=client, model="fake")
    assert result["answer"] == "Your desk lamp has shipped."
    assert result["trace"][0]["tool"] == "get_order_details"


def test_agent_stops_after_step_limit():
    looping = [_reply(tool_calls=[_tool_call("get_order_details", '{"order_id": "ORD-1001"}')]) for _ in range(10)]
    result = run_agent([], "loop", client=FakeClient(looping), model="fake")
    assert "could not complete" in result["answer"]


def test_agent_fails_safely_on_api_error():
    class Broken:
        chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **k: 1 / 0))

    result = run_agent([], "hi", client=Broken(), model="fake")
    assert "Sorry" in result["answer"]


def test_agent_tools_see_only_scoped_orders():
    """Through the real graph, order tools respect use_orders (per-customer scoping)."""
    import json

    from tools.order_tools import use_orders

    mine = {"order_id": "ORD-2001", "status": "Shipped", "item": "Lamp", "ordered_on": "2026-10-01"}
    client = FakeClient([
        _reply(tool_calls=[_tool_call("get_order_details", '{"order_id": "ORD-2001"}')]),
        _reply(tool_calls=[_tool_call("get_order_details", '{"order_id": "ORD-1001"}')]),
        _reply(content="done"),
    ])
    with use_orders([mine]):
        result = run_agent([], "check both", client=client, model="fake")
    assert result["answer"] == "done"
    assert [t["args"]["order_id"] for t in result["trace"]] == ["ORD-2001", "ORD-1001"]
