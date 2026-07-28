# exobios-ingest

Standalone offline ingestion pipeline for exobios-ai. Takes raw client
documents, parses/chunks/embeds them, and writes the result into Qdrant so
the online RAG service can retrieve from them. Runs as a one-off script, not
a server — separate project from the FastAPI request-serving service.

## What this project does

1. Load a raw document (PDF/DOCX/etc.) and parse it into a structured form
2. Classify it — assign `complaint_category` and `applicable_roles`
3. Register it — save its metadata to a local registry file
4. Clean/process the parsed structure (currently a pass-through stage)
5. Chunk it into retrieval-sized pieces, each carrying heading/page info
6. Embed each chunk into a vector
7. Store each chunk (vector + metadata) as a point in Qdrant

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- Docker (to run Qdrant locally)
- An OpenAI API key

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
cd exobios-ingest
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

<!--
### 4. Set up environment variables

Create a `.env` file in the project root:

```env
openai_api_key=sk-your-key-here
qdrant_url=http://localhost:6333
collection_name=clinical_corpus
embedding_model=text-embedding-3-small
chunk_max_tokens=400
tokenizer_model=BAAI/bge-small-en-v1.5
client_files_dir=data/client_files
registry_path=data/registry.json
```

`.env` is loaded automatically via `pydantic-settings`. Never commit this
file — it holds your real API key.

### 5. Start Qdrant locally

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Leave this running in its own terminal. The pipeline connects to it at
`http://localhost:6333` by default — confirm this matches `qdrant_url` in
your `.env`.

### 6. Add documents to ingest

Drop your source files (PDF/DOCX) into:

```
data/client_files/
```

Every file in this folder gets processed when you run the pipeline. This
folder is read-only from the pipeline's perspective — nothing here gets
modified.

## Running the pipeline

```bash
uv run ingestion/scripts/main.py
```

This processes every file in `data/client_files/` sequentially: load →
classify → register → process → chunk → embed → store. Progress prints to
the terminal per document and per stage.
-->
## Project structure

```
exobios-ingest/
├── ingestion/
│   ├── config/
│   │   └── settings.py         # all tunable values, loaded from .env
│   ├── loaders/
│   │   └── loader.py           # raw file -> parsed Docling document + document_id
│   ├── services/
│   │   ├── classify_documents.py  # LLM call: assigns complaint_category, applicable_roles
│   │   └── registry.py            # writes document metadata to registry.json
│   ├── process/
│   │   └── process.py          # cleans/organises the parsed document before chunking
│   ├── chunkers/
│   │   └── chunker.py           # splits parsed document into chunks with heading/page info
│   ├── embedder/
│   │   └── embedder.py           # calls the embedding model, returns a vector per chunk
│   ├── store/
│   │   └── qdrant_store.py        # writes each chunk (vector + metadata) into Qdrant
│   └── scripts/
│       └── main.py                 # orchestrator — runs every stage in sequence, per document
├── data/
│   ├── client_files/                # input documents go here
│   └── registry.json                  # generated — document_id -> metadata lookup
├── .env                                # not committed — your local config/secrets
├── pyproject.toml                        # dependency manifest (uv-managed)
└── README.md
```

## What each file is responsible for

- **`config/settings.py`** — single source of truth for every configurable
  value (model names, Qdrant URL, chunk size, folder paths). Every other
  file imports from here rather than hardcoding its own values.
- **`loaders/loader.py`** — takes one filepath, runs it through Docling,
  returns the structured document plus a freshly generated `document_id`.
  Does not chunk, classify, or clean — parsing only.
- **`services/classify_documents.py`** — sends the document's text to an
  LLM once, asking it to pick applicable `complaint_category` and
  `applicable_roles` values from a fixed list. Runs once per document, not
  per chunk.
- **`services/registry.py`** — appends the document's metadata (title,
  file location, classification result) to `data/registry.json`, keyed by
  `document_id`. This is the lookup used later to resolve a citation's
  `document_id` back into a human-readable title and file link.
- **`process/process.py`** — intended for cleaning/organising the parsed
  document before chunking. Currently a pass-through — no real cleaning
  logic implemented yet.
- **`chunkers/chunker.py`** — runs Docling's `HybridChunker` over the
  processed document, producing a list of chunks. Each chunk carries its
  text, the heading it fell under, and its page number.
- **`embedder/embedder.py`** — wraps the embedding model API call. Takes a
  chunk's text, returns its vector. Holds the API client once at
  construction rather than recreating it per call.
- **`store/qdrant_store.py`** — wraps the Qdrant client. Ensures the
  target collection exists, and writes one point (vector + merged
  document/chunk metadata) per chunk.
- **`scripts/main.py`** — the only file you actually run. Loops over every
  file in `data/client_files/`, calling each stage above in order for that
  file, then moves to the next.

<!--
## Known limitations (current state)

- `content_hash`, `ingestion_version`, `chunk_id`, `section`, `page_end`
  are not yet populated in the stored payload.
- `issuing_authority`, `version`, `publication_date` are not extracted —
  these require either an LLM guess added to the classification step, or
  manual entry, neither of which is wired up yet.
- `is_red_flag_chunk` classification is not implemented — deferred to a
  later evaluation phase.
- `original_file_location` currently stores a local filepath, not a
  cloud storage link. File upload to object storage (S3 or equivalent) is
  not yet implemented — files are referenced locally only.
- No caching layer yet — re-running the pipeline reprocesses every file
  in `data/client_files/` from scratch, even if already ingested.
- No human review/approval step before a document's chunks are written to
  Qdrant.
-->