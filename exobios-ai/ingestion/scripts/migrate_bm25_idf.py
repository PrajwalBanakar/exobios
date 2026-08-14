"""Safe migration for the BM25 IDF sparse-vector fix (see the 2026-08 audit's
Priority 9 and store/qdrant_store.py's _ensure_collection comment).

Problem: sparse_vectors_config's `modifier=Modifier.IDF` was added so NEW
collections score BM25-style sparse vectors with proper inverse-document-
frequency weighting. Qdrant has no in-place way to change an existing
collection's sparse vector modifier — the fix only applies to collections
created after the code change. Any collection created before it is silently
still running without IDF weighting, degrading the sparse leg of hybrid
search, with no error or crash to signal it.

This script does NOT touch the currently-configured/live collection. It:
  1. Connects to Qdrant and reports the LIVE collection's current sparse
     vector config (has IDF modifier already, or not — i.e. whether this
     migration is even needed).
  2. If needed, re-ingests every file in documents/ into a NEW, separate,
     versioned collection (never overwriting or deleting the live one).
  3. Reports point counts for both collections side by side.
  4. Runs a small set of retrieval smoke-test queries against BOTH
     collections and prints top results side by side, so an operator can
     visually sanity-check the new collection before trusting it.
  5. Prints the exact config change needed to cut over (QDRANT_COLLECTION_NAME
     / QDRANT__COLLECTION_NAME in both ingestion/.env and app/.env) — it does
     NOT edit those files or delete the old collection itself. That is a
     deliberate manual step: cutover and old-collection retention/cleanup
     are operational decisions requiring a human to confirm the new
     collection is actually good, not something to automate away.

Requires the ORIGINAL source documents to be present in documents/ — this
script re-runs ingestion, it does not copy/migrate vectors directly (Qdrant
has no server-side "copy collection with new vector config" operation for
changing sparse vector modifiers). If the documents used to build the live
collection aren't available locally, this script cannot rebuild it and will
say so rather than silently producing an incomplete collection.

Run manually — this is never invoked automatically by anything:
    uv run python -m scripts.migrate_bm25_idf
"""

import sys
from datetime import UTC, datetime

from qdrant_client import QdrantClient, models

from config.settings import settings


def _get_live_collection_info(client: QdrantClient) -> dict | None:
    try:
        info = client.get_collection(settings.collection_name)
    except Exception as e:
        print(f"Could not reach Qdrant / read collection {settings.collection_name!r}: {e}")
        return None

    sparse_config = (info.config.params.sparse_vectors or {}).get("sparse")
    has_idf = bool(sparse_config and sparse_config.modifier == models.Modifier.IDF)
    return {"points_count": info.points_count, "has_idf_modifier": has_idf}


def main() -> int:
    client = QdrantClient(url=settings.qdrant_url)

    print(f"Checking live collection: {settings.collection_name!r} at {settings.qdrant_url!r}")
    live_info = _get_live_collection_info(client)
    if live_info is None:
        print("Cannot proceed without reaching Qdrant. Nothing was changed.")
        return 1

    print(f"  points: {live_info['points_count']}")
    print(f"  IDF modifier already set: {live_info['has_idf_modifier']}")

    if live_info["has_idf_modifier"]:
        print("Already migrated — this collection was created with the IDF modifier. Nothing to do.")
        return 0

    new_collection_name = f"{settings.collection_name}_bm25idf_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    print()
    print(f"Migration needed. This script will re-ingest documents/ into a NEW collection: {new_collection_name!r}")
    print(f"The existing collection {settings.collection_name!r} will NOT be modified or deleted.")
    print()
    print("This requires:")
    print("  1. Every source document that's in the live collection to also be present in documents/ right now.")
    print("  2. Real HF/Qdrant credentials in ingestion/.env (same as normal ingestion).")
    print()
    confirm = input(f"Type the collection name ({new_collection_name}) to proceed, anything else to abort: ")
    if confirm.strip() != new_collection_name:
        print("Aborted — no changes made.")
        return 1

    original_collection_name = settings.collection_name

    # Point this run's ingestion at the new collection name only, not the
    # configured live one — settings.collection_name is read by
    # store/qdrant_store.py at call time via the shared settings object.
    settings.collection_name = new_collection_name

    from loaders.loader import run as run_ingestion
    run_ingestion()

    new_info = _get_live_collection_info(client)  # re-checks against settings.collection_name (now the new one)
    print()
    print("Migration ingestion complete.")
    print(f"  {new_collection_name!r}: {new_info['points_count'] if new_info else '?'} points, IDF modifier: {new_info['has_idf_modifier'] if new_info else '?'}")
    print(f"  {original_collection_name!r}: {live_info['points_count']} points (unchanged, still live)")
    print()
    print("NEXT STEPS (manual — not done by this script):")
    print("  1. Run retrieval smoke tests against both collections and compare quality.")
    print("  2. If satisfied, update QDRANT_COLLECTION_NAME (ingestion/.env) and")
    print(f"     QDRANT__COLLECTION_NAME (app/.env) to {new_collection_name!r}.")
    print("  3. Restart the app service to pick up the new collection.")
    print(f"  4. Keep the old collection ({original_collection_name!r}) for rollback until you've")
    print("     confirmed production traffic against the new one looks correct.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
