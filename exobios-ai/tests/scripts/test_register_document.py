import hashlib
import sys
from pathlib import Path

import pytest

# scripts/ is a standalone tool directory, not part of the installed `app`
# package (see pyproject.toml's packages.find), so it isn't importable via
# the usual "app.*" path — insert it directly, the same way
# scripts/register_document.py inserts the project root for its own imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import register_document as cli  # noqa: E402

from app.ingestion.exceptions import DuplicateDocument, UnsupportedDocumentType  # noqa: E402
from app.ingestion.models.document import ApprovalStatus, Subject  # noqa: E402
from app.ingestion.registry.in_memory_registry import InMemoryDocumentRegistry  # noqa: E402
from app.storage.local_storage import LocalDocumentStorage  # noqa: E402


@pytest.fixture
def storage_root(tmp_path: Path) -> Path:
    (tmp_path / "physiology").mkdir()
    (tmp_path / "physiology" / "book.pdf").write_bytes(b"%PDF-1.4 physiology textbook content")
    return tmp_path


def test_register_document_success(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)
    registry = InMemoryDocumentRegistry()

    metadata = cli.register_document(
        file_path=storage_root / "physiology" / "book.pdf",
        storage=storage,
        registry=registry,
        subject=Subject.PHYSIOLOGY,
        title="Guyton and Hall Textbook of Medical Physiology",
        author="John E. Hall",
        publisher="Elsevier",
        edition="14th",
        publication_year=2020,
        approval_status=ApprovalStatus.APPROVED_FOR_POC,
    )

    assert registry.get(metadata.id) == metadata
    assert metadata.title == "Guyton and Hall Textbook of Medical Physiology"
    assert metadata.subject == Subject.PHYSIOLOGY
    assert metadata.approval_status == ApprovalStatus.APPROVED_FOR_POC


def test_checksum_matches_sha256_of_file_content(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)
    file_path = storage_root / "physiology" / "book.pdf"
    expected = hashlib.sha256(file_path.read_bytes()).hexdigest()

    metadata = cli.register_document(
        file_path=file_path,
        storage=storage,
        registry=InMemoryDocumentRegistry(),
        subject=Subject.PHYSIOLOGY,
        title="Some Textbook",
    )

    assert metadata.checksum == expected


def test_storage_key_is_relative_and_portable_not_an_absolute_path(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    metadata = cli.register_document(
        file_path=storage_root / "physiology" / "book.pdf",
        storage=storage,
        registry=InMemoryDocumentRegistry(),
        subject=Subject.PHYSIOLOGY,
        title="Some Textbook",
    )

    assert metadata.storage_key == "physiology/book.pdf"
    assert not Path(metadata.storage_key).is_absolute()


def test_register_document_missing_file_raises(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)

    with pytest.raises(cli.RegistrationError):
        cli.register_document(
            file_path=storage_root / "physiology" / "missing.pdf",
            storage=storage,
            registry=InMemoryDocumentRegistry(),
            subject=Subject.PHYSIOLOGY,
            title="Some Textbook",
        )


def test_register_document_unsupported_type_raises(storage_root: Path):
    (storage_root / "physiology" / "notes.csv").write_text("a,b,c")
    storage = LocalDocumentStorage(root=storage_root)

    with pytest.raises(UnsupportedDocumentType):
        cli.register_document(
            file_path=storage_root / "physiology" / "notes.csv",
            storage=storage,
            registry=InMemoryDocumentRegistry(),
            subject=Subject.PHYSIOLOGY,
            title="Not a textbook",
        )


def test_register_document_outside_storage_root_raises(
    tmp_path_factory: pytest.TempPathFactory, storage_root: Path
):
    # A genuinely separate temp directory, not a subdirectory of storage_root
    # (storage_root is itself built from the shared `tmp_path` fixture, so
    # reusing `tmp_path` here would land "outside_dir" back inside the root).
    outside_dir = tmp_path_factory.mktemp("outside")
    outside_file = outside_dir / "book.pdf"
    outside_file.write_bytes(b"%PDF-1.4 not under the storage root")
    storage = LocalDocumentStorage(root=storage_root)

    with pytest.raises(cli.RegistrationError):
        cli.register_document(
            file_path=outside_file,
            storage=storage,
            registry=InMemoryDocumentRegistry(),
            subject=Subject.PHYSIOLOGY,
            title="Some Textbook",
        )


def test_register_document_duplicate_checksum_raises(storage_root: Path):
    storage = LocalDocumentStorage(root=storage_root)
    registry = InMemoryDocumentRegistry()
    cli.register_document(
        file_path=storage_root / "physiology" / "book.pdf",
        storage=storage,
        registry=registry,
        subject=Subject.PHYSIOLOGY,
        title="First registration",
    )

    with pytest.raises(DuplicateDocument):
        cli.register_document(
            file_path=storage_root / "physiology" / "book.pdf",
            storage=storage,
            registry=registry,
            subject=Subject.PHYSIOLOGY,
            title="Second registration attempt of the same file",
        )


def test_list_documents_filters_by_subject(storage_root: Path):
    (storage_root / "anatomy").mkdir()
    (storage_root / "anatomy" / "book.pdf").write_bytes(b"%PDF-1.4 anatomy content")
    storage = LocalDocumentStorage(root=storage_root)
    registry = InMemoryDocumentRegistry()
    cli.register_document(
        file_path=storage_root / "physiology" / "book.pdf",
        storage=storage,
        registry=registry,
        subject=Subject.PHYSIOLOGY,
        title="Physiology book",
    )
    cli.register_document(
        file_path=storage_root / "anatomy" / "book.pdf",
        storage=storage,
        registry=registry,
        subject=Subject.ANATOMY,
        title="Anatomy book",
    )

    results = cli.list_documents(registry, subject=Subject.ANATOMY)

    assert len(results) == 1
    assert results[0].title == "Anatomy book"


def test_cli_rejects_unknown_subject_choice():
    parser = cli._build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "register",
                "--file",
                "data/source_documents/physiology/book.pdf",
                "--subject",
                "astrology",
                "--title",
                "Some Textbook",
            ]
        )


def test_cli_rejects_unknown_approval_status_choice():
    parser = cli._build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "register",
                "--file",
                "data/source_documents/physiology/book.pdf",
                "--subject",
                "physiology",
                "--title",
                "Some Textbook",
                "--approval-status",
                "definitely-approved",
            ]
        )


def test_cli_register_requires_title():
    parser = cli._build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "register",
                "--file",
                "data/source_documents/physiology/book.pdf",
                "--subject",
                "physiology",
            ]
        )
