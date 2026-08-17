# exobios-ingest

Standalone away from user ingestion pipeline for exobios-ai. Takes raw client
documents, parses/chunks/embeds them, and writes the result into Qdrant so
the online RAG service can retrieve from them. Runs as a one-off script, not
a server — separate project from the FastAPI request-serving service.

## What this project does

1. Load a raw document (PDF/DOCX/etc.) and parse it into a structured form
2. Classify it — assign `complaint_category` and `applicable_roles`
3. Register it — upsert its metadata into Supabase
4. Clean/process the parsed structure (currently a pass-through stage)
5. Chunk it into retrieval-sized pieces, each carrying heading/page info
6. Embed each chunk into a vector
7. Store each chunk (vector + metadata) as a point in Qdrant

### Idempotency

`document_id` is derived deterministically from a SHA-256 hash of the source
file's bytes (`loaders/loader.py::_compute_document_id`), and each chunk's
Qdrant point id is derived from `(document_id, position in document)`
(`chunkers/chunker.py`). Re-running the pipeline on the same file —
deliberately, or as a retry after a crash/partial failure — always produces
the same ids, so the Supabase upsert and Qdrant upsert overwrite in place
rather than creating duplicates. If a run fails after the Supabase metadata
row is written but before Qdrant is fully populated (`run()` in
`loaders/loader.py` checks and logs this case explicitly), the fix is simply
to re-run the pipeline over the same file — it will fill in the missing
vectors without duplicating what already succeeded. Editing a file's content
and re-ingesting it produces a *new* document_id (different hash), i.e. is
treated as a new document version, not an in-place update of the old one.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- Docker (to run Qdrant locally)
- Other API keys/tokens in .env.example

## Setup

### 1. Install uv (if not already installed)

Mac/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone/enter the project and pin the Python version

```bash
cd exobios/exobios-ai/ingest
uv python pin 3.12
```

### 3. Install dependencies

```bash
uv sync
```

This reads `pyproject.toml` and installs everything into a project-local
virtual environment automatically — no manual `venv`/`activate` step needed.
All commands below should be run with `uv run`, which always executes
inside that environment.


### 4. Set up environment variables

Create a `.env` file in the project root:

#### Take a look at the `.env.example` file in ingestion/ folder, fill in those keys in an .env file

`.env` is loaded automatically via `pydantic-settings`. Never commit this
file — it holds your real API key.

### 5. Start Qdrant locally

`docker-compose.yaml` in this directory defines a local Qdrant service (no
Dockerfile for the ingestion script itself — it runs directly via `uv run`,
not in a container).

##### 1. Start docker (either via CLI or docker desktop)
##### 2. Execute:

```bash
docker compose up -d
```

### 6. Add documents to ingest

Drop your source files (PDF/DOCX) into:

```
documents/
```

Every file in this folder gets processed when you run the pipeline. 

## Running the pipeline

```bash
cd exobios/exobios-ai/ingestion
uv run python -m scripts.main
```

This processes every file in `documents/` sequentially: 
load → classify → register → process → chunk → embed → store. 
-->
## Project structure

```
exobios-ingest/
├── ingestion/
│   ├── config/
│   │   └── settings.py             # all tunable values, loaded from .env
│   ├── loaders/
│   │   ├── loader.py               # raw file -> executes all following services
│   │   ├── load_documents.py
│   │   ├── convert.py
│   │   └── classify_documents.py
│   ├── services/
│   │   └── upload.py               # writes document metadata + S3 identifiers to supabase + uploads parsed document and raw document to S3
│   ├── process/
│   │   └── process.py              # no assigned task, future scope, no need currently, do not implement
│   ├── chunkers/
│   │   └── chunker.py              # utilises docling hybridchunker + tiktoken tokeniser(works for now, in future HF tokeniser can be used)
│   ├── embedder/
│   │   └── embedder.py             # calls the embedding model, returns a vector per chunk
│   ├── store/
│   │   └── qdrant_store.py         # writes each chunk (vector + metadata) into Qdrant
│   └── scripts/
│       └── main.py                 # orchestrator — runs every stage in sequence, per document
├── data/
│   ├── docling_output/             # how parsed docs look (.md)
├── .env.example                    # rename and replace with your keys
├── pyproject.toml                  # dependency manifest (uv-managed)
└── README.md
```

#### To check out stored embeddings, : 
-> hit : http://localhost:6333/dashboard
-> Set up your AWS and Supabase account, fill in .env, then everything shall work end to end

## Tests

```bash
uv sync --dev
uv run pytest tests/ -v
```

These are pure-logic unit tests for the deterministic id derivation
(`_compute_document_id`, chunk id generation) that idempotency depends on —
they don't touch live Qdrant/Supabase/HF and skip themselves automatically
if docling isn't importable. There is no coverage yet for the full
load→classify→chunk→embed→store pipeline end to end; that would need a
recorded-fixture or live-integration test harness, which doesn't exist in
this project.