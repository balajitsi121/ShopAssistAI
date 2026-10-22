from datetime import date

from tools.return_tools import check_return_eligibility

TODAY = date(2026, 10, 16)


def test_delivered_within_window_is_eligible():
    result = check_return_eligibility("ORD-1002", today=TODAY)
    assert result["eligible"] is True
    assert result["reasons"] == []


def test_outside_return_window_is_not_eligible():
    result = check_return_eligibility("ORD-1002", today=date(2026, 11, 20))
    assert result["eligible"] is False
    assert "return window" in result["reasons"][0]


def test_final_sale_is_not_eligible():
    result = check_return_eligibility("ORD-1003", today=date(2026, 9, 20))
    assert result["eligible"] is False
    assert any("final sale" in r for r in result["reasons"])


def test_shipped_order_is_not_eligible():
    result = check_return_eligibility("ORD-1001", today=TODAY)
    assert result["eligible"] is False
    assert "not delivered" in result["reasons"][0]


def test_processing_order_is_not_eligible():
    assert check_return_eligibility("ORD-1004", today=TODAY)["eligible"] is False


def test_unknown_order_is_not_eligible():
    result = check_return_eligibility("ORD-0000", today=TODAY)
    assert result["eligible"] is False
    assert result["reasons"] == ["Order not found."]
