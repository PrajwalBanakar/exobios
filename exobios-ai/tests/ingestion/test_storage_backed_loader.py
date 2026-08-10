from pathlib import Path

import pytest

from app.ingestion.loaders.storage_backed_loader import StorageBackedFileLoader
from app.storage.exceptions import DocumentNotFoundError
from app.storage.local_storage import LocalDocumentStorage


@pytest.fixture
def storage(tmp_path: Path) -> LocalDocumentStorage:
    (tmp_path / "physiology").mkdir()
    (tmp_path / "physiology" / "book.pdf").write_bytes(b"%PDF-1.4 physiology content")
    return LocalDocumentStorage(root=tmp_path)


def test_load_reads_content_through_storage_by_key(storage: LocalDocumentStorage):
    loader = StorageBackedFileLoader(storage=storage)

    loaded = loader.load("physiology/book.pdf")

    assert loaded.content == b"%PDF-1.4 physiology content"


def test_load_sets_filename_from_the_key(storage: LocalDocumentStorage):
    loader = StorageBackedFileLoader(storage=storage)

    loaded = loader.load("physiology/book.pdf")

    assert loaded.filename == "book.pdf"


def test_load_sets_original_path_to_the_logical_key_not_a_filesystem_path(
    storage: LocalDocumentStorage,
):
    loader = StorageBackedFileLoader(storage=storage)

    loaded = loader.load("physiology/book.pdf")

    assert loaded.original_path == "physiology/book.pdf"


def test_load_missing_key_raises_document_not_found(storage: LocalDocumentStorage):
    loader = StorageBackedFileLoader(storage=storage)

    with pytest.raises(DocumentNotFoundError):
        loader.load("physiology/missing.pdf")


def test_load_accepts_path_objects_as_well_as_strings(storage: LocalDocumentStorage):
    loader = StorageBackedFileLoader(storage=storage)

    loaded = loader.load(Path("physiology/book.pdf"))

    assert loaded.content == b"%PDF-1.4 physiology content"
