import os
import ollama
from dotenv import load_dotenv

load_dotenv()
MODEL = os.getenv("OLLAMA_MODEL", "qwen2:7b")

tools = [{
    "type": "function",
    "function": {
        "name": "get_order_details",
        "description": "Look up an order by its order ID, e.g. ORD-1001.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
}]

response = ollama.chat(
    model=MODEL,
    messages=[{"role": "user", "content": "Where is my order ORD-1001?"}],
    tools=tools,
)

calls = response.message.tool_calls
print("Tool calls:", calls if calls else "NONE - model answered in text")
print("Text:", response.message.content)