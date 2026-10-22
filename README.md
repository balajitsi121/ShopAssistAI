# ShopAssist AI (Agentic AI POC)

Agentic AI assistant for order status, return policy questions and return eligibility.
Vector RAG + predefined tools + deterministic business rules. Synthetic sample data only.

## Structure
- `tools/`   order lookup and return eligibility rules
- `rag/`     policy chunking, embeddings, ChromaDB retrieval
- `agent/`   LangGraph agent (model -> tools -> model) using the DeepSeek API
- `ui/`      Streamlit chat interface
- `data/`    sample orders and policy documents
- `tests/`   unit tests (`python -m pytest`)

## Setup (once)
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then add DEEPSEEK_API_KEY
```

## Run
```
.venv\Scripts\activate
streamlit run ui/app.py
```

Other commands:
- `python -m pytest`                         run unit tests
- `python -m rag.ingest`                     rebuild the policy index (also runs automatically on first question)
- `python -m rag.retrieve "refund time?"`    test policy search on its own
- `python test_deepseek.py`                  check the DeepSeek key and tool calling

## Notes
- First policy search downloads the embedding model (about 90 MB), so it needs internet once.
- Return rules and the 30-day window are from a draft sample policy pending PM approval.
