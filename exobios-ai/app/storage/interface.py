from abc import ABC, abstractmethod


class DocumentStorage(ABC):
    """Source-agnostic read access to stored original documents, keyed by a
    logical, portable key (e.g. "physiology/book.pdf") rather than an
    absolute filesystem path.

    Deliberately read-only for this phase: documents are placed by a human
    (Google Drive → manual download → local folder), not uploaded through
    the application, so no `write()` method exists yet — adding one only
    when an actual upload path is built avoids an unused method every
    implementation would have to carry.

    Swap `LocalDocumentStorage` for an object-storage-backed implementation
    (S3 / Cloudflare R2 / GCS / Azure Blob / MinIO) later by implementing
    this interface — no caller changes required, since every consumer
    depends only on this abstraction.
    """

    @abstractmethod
    def read(self, key: str) -> bytes: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def list(self, prefix: str | None = None) -> list[str]: ...
