# ShopAssist AI - WordPress Demo Site Setup

Goal: a dummy WooCommerce shop on the development server with a floating ShopAssist chat bubble, so the POC can be shown to the client inside a realistic shop.

## How it fits together

```
Visitor browser  ->  WordPress (chat bubble plugin)  ->  ShopAssist API (FastAPI, port 8000)  ->  agent + RAG + DeepSeek
```

- The browser only talks to WordPress (`/wp-json/shopassist/v1/chat`).
- WordPress calls the ShopAssist API from the server, so the API URL and key are never exposed in the page and there are no CORS problems.
- The API runs the same agent as the Streamlit screen (`agent/agent.py`).

## What you need

1. A development server with WordPress 6.x and PHP 7.4 or later (WooCommerce optional but recommended).
2. Python 3.11 on the server (or any machine the WordPress server can reach).
3. Your DeepSeek API key.
4. Internet from the Python machine (DeepSeek API, and a one-time ~90 MB embedding model download).

## Part A - Run the ShopAssist API

1. Copy the project folder to the server. Leave out `.venv`, `.env`, `chroma_db` and `__pycache__`.
2. In the project folder:

```
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
```

3. Edit `.env`:

```
DEEPSEEK_API_KEY=<your DeepSeek key>
SHOPASSIST_API_KEY=<make up a long random string>
```

4. Build the policy index once (downloads the embedding model):

```
python -m rag.ingest
```

5. Start the API:

```
uvicorn api.server:app --host 127.0.0.1 --port 8000
```

   - Use `127.0.0.1` if WordPress runs on the same server.
   - Use `0.0.0.0` only if WordPress is on another machine, and allow port 8000 in the firewall for the WordPress server only.
6. Check it: open `http://<server>:8000/health`. You should see `{"status":"ok"}`.

To keep it running after you log out, use a service. Linux example (`/etc/systemd/system/shopassist.service`):

```
[Unit]
Description=ShopAssist AI API
After=network.target

[Service]
WorkingDirectory=/opt/ShopAssistAI
ExecStart=/opt/ShopAssistAI/.venv/bin/uvicorn api.server:app --host 127.0.0.1 --port 8000
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

Then `sudo systemctl enable --now shopassist`.

## Part B - Build the WordPress demo site

1. Install WordPress on the dev server if it is not there yet.
2. Install and activate **WooCommerce** (Plugins > Add New). Run its setup wizard with the store country you want; skip payments and shipping.
3. Install the chat plugin: Plugins > Add New > Upload Plugin > choose `shopassist-chat.zip` (in the `wordpress` folder of the project) > Install > Activate.
4. Go to **Settings > ShopAssist Chat** and fill in:
   - **API URL**: for example `http://127.0.0.1:8000`
   - **API key**: the same value as `SHOPASSIST_API_KEY` in `.env`
   - Leave **Show tool calls** ticked for demos, so the client can see how the agent works.
5. Click **Save Changes**, then **Test connection**. You should see "Connected".
6. Click **Create demo content**. This adds:
   - a **Returns Policy** page (the same text as the policy the agent searches),
   - a **Demo Orders** page listing the four sample order numbers,
   - four WooCommerce products (Desk lamp, Running shoes, Clearance backpack, Rain jacket).
7. Optional polish: set the store currency to Indian Rupee in WooCommerce > Settings > General (the sample totals are in rupees), add the two pages to the main menu, and choose a clean shop theme such as Storefront.
8. Open the site front end. A **Chat** button appears bottom right.

## Demo script (about 5 minutes)

| # | Say or type | What the client should see |
| --- | --- | --- |
| 1 | Open the shop, then click Chat | The assistant greets and offers three starter questions |
| 2 | Where is my order ORD-1001? | Status "Shipped" and the estimated delivery date; the tool chip `get_order_details` |
| 3 | Can I return ORD-1002? | Eligible (delivered within the 30-day window); tool chip `check_return_eligibility` |
| 4 | Can I return ORD-1003? | Not eligible, because it is a final-sale item |
| 5 | How long do refunds take? | Answer from the policy, with the source "Return Policy - 4. Refund procedure" |
| 6 | Where is my order ORD-9999? | A polite "not found" instead of an invented answer |
| 7 | Please refund my order | The assistant explains it cannot issue refunds or start returns |

Point out: the return decision comes from fixed business rules, not from the language model; answers are grounded in the sample data and the policy page visible on the site.

## Troubleshooting

| Problem | Likely cause and fix |
| --- | --- |
| No Chat button on the site | Plugin not activated, or a page cache is serving an old page. Clear the cache and reload. |
| "Could not reach the API" on Test connection | API not running, wrong URL, or firewall. Open `/health` from the WordPress server with `curl`. |
| Chat says "assistant is not available right now" | API returned an error. Check the API terminal: usually a wrong `X-API-Key`, a missing DeepSeek key, or no internet from the API machine. |
| Chat says you are sending messages too quickly | Built-in limit of 20 messages per minute per visitor. Wait a minute. |
| First answer is slow | The embedding model is loading. Run `python -m rag.ingest` once beforehand, and ask a test question before the demo. |
| Policy answers look wrong | Edit `data/policies/return_policy.md`, run `python -m rag.ingest`, and keep the WordPress Returns Policy page in step with it. |

## Security notes (development only)

- The demo uses synthetic data only. Do not put real customer or order data behind it.
- Always set `SHOPASSIST_API_KEY`, and do not expose port 8000 to the public internet.
- Use HTTPS for the dev site if it is reachable from outside the office.
- Keep the DeepSeek key only in `.env`. It is never stored in WordPress.
- The widget's public endpoint has a basic rate limit, but it is not a replacement for real bot protection on a live site.
- The WooCommerce products are display items only. The chat answers come from the ShopAssist sample orders (ORD-1001 to ORD-1004), not from WooCommerce orders.

## Files added for this demo

- `api/server.py` - HTTP API (`/chat`, `/health`) around the agent
- `wordpress/shopassist-chat/` - the WordPress plugin source
- `wordpress/shopassist-chat.zip` - upload this in WordPress
- `tests/test_api.py` - API tests
