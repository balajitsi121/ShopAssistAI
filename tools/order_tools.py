"""Order lookup tool.

By default it reads synthetic sample orders from data/orders.json (CLI / Streamlit demo).
The HTTP API can instead scope a single request to the signed-in customer's own orders
(supplied by the trusted WordPress server) with `use_orders(...)`.
"""
import json
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

ORDERS_FILE = Path(__file__).resolve().parent.parent / "data" / "orders.json"

# When set, all order tools see only these orders (keyed by order_id) instead of orders.json.
_request_orders: ContextVar[dict[str, dict] | None] = ContextVar("request_orders", default=None)


@contextmanager
def use_orders(orders: list[dict]):
    """Scope order lookups to `orders` (one customer's orders) for the duration of the block."""
    token = _request_orders.set({o["order_id"].strip().upper(): o for o in orders})
    try:
        yield
    finally:
        _request_orders.reset(token)


def _load_orders() -> dict[str, dict]:
    """Load orders keyed by order_id: the request-scoped orders if set, else the sample file."""
    scoped = _request_orders.get()
    if scoped is not None:
        return scoped
    with ORDERS_FILE.open(encoding="utf-8") as f:
        return {order["order_id"]: order for order in json.load(f)}


def get_order_details(order_id: str) -> dict | None:
    """Return order details if the order exists (in scope), otherwise None."""
    return _load_orders().get(order_id.strip().upper())


def list_orders() -> list[dict]:
    """Return all orders in scope, newest first (used by the UI sidebar and list_my_orders)."""
    return sorted(_load_orders().values(), key=lambda o: o.get("ordered_on") or "", reverse=True)
