"""Tests for the ingestion status lifecycle (PENDING -> PROCESSING ->
COMPLETED/FAILED) added in services/upload.py::update_document_status and
wired through loaders/loader.py::run(). See the 2026-08 audit's Priority 7."""

import pytest

pytest.importorskip("supabase", reason="services.upload pulls in boto3/supabase at import time")

import services.upload as upload_module  # noqa: E402
from schemas.document_schema import DocumentStatus  # noqa: E402


class _FakeQuery:
    def __init__(self, recorder, table_name):
        self._recorder = recorder
        self._table_name = table_name
        self._payload = None

    def update(self, payload):
        self._payload = payload
        return self

    def eq(self, column, value):
        self._recorder.append((self._table_name, self._payload, column, value))
        return self

    def execute(self):
        return None


class _FakeSupabaseClient:
    def __init__(self):
        self.calls = []

    def table(self, name):
        return _FakeQuery(self.calls, name)


def test_update_document_status_writes_status_and_clears_error_on_success(monkeypatch):
    fake_client = _FakeSupabaseClient()
    monkeypatch.setattr(upload_module, "supabase_client", fake_client)

    result = upload_module.update_document_status("doc-1", DocumentStatus.COMPLETED)

    assert result is True
    table_name, payload, column, value = fake_client.calls[0]
    assert table_name == "documents"
    assert payload == {"status": "COMPLETED", "error_message": None}
    assert (column, value) == ("document_id", "doc-1")


def test_update_document_status_records_failure_reason(monkeypatch):
    fake_client = _FakeSupabaseClient()
    monkeypatch.setattr(upload_module, "supabase_client", fake_client)

    upload_module.update_document_status("doc-1", DocumentStatus.FAILED, error_message="embedding failed after 4 attempts")

    _, payload, _, _ = fake_client.calls[0]
    assert payload["status"] == "FAILED"
    assert payload["error_message"] == "embedding failed after 4 attempts"


def test_update_document_status_truncates_long_error_messages(monkeypatch):
    fake_client = _FakeSupabaseClient()
    monkeypatch.setattr(upload_module, "supabase_client", fake_client)

    huge_message = "x" * 5000
    upload_module.update_document_status("doc-1", DocumentStatus.FAILED, error_message=huge_message)

    _, payload, _, _ = fake_client.calls[0]
    assert len(payload["error_message"]) == upload_module._MAX_ERROR_MESSAGE_LENGTH


def test_update_document_status_returns_false_and_reports_on_supabase_error(monkeypatch):
    class _BoomClient:
        def table(self, name):
            raise ConnectionError("supabase unreachable")

    monkeypatch.setattr(upload_module, "supabase_client", _BoomClient())

    assert upload_module.update_document_status("doc-1", DocumentStatus.FAILED, error_message="x") is False


def test_document_status_enum_matches_migration_check_constraint():
    # ingestion/supabase/migrations/20260814010000_*.sql's CHECK constraint
    # lists these four literals — keep them in sync.
    assert {s.value for s in DocumentStatus} == {"PENDING", "PROCESSING", "COMPLETED", "FAILED"}
