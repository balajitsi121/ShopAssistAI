from tools.order_tools import get_order_details


def test_known_order_returns_details():
    assert get_order_details("ORD-1001")["status"] == "Shipped"


def test_unknown_order_returns_none():
    assert get_order_details("ORD-0000") is None
