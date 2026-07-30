import pytest

from app.ingestion.models.document import DocumentMetadata, DocumentType
from app.ingestion.registry.in_memory_registry import InMemoryDocumentRegistry


def _make_metadata(**overrides) -> DocumentMetadata:
    defaults = {
        "filename": "a.txt",
        "original_path": "/tmp/a.txt",
        "document_type": DocumentType.TXT,
        "source": "unit-test",
        "checksum": "checksum-a",
    }
    defaults.update(overrides)
    return DocumentMetadata(**defaults)


def test_register_and_get_round_trips():
    registry = InMemoryDocumentRegistry()
    metadata = _make_metadata()

    registry.register(metadata)

    assert registry.get(metadata.id) == metadata


def test_get_returns_none_for_unknown_id():
    registry = InMemoryDocumentRegistry()

    assert registry.get(_make_metadata().id) is None


def test_find_by_checksum_locates_registered_document():
    registry = InMemoryDocumentRegistry()
    metadata = _make_metadata(checksum="unique-checksum")
    registry.register(metadata)

    found = registry.find_by_checksum("unique-checksum")

    assert found is not None
    assert found.id == metadata.id


def test_find_by_checksum_returns_none_when_absent():
    registry = InMemoryDocumentRegistry()

    assert registry.find_by_checksum("missing") is None


def test_update_requires_document_to_already_be_registered():
    registry = InMemoryDocumentRegistry()

    with pytest.raises(KeyError):
        registry.update(_make_metadata())


def test_update_persists_changes():
    registry = InMemoryDocumentRegistry()
    metadata = _make_metadata()
    registry.register(metadata)

    metadata.chunk_count = 5
    registry.update(metadata)

    assert registry.get(metadata.id).chunk_count == 5


def test_list_all_returns_every_registered_document():
    registry = InMemoryDocumentRegistry()
    first = _make_metadata(checksum="c1")
    second = _make_metadata(checksum="c2")
    registry.register(first)
    registry.register(second)

    ids = {doc.id for doc in registry.list_all()}

    assert ids == {first.id, second.id}
