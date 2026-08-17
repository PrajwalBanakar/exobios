# data/

Local document storage for the textbook RAG proof of concept (AI-7A). This
directory is where original source documents live on disk during local
development, plus space reserved for artifacts a future ingestion pipeline
will derive from them.

**Nothing under `source_documents/`, `extracted/`, or `processed/` is
committed to Git** — only this README and the `.gitkeep` placeholders that
keep the folder structure present on a fresh clone. Verify with
`git check-ignore -v data/source_documents/<subject>/<file>.pdf`.

## Where PDFs go

```text
data/source_documents/anatomy/
data/source_documents/physiology/
data/source_documents/biochemistry/
```

Drop the original PDF straight into the subfolder matching its subject. No
renaming, no processing — just the file as downloaded.

## Workflow

```text
Google Drive
  → manually download the approved textbook
  → place the original PDF under data/source_documents/<subject>/
  → register it (python scripts/register_document.py register ...)
  → a future ingestion pipeline phase (AI-7B+) processes it from here
```

## Rules

- **Originals are immutable.** Nothing in this codebase edits a file under
  `source_documents/` — it is read-only input. If a book needs correcting,
  replace the file and re-register it; don't hand-edit a PDF in place.
- **PDFs are never committed.** These are the client's copyrighted
  textbooks. `.gitignore` excludes the actual files; only directory
  structure (via `.gitkeep`) is tracked.
- **Filenames are not application logic.** Which subject/title/edition a
  document is comes from its registry metadata (see
  `scripts/register_document.py` and `SQLiteDocumentRegistry`), never from
  parsing the filename. Name files however is convenient for you.
- **`extracted/` and `processed/` are reserved, not yet used.** They exist
  now so the eventual extraction/chunking phases (AI-7B/AI-7C) have an
  obvious place to write debug/intermediate artifacts, separate from the
  untouched originals. Nothing writes here yet.
- **Local disk is a POC stand-in, not the end state.** `LocalDocumentStorage`
  implements the same `DocumentStorage` interface an object-storage backend
  (S3, Cloudflare R2, GCS, Azure Blob, MinIO) would later implement — moving
  off local disk in production won't require touching the ingestion/registry
  code above this boundary.
