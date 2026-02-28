# Internal Knowledge Base Agent

RAG-based agent that indexes documentation, PDF/DOCX files, and past ticket resolutions. Team members ask questions in natural language and get accurate, sourced answers with streaming responses.

## Tech Stack

- **LLM**: Cohere (command-a-03-2025)
- **Embeddings**: Cohere (embed-english-v3.0)
- **Vector Store**: ChromaDB (local)
- **Document Formats**: PDF, DOCX
- **UI**: Streamlit

## Features

- Region-aware filtering (All, India, US) — use "All" for tickets that apply to all regions
- Department filter (Infra, HR, Finance, General)
- Ticket resolutions from JSON (sync from `data/ticket_resolutions.json`)
- Streaming AI responses
- Source citation in answers
- "I don't know" fallback when context is insufficient
- Confidence score on answers
- Query logging for audit trail
- Admin document manager (upload, list, delete)
- Last updated timestamps for documents

## Setup

### 1. Create virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# or: source .venv/bin/activate   # Linux/Mac
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env   # Windows
# or: cp .env.example .env   # Linux/Mac
```

Edit `.env` and add your Cohere API key:

```
COHERE_API_KEY=your_key_here
```

## Usage

### Run the app

```bash
streamlit run app.py
```

**Chat**: Select region (All/India/US) and department, then ask questions. Answers stream in real time with sources and confidence. "All" shows only general tickets; "India" or "US" shows region-specific plus "All" tickets.

**Admin**:
- **Sync Ticket Resolutions** — Loads tickets from `data/ticket_resolutions.json` into the knowledge base
- **Upload Documents** — Ingest PDF/DOCX with region and department
- **Document Library** — View and delete indexed documents

### Ticket resolutions

Edit `data/ticket_resolutions.json` to add or update tickets. Format:

```json
[
  {
    "ticket": "VPN not connecting",
    "region": "India",
    "resolution": "Reset MFA token and reissue certificate.",
    "department": "Infra"
  },
  {
    "ticket": "General password reset",
    "region": "All",
    "resolution": "Use self-service portal or contact IT.",
    "department": "Infra"
  }
]
```

Use `region: "All"` for tickets that apply to all regions (e.g. global policies).

Click **Sync Ticket Resolutions** in Admin to refresh the knowledge base.

### CLI (optional)

**Ingest a document:**

```bash
python scripts/ingest_example.py path/to/document.pdf India Infra
```

**Ask a question:**

```bash
python scripts/ask_example.py "How do I fix VPN issues?" India
```

Regions: `All`, `India`, `US`  
Departments: `Infra`, `HR`, `Finance`, `General`

### From Python

```python
from pathlib import Path
from src.rag_service import answer, answer_stream, get_admin_service

# Ask (non-streaming)
resp = answer("What is the VPN fix?", region="India", department="Infra")

# Ask (streaming)
for part in answer_stream("Laptop HDMI not working?", region="India"):
    if part["type"] == "token":
        print(part["content"], end="")
    elif part["type"] == "done":
        print(part["response"].sources)

# Admin
admin = get_admin_service()
admin.upload_document(Path("policy.pdf"), region="US", department="HR")
admin.sync_ticket_resolutions()
docs = admin.list_documents()
```

## Project Structure

```
knowledge-base-agent/
├── app.py                    # Streamlit UI
├── requirements.txt
├── pyproject.toml
├── .env.example
├── data/
│   └── ticket_resolutions.json   # Past ticket resolutions
├── src/
│   ├── config.py             # Settings, regions, departments, models
│   ├── models.py             # Pydantic/dataclass models
│   ├── document_loader.py    # PDF/DOCX text extraction
│   ├── chunker.py            # Text chunking
│   ├── embedding_service.py # Cohere embeddings (batched)
│   ├── vector_store.py       # ChromaDB + region/department filtering
│   ├── ingestion_service.py # Document + ticket ingestion
│   ├── generation_service.py # RAG + Cohere chat (streaming)
│   ├── query_logger.py       # Audit trail
│   ├── admin_service.py      # Document + ticket management
│   └── rag_service.py        # Main entry point
└── scripts/
    ├── ingest_example.py
    └── ask_example.py
```

## Data Flow

1. **Ingest documents**: PDF/DOCX → chunk → embed (Cohere, batched) → store in ChromaDB with metadata `{region, source, department, uploaded_at}`
2. **Ingest tickets**: `data/ticket_resolutions.json` → each ticket as chunk → embed → store with `source=ticket_resolutions`. Use `region: "All"` for tickets applicable to all regions.
3. **Query**: User question + region + department → embed query → retrieve top-k (region "India"/"US" returns that region + "All" chunks; "All" returns only "All" chunks) → Cohere chat_stream with documents → streaming answer + citations + confidence
4. **Log**: Each query appended to `query_logs.jsonl`

## Configuration

| Setting | Description |
|---------|-------------|
| `COHERE_API_KEY` | Required. Get from [Cohere Dashboard](https://dashboard.cohere.com/) |
| `CHROMA_PERSIST_DIR` | Vector store path (default: `./chroma_db`) |
| `EMBED_MODEL` | `embed-english-v3.0` (default) or `embed-v4.0` |
| `CHAT_MODEL` | `command-a-03-2025` (default) or `command-r-08-2024` |

## Excluded from Git

- `.env` — API keys
- `chroma_db/` — Vector store (regeneratable)
- `query_logs.jsonl` — Query audit log
