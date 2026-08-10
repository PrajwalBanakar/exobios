from pathlib import Path

import pytest

from app.storage.exceptions import DocumentNotFoundError, InvalidStorageKeyError
from app.storage.local_storage import LocalDocumentStorage


@pytest.fixture
def storage_root(tmp_path: Path) -> Path:
    (tmp_path / "anatomy").mkdir()
    (tmp_path / "physiology").mkdir()
    (tmp_path / "anatomy" / "book.pdf").write_bytes(b"%PDF-1.4 anatomy content")
    (tmp_path / "physiology" / "book.pdf").write_bytes(b"%PDF-1.4 physiology content")
    return tmp_path


def test_read_returns_exact_file_bytes(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    content = storage.read("anatomy/book.pdf")

    assert content == b"%PDF-1.4 anatomy content"


def test_read_missing_file_raises_document_not_found(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    with pytest.raises(DocumentNotFoundError):
        storage.read("anatomy/missing.pdf")


def test_exists_true_for_present_file(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    assert storage.exists("physiology/book.pdf") is True


def test_exists_false_for_missing_file(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    assert storage.exists("physiology/missing.pdf") is False


def test_exists_false_for_path_traversal_key(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    assert storage.exists("../secret.env") is False


def test_list_returns_all_files_as_relative_posix_keys(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    keys = storage.list()

    assert keys == ["anatomy/book.pdf", "physiology/book.pdf"]


def test_list_with_prefix_scopes_to_subject_folder(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    keys = storage.list(prefix="anatomy")

    assert keys == ["anatomy/book.pdf"]


def test_list_returns_empty_for_nonexistent_prefix(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    assert storage.list(prefix="pharmacology") == []


def test_nested_subject_folder_keys_supported(storage_root: Path):
    (storage_root / "biochemistry").mkdir()
    (storage_root / "biochemistry" / "book.pdf").write_bytes(b"%PDF-1.4 biochem content")
    storage = LocalDocumentStorage(root=storage_root)

    assert storage.read("biochemistry/book.pdf") == b"%PDF-1.4 biochem content"
    assert "biochemistry/book.pdf" in storage.list()


@pytest.mark.parametrize(
    "malicious_key",
    [
        "../../secret.env",
        "../outside.pdf",
        "anatomy/../../secret.env",
    ],
)
def test_path_traversal_is_rejected(storage_root: Path, malicious_key: str):
    storage = LocalDocumentStorage(root=storage_root)

    with pytest.raises(InvalidStorageKeyError):
        storage.read(malicious_key)


def test_absolute_key_is_rejected(storage_root: Path, tmp_path: Path):
    outside_file = tmp_path.parent / "outside.pdf"
    storage = LocalDocumentStorage(root=storage_root)

    with pytest.raises(InvalidStorageKeyError):
        storage.read(str(outside_file))


def test_blank_key_is_rejected(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    with pytest.raises(InvalidStorageKeyError):
        storage.read("")


def test_root_confinement_survives_symlink_style_dotdot_within_root(storage_root: Path):
    # "anatomy/../physiology/book.pdf" stays inside root after resolution —
    # confinement is about the *resolved* destination, not merely rejecting
    # every ".." token outright.
    storage = LocalDocumentStorage(root=storage_root)

    assert storage.read("anatomy/../physiology/book.pdf") == b"%PDF-1.4 physiology content"


def test_read_does_not_mutate_the_source_file(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)
    original = (storage_root / "anatomy" / "book.pdf").read_bytes()

    storage.read("anatomy/book.pdf")
    storage.read("anatomy/book.pdf")

    assert (storage_root / "anatomy" / "book.pdf").read_bytes() == original


def test_root_property_is_resolved_absolute_path(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    assert storage.root.is_absolute()
    assert storage.root == storage_root.resolve()
