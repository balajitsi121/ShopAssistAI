import json

from agent.tool_registry import run_tool


def _run(name, args):
    result, trace = run_tool(name, json.dumps(args))
    return json.loads(result), trace


def test_order_lookup():
    result, trace = _run("get_order_details", {"order_id": "ord-1001"})
    assert result["status"] == "Shipped"
    assert trace["args"]["order_id"] == "ORD-1001"


def test_invalid_order_id_is_rejected():
    result, _ = _run("get_order_details", {"order_id": "1001; DROP TABLE"})
    assert "Invalid order ID" in result["error"]


def test_unknown_order():
    result, _ = _run("get_order_details", {"order_id": "ORD-9999"})
    assert "not found" in result["error"]


def test_eligibility_runs_business_rules():
    result, _ = _run("check_return_eligibility", {"order_id": "ORD-1003"})
    assert result["eligible"] is False


def test_unknown_tool_and_bad_json():
    assert "Unknown tool" in _run("delete_everything", {})[0]["error"]
    result, _ = run_tool("get_order_details", "not json")
    assert "valid JSON" in json.loads(result)["error"]


def test_list_my_orders_is_scoped_and_newest_first():
    from tools.order_tools import use_orders

    orders = [
        {"order_id": "ORD-3001", "status": "Delivered", "item": "A", "ordered_on": "2026-09-01"},
        {"order_id": "ORD-3002", "status": "Shipped", "item": "B", "ordered_on": "2026-10-01"},
    ]
    with use_orders(orders):
        result, _ = _run("list_my_orders", {})
        other, _ = _run("get_order_details", {"order_id": "ORD-1001"})
    assert [o["order_id"] for o in result["orders"]] == ["ORD-3002", "ORD-3001"]
    assert "not found" in other["error"]


def test_longer_order_numbers_are_accepted():
    result, _ = _run("get_order_details", {"order_id": "ORD-12345"})
    assert "not found" in result["error"]  # valid format, just unknown
