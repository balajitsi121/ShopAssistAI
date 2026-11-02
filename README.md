# ShopAssist AI API (Agentic AI POC)

REST API for an AI assistant that answers order status, return policy and return eligibility questions.
Policy RAG (keyword/BM25 retrieval) + predefined tools + deterministic business rules. Synthetic sample data only.

## Structure
- `api/`     FastAPI server (`/health`, `/chat`)
- `agent/`   LangGraph agent (model -> tools -> model) using any OpenAI-compatible LLM API (OpenRouter, DeepSeek)
- `tools/`   order lookup and return eligibility rules
- `rag/`     policy chunking and BM25 retrieval (pure Python, no model download)
- `data/`    sample orders and policy documents
- `tests/`   unit tests
- `render.yaml`  Render deployment blueprint

## Local setup
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env      # then add LLM_API_KEY
```

## Run locally
```
uvicorn api.server:app --reload --port 8000
```
Interactive docs: http://localhost:8000/docs

## API
`GET /health` returns `{"status": "ok"}`.

`POST /chat` (send header `X-API-Key` when `SHOPASSIST_API_KEY` is set)
```json
{
  "message": "Can I return ORD-1002?",
  "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
}
```
Response: `{"answer": "...", "trace": [{"tool": "...", "args": {...}, "sources": [...]}]}`

Optional per-customer mode: pass `orders` (the customer's own orders) and `customer_name`;
the agent then sees only those orders instead of `data/orders.json`.

## Other commands
- `python -m pytest`                         run unit tests
- `python -m rag.ingest`                     list the policy sections that will be searched
- `python -m rag.retrieve "refund time?"`    test policy search on its own

## Deploy (Render)
1. Commit and push to GitHub (`main`).
2. In Render: New > Blueprint, select this repository. Render reads `render.yaml`
   (build `pip install -r requirements.txt`, start `uvicorn api.server:app --host 0.0.0.0 --port $PORT`,
   health check `/health`, Python 3.11.9).
3. When prompted, enter `LLM_API_KEY` (OpenRouter key). Set `ALLOWED_ORIGINS` only if a browser calls the API directly;
   leave it blank when the WordPress server calls it server-to-server.
4. `SHOPASSIST_API_KEY` is generated automatically; copy it from the service's Environment tab into the
   WordPress plugin settings (sent as the `X-API-Key` header).
5. Verify: `curl https://<service>.onrender.com/health` then POST to `/chat` with the key.

| Variable | Required | Default |
|---|---|---|
| `LLM_API_KEY` (or `DEEPSEEK_API_KEY`) | yes | - |
| `LLM_BASE_URL` (or `DEEPSEEK_BASE_URL`) | no | `https://api.deepseek.com` (render.yaml sets OpenRouter) |
| `LLM_MODEL` (or `DEEPSEEK_MODEL`) | no | `deepseek-v4-flash` (render.yaml sets `openrouter/free`) |
| `SHOPASSIST_API_KEY` | recommended | blank = no auth |
| `ALLOWED_ORIGINS` | no | blank = no browser origins |

## Demo UI (Streamlit Community Cloud)
`ui/app.py` is an optional chat page for demos. It calls the agent directly; it does **not** expose
the `/chat` REST API, so WordPress must still use the API deployment above.
- Local: `pip install -r ui/requirements.txt` then `streamlit run ui/app.py`
- Cloud: New app > repository `main` > main file `ui/app.py` > Python 3.11; in Secrets add
  `LLM_API_KEY`, `LLM_BASE_URL` and `LLM_MODEL` (same values as the API).

## Notes
- OpenRouter's free router (`openrouter/free`) picks a random free model per request, so answer quality varies, and free usage is rate limited (roughly 50 requests/day without credits). One question can use up to 5 model calls.
- Policy search runs fully offline: sections are read from `data/policies/*.md` on first use and cached. Add or edit a `.md` file (one `## ` heading per section) and redeploy.
- Render's free plan sleeps after 15 minutes of inactivity; the next request takes roughly 30 to 60 seconds to wake it.
- Return rules and the 30-day window are from a draft sample policy pending PM approval.
