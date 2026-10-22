"""Tool definitions the LLM can call, plus a safe dispatcher.

All inputs are validated here. Tool results and retrieved policy text are treated
as untrusted data: the model is told never to follow instructions found in them.
"""
import json
import re

from tools.order_tools import get_order_details, list_orders
from tools.return_tools import check_return_eligibility

ORDER_ID_RE = re.compile(r"^ORD-\d{3,8}$")

TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "list_my_orders",
            "description": "List the signed-in customer's orders (order ID, item, status, order date), newest first. Use when the customer does not give an order ID, e.g. 'where is my order?'.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Get the status and delivery details of an order by order ID (format ORD-1234).",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "e.g. ORD-1001"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_return_eligibility",
            "description": "Decide whether an order can be returned, using fixed business rules. Always use this for 'can I return...' questions.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "e.g. ORD-1002"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": "Search the store's return policy for passages relevant to a question (return window, refunds, conditions).",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "The policy question to look up"}},
                "required": ["query"],
            },
        },
    },
]


def _error(message: str) -> dict:
    return {"error": message}


def run_tool(name: str, raw_arguments: str) -> tuple[str, dict]:
    """Execute one tool call. Returns (JSON string for the model, trace entry for the UI)."""
    sources: list[dict] = []
    try:
        args = json.loads(raw_arguments or "{}")
        if not isinstance(args, dict):
            raise ValueError
    except ValueError:
        args, result = {}, _error("Tool arguments were not valid JSON.")
    else:
        if name == "list_my_orders":
            result = {
                "orders": [
                    {k: o.get(k) for k in ("order_id", "item", "status", "ordered_on")} for o in list_orders()[:20]
                ]
            }
        elif name in ("get_order_details", "check_return_eligibility"):
            order_id = str(args.get("order_id", "")).strip().upper()
            args["order_id"] = order_id
            if not ORDER_ID_RE.match(order_id):
                result = _error("Invalid order ID. Expected a format like ORD-1001.")
            elif name == "get_order_details":
                result = get_order_details(order_id) or _error(f"Order {order_id} was not found.")
            else:
                result = check_return_eligibility(order_id)
        elif name == "search_policy":
            query = str(args.get("query", "")).strip()[:300]
            args["query"] = query
            if not query:
                result = _error("A search query is required.")
            else:
                from rag.retrieve import search_policy  # lazy: keeps chromadb optional for tests

                hits = search_policy(query)
                sources = [{"source": h["source"], "section": h["section"]} for h in hits]
                result = {"passages": [{"section": h["section"], "text": h["text"]} for h in hits]}
        else:
            result = _error(f"Unknown tool: {name}")

    return json.dumps(result, ensure_ascii=False), {"tool": name, "args": args, "sources": sources}
