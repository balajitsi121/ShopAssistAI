"""ShopAssist AI chat interface.   Run:  streamlit run ui/app.py"""
import html
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make project root importable

import streamlit as st
from dotenv import load_dotenv

from agent.agent import run_agent
from tools.order_tools import list_orders

load_dotenv()
ACCENT = "#0f766e"

st.set_page_config(page_title="ShopAssist AI", page_icon="🛍️", layout="wide")

st.markdown(
    f"""
<style>
section[data-testid="stSidebar"] {{ background: #f3f5f4; }}
.sa-title {{ font-size: 1.6rem; font-weight: 700; color: #0f4c45; margin: 0; }}
.sa-badge {{ display: inline-block; font-size: .75rem; font-weight: 600; color: #7a4b00;
  background: #fdf0d5; border-radius: 999px; padding: 4px 10px; margin: 6px 0 12px; }}
.sa-chip {{ display: inline-block; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .75rem;
  color: #0f4c45; background: #e3f1ee; border-radius: 6px; padding: 3px 8px; margin: 0 6px 6px 0; }}
.sa-source {{ display: inline-block; font-size: .8rem; color: #1f2937; background: #fff;
  border: 1px solid #d3dbd8; border-radius: 6px; padding: 2px 8px; margin: 0 6px 6px 0; }}
.sa-label {{ font-size: .8rem; color: #5b6763; margin-right: 6px; }}
div.stButton > button {{ text-align: left; border-radius: 8px; }}
div.stButton > button:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
</style>
""",
    unsafe_allow_html=True,
)

# ---- session state -------------------------------------------------------------------------
st.session_state.setdefault("messages", [])  # [{"role", "content", "trace"}]
st.session_state.setdefault("pending", None)  # prompt queued by a sidebar button


def render_details(trace: list[dict]) -> None:
    """Show tool calls and policy sources under an assistant answer."""
    if not trace:
        return
    chips = "".join(
        f'<span class="sa-chip">tool: {html.escape(t["tool"])}({html.escape(", ".join(repr(v) for v in t["args"].values()))})</span>'
        for t in trace
    )
    st.markdown(chips, unsafe_allow_html=True)
    sources = {(s["source"], s["section"]) for t in trace for s in t["sources"]}
    if sources:
        tags = "".join(
            f'<span class="sa-source">{html.escape(src)} · {html.escape(sec)}</span>' for src, sec in sorted(sources)
        )
        st.markdown(f'<span class="sa-label">Sources:</span>{tags}', unsafe_allow_html=True)


# ---- sidebar -------------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<p class="sa-title">ShopAssist AI</p>', unsafe_allow_html=True)
    st.markdown('<span class="sa-badge">Proof of concept · sample data only</span>', unsafe_allow_html=True)

    st.caption("SAMPLE ORDERS")
    for order in list_orders():
        label = f"{order['order_id']} · {order['item']} · {order['status']}"
        if st.button(label, key=f"order-{order['order_id']}", use_container_width=True):
            st.session_state.pending = f"Where is my order {order['order_id']}?"

    st.caption("TRY ASKING")
    for question in (
        "Can I return the running shoes from ORD-1002?",
        "Can I return ORD-1003?",
        "How long do refunds take?",
    ):
        if st.button(question, key=f"q-{question}", use_container_width=True):
            st.session_state.pending = question

    st.caption("SETTINGS")
    st.text_input("LLM provider", value=f"DeepSeek ({os.getenv('LLM_MODEL', 'deepseek-flash')})", disabled=True)
    show_details = st.checkbox("Show tool calls and sources", value=True)
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("Read-only demo. ShopAssist cannot issue refunds, change orders or submit real returns.")

# ---- main chat -----------------------------------------------------------------------------
st.subheader("Order and returns assistant")
st.caption("Ask about order status, return eligibility or the return policy.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant" and show_details:
            render_details(message.get("trace", []))

prompt = st.chat_input("Ask about an order, a return or the policy")
if st.session_state.pending:
    prompt, st.session_state.pending = st.session_state.pending, None

if prompt:
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = run_agent(history, prompt)
        st.write(result["answer"])
        if show_details:
            render_details(result["trace"])
    st.session_state.messages.append({"role": "assistant", "content": result["answer"], "trace": result["trace"]})
