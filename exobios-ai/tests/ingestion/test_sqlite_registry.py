from pathlib import Path

import pytest

from app.ingestion.exceptions import DuplicateDocument
from app.ingestion.models.document import ApprovalStatus, DocumentMetadata, DocumentType, Subject
from app.ingestion.registry.sqlite_registry import SQLiteDocumentRegistry


def _make_metadata(**overrides) -> DocumentMetadata:
    defaults = {
        "filename": "book.pdf",
        "original_path": "/tmp/book.pdf",
        "document_type": DocumentType.PDF,
        "source": "unit-test",
        "checksum": "checksum-a",
    }
    defaults.update(overrides)
    return DocumentMetadata(**defaults)


def test_initializing_creates_the_database_file(tmp_path: Path):
    db_path = tmp_path / "registry.db"

    SQLiteDocumentRegistry(db_path=db_path)

    assert db_path.is_file()


def test_initializing_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "registry.db"

    SQLiteDocumentRegistry(db_path=db_path)
    SQLiteDocumentRegistry(db_path=db_path)  # must not raise on an existing schema


def test_initializing_creates_parent_directories(tmp_path: Path):
    db_path = tmp_path / "nested" / "dir" / "registry.db"

    SQLiteDocumentRegistry(db_path=db_path)

    assert db_path.is_file()


def test_register_and_get_round_trips(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")
    metadata = _make_metadata(
        title="Guyton and Hall Textbook of Medical Physiology",
        subject=Subject.PHYSIOLOGY,
        author="John E. Hall",
        publisher="Elsevier",
        edition="14th",
        publication_year=2020,
        storage_key="physiology/book.pdf",
        approval_status=ApprovalStatus.APPROVED_FOR_POC,
        copyright_status="client-provided, not for redistribution",
        allow_image_display=False,
    )

    registry.register(metadata)
    found = registry.get(metadata.id)

    assert found == metadata


def test_data_persists_after_registry_object_is_recreated(tmp_path: Path):
    db_path = tmp_path / "registry.db"
    metadata = _make_metadata(checksum="persist-me")
    SQLiteDocumentRegistry(db_path=db_path).register(metadata)

    reopened = SQLiteDocumentRegistry(db_path=db_path)
    found = reopened.get(metadata.id)

    assert found is not None
    assert found.id == metadata.id
    assert found.checksum == "persist-me"


def test_get_returns_none_for_unknown_id(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")

    assert registry.get(_make_metadata().id) is None


def test_find_by_checksum_locates_registered_document(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")
    metadata = _make_metadata(checksum="unique-checksum")
    registry.register(metadata)

    found = registry.find_by_checksum("unique-checksum")

    assert found is not None
    assert found.id == metadata.id


def test_find_by_checksum_returns_none_when_absent(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")

    assert registry.find_by_checksum("missing") is None


def test_register_duplicate_checksum_raises_duplicate_document(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")
    first = _make_metadata(checksum="dup-checksum", filename="a.pdf")
    registry.register(first)

    second = _make_metadata(checksum="dup-checksum", filename="b.pdf")
    with pytest.raises(DuplicateDocument) as exc_info:
        registry.register(second)

    assert exc_info.value.existing_document_id == first.id
    # The duplicate attempt must not have created a second row.
    assert len(registry.list_all()) == 1


def test_update_requires_document_to_already_be_registered(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")

    with pytest.raises(KeyError):
        registry.update(_make_metadata())


def test_update_persists_changes(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")
    metadata = _make_metadata()
    registry.register(metadata)

    metadata.chunk_count = 5
    registry.update(metadata)

    assert registry.get(metadata.id).chunk_count == 5


def test_update_bumps_updated_at(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")
    metadata = _make_metadata()
    registry.register(metadata)
    original_updated_at = registry.get(metadata.id).updated_at

    metadata.page_count = 42
    registry.update(metadata)

    assert registry.get(metadata.id).updated_at >= original_updated_at


def test_list_all_returns_every_registered_document(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")
    first = _make_metadata(checksum="c1")
    second = _make_metadata(checksum="c2")
    registry.register(first)
    registry.register(second)

    ids = {doc.id for doc in registry.list_all()}

    assert ids == {first.id, second.id}


def test_list_all_filters_by_subject(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")
    registry.register(_make_metadata(checksum="c1", subject=Subject.ANATOMY))
    registry.register(_make_metadata(checksum="c2", subject=Subject.PHYSIOLOGY))

    results = registry.list_all(subject=Subject.PHYSIOLOGY)

    assert len(results) == 1
    assert results[0].subject == Subject.PHYSIOLOGY


def test_list_all_filters_by_approval_status(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")
    registry.register(_make_metadata(checksum="c1", approval_status=ApprovalStatus.PENDING))
    registry.register(
        _make_metadata(checksum="c2", approval_status=ApprovalStatus.APPROVED_FOR_POC)
    )

    results = registry.list_all(approval_status=ApprovalStatus.APPROVED_FOR_POC)

    assert len(results) == 1
    assert results[0].approval_status == ApprovalStatus.APPROVED_FOR_POC


def test_optional_textbook_fields_round_trip_as_none_when_unset(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")
    metadata = _make_metadata()  # no title/subject/author/etc supplied

    registry.register(metadata)
    found = registry.get(metadata.id)

    assert found.title is None
    assert found.subject is None
    assert found.storage_key is None
    assert found.allow_image_display is None


def test_tags_round_trip(tmp_path: Path):
    registry = SQLiteDocumentRegistry(db_path=tmp_path / "registry.db")
    metadata = _make_metadata(tags=["who", "pediatrics"])

    registry.register(metadata)

    assert registry.get(metadata.id).tags == ["who", "pediatrics"]
