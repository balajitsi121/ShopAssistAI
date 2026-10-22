import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

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

response = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "deepseek-flash"),
    messages=[{"role": "user", "content": "Where is my order ORD-1001?"}],
    tools=tools,
)

msg = response.choices[0].message
print("Tool calls:", msg.tool_calls if msg.tool_calls else "NONE - answered in text")
print("Text:", msg.content)
