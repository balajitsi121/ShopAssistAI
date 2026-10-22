"""Deterministic return eligibility rules. No LLM is involved in these decisions."""
from datetime import date

from tools.order_tools import get_order_details

RETURN_WINDOW_DAYS = 30  # Sample policy, section 2. Pending PM approval.


def check_return_eligibility(order_id: str, today: date | None = None) -> dict:
    """Check whether an order can be returned under the sample policy.

    Returns {"order_id", "eligible", "reasons"}. Every failed rule adds a reason.
    """
    today = today or date.today()
    order = get_order_details(order_id)

    if order is None:
        return {"order_id": order_id, "eligible": False, "reasons": ["Order not found."]}

    reasons = []

    if order["status"] != "Delivered" or not order.get("delivered_on"):
        reasons.append(f"Order is not delivered yet (status: {order['status']}).")
    else:
        days_since = (today - date.fromisoformat(order["delivered_on"])).days
        if days_since > RETURN_WINDOW_DAYS:
            reasons.append(
                f"Delivered {days_since} days ago, outside the {RETURN_WINDOW_DAYS}-day return window."
            )

    if order.get("final_sale"):
        reasons.append("Item is marked final sale and cannot be returned.")

    return {"order_id": order["order_id"], "eligible": not reasons, "reasons": reasons}
