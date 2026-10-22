import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

import api.server as server

client = TestClient(server.app)


def _fake_agent(history, message, **kwargs):
    return {"answer": f"echo: {message}", "trace": [{"tool": "get_order_details", "args": {}, "sources": []}]}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_chat_returns_answer_and_trace(monkeypatch):
    monkeypatch.setattr(server, "run_agent", _fake_agent)
    monkeypatch.setattr(server, "API_KEY", "")
    body = client.post("/chat", json={"message": "hi", "history": []}).json()
    assert body["answer"] == "echo: hi"
    assert body["trace"][0]["tool"] == "get_order_details"


def test_chat_requires_key_when_configured(monkeypatch):
    monkeypatch.setattr(server, "run_agent", _fake_agent)
    monkeypatch.setattr(server, "API_KEY", "secret")
    assert client.post("/chat", json={"message": "hi"}).status_code == 401
    assert client.post("/chat", json={"message": "hi"}, headers={"X-API-Key": "secret"}).status_code == 200


def test_chat_rejects_empty_and_oversized_messages(monkeypatch):
    monkeypatch.setattr(server, "API_KEY", "")
    assert client.post("/chat", json={"message": ""}).status_code == 422
    assert client.post("/chat", json={"message": "x" * 1001}).status_code == 422


def test_chat_scopes_tools_to_supplied_orders(monkeypatch):
    """With `orders`, the agent's order tools see only those orders (not orders.json)."""
    from tools.order_tools import get_order_details

    seen = {}

    def agent(history, message, **kwargs):
        seen["mine"] = get_order_details("ORD-2001")
        seen["other"] = get_order_details("ORD-1001")  # exists in orders.json, not in this customer's orders
        seen["context"] = kwargs.get("customer_context")
        return {"answer": "ok", "trace": []}

    monkeypatch.setattr(server, "run_agent", agent)
    monkeypatch.setattr(server, "API_KEY", "")
    order = {"order_id": "ORD-2001", "status": "Shipped", "item": "Lamp", "ordered_on": "2026-10-01"}
    r = client.post("/chat", json={"message": "hi", "orders": [order], "customer_name": "Asha"})
    assert r.status_code == 200
    assert seen["mine"]["item"] == "Lamp"
    assert seen["other"] is None
    assert "Asha" in seen["context"]


def test_chat_guest_sees_no_orders(monkeypatch):
    from tools.order_tools import list_orders

    seen = {}

    def agent(history, message, **kwargs):
        seen["orders"] = list_orders()
        seen["context"] = kwargs.get("customer_context")
        return {"answer": "ok", "trace": []}

    monkeypatch.setattr(server, "run_agent", agent)
    monkeypatch.setattr(server, "API_KEY", "")
    client.post("/chat", json={"message": "hi", "orders": []})
    assert seen["orders"] == []
    assert "not signed in" in seen["context"]


def test_chat_rejects_malformed_orders(monkeypatch):
    monkeypatch.setattr(server, "API_KEY", "")
    bad = {"order_id": "x; drop", "status": "Shipped", "item": "Lamp"}
    assert client.post("/chat", json={"message": "hi", "orders": [bad]}).status_code == 422
