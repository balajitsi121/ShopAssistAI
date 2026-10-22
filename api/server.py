"""HTTP API around the ShopAssist agent, so other sites (e.g. the WordPress demo) can use it.

Run:  uvicorn api.server:app --host 0.0.0.0 --port 8000
"""
import hmac
import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent.agent import run_agent
from tools.order_tools import use_orders

load_dotenv()

API_KEY = os.getenv("SHOPASSIST_API_KEY", "")  # optional shared secret (sent as X-API-Key)
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class OrderIn(BaseModel):
    """One order of the signed-in customer, as supplied by the trusted WordPress server."""

    order_id: str = Field(pattern=r"^ORD-\d{3,8}$")
    status: Literal["Processing", "Shipped", "Delivered", "Cancelled"]
    item: str = Field(max_length=200)
    category: str | None = Field(default=None, max_length=100)
    final_sale: bool = False
    ordered_on: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    shipped_on: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    delivered_on: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    estimated_delivery: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    total: float | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[Turn] = Field(default_factory=list, max_length=20)
    # Per-customer mode (used by WordPress). `orders` present (even empty) = only these orders are visible.
    orders: list[OrderIn] | None = Field(default=None, max_length=50)
    customer_name: str | None = Field(default=None, max_length=100)


app = FastAPI(title="ShopAssist AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _customer_context(request: ChatRequest) -> str:
    if request.orders is None:
        return ""
    if request.customer_name:
        return f"The customer is signed in as {request.customer_name} and can only see their own orders."
    return "The customer is not signed in. Tell them to log in to see their orders; you can still explain the return policy."


@app.post("/chat")
def chat(request: ChatRequest, x_api_key: str = Header(default="")) -> dict:
    """Answer one customer message. Sync on purpose: FastAPI runs it in a worker thread."""
    if API_KEY and not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")
    history = [t.model_dump() for t in request.history]
    context = _customer_context(request)
    if request.orders is None:  # sample-data mode (orders.json)
        result = run_agent(history, request.message, customer_context=context)
    else:  # signed-in / guest mode: tools only see this customer's orders
        with use_orders([o.model_dump() for o in request.orders]):
            result = run_agent(history, request.message, customer_context=context)
    return {"answer": result["answer"], "trace": result["trace"]}
