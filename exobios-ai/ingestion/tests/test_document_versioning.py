"""Tests for the ingestion-side half of the document-versioning foundation
(services/upload.py::find_active_versions/mark_superseded, wired through
loaders/loader.py::run()). See the 2026-08 audit's Priority 8."""

from types import SimpleNamespace

import pytest

pytest.importorskip("supabase", reason="services.upload pulls in boto3/supabase at import time")

import services.upload as upload_module  # noqa: E402
from schemas.document_schema import DocumentStatus  # noqa: E402


class _FakeSelectQuery:
    def __init__(self, rows):
        self._rows = rows
        self._filters = {}

    def select(self, *_a):
        return self

    def eq(self, column, value):
        self._filters[column] = value
        return self

    def neq(self, column, value):
        self._filters[f"neq:{column}"] = value
        return self

    def execute(self):
        matching = [
            r for r in self._rows
            if r.get("logical_document_key") == self._filters.get("logical_document_key")
            and r.get("is_active") == self._filters.get("is_active")
            and r.get("status") == self._filters.get("status")
            and r.get("document_id") != self._filters.get("neq:document_id")
        ]
        return SimpleNamespace(data=[{"document_id": r["document_id"]} for r in matching])


def test_find_active_versions_returns_matching_completed_active_rows(monkeypatch):
    rows = [
        {"document_id": "old-1", "logical_document_key": "textbook", "is_active": True, "status": "COMPLETED"},
        {"document_id": "unrelated", "logical_document_key": "other-doc", "is_active": True, "status": "COMPLETED"},
    ]

    class _Client:
        def table(self, name):
            return _FakeSelectQuery(rows)

    monkeypatch.setattr(upload_module, "supabase_client", _Client())

    result = upload_module.find_active_versions("textbook", exclude_document_id="new-1")

    assert result == ["old-1"]


def test_find_active_versions_excludes_the_current_document_id(monkeypatch):
    rows = [{"document_id": "doc-1", "logical_document_key": "textbook", "is_active": True, "status": "COMPLETED"}]

    class _Client:
        def table(self, name):
            return _FakeSelectQuery(rows)

    monkeypatch.setattr(upload_module, "supabase_client", _Client())

    # Excluding itself (a retry/re-run of the same document_id) must not
    # treat the document as superseding itself.
    result = upload_module.find_active_versions("textbook", exclude_document_id="doc-1")

    assert result == []


def test_find_active_versions_ignores_incomplete_or_inactive_rows(monkeypatch):
    rows = [
        {"document_id": "failed-1", "logical_document_key": "textbook", "is_active": True, "status": "FAILED"},
        {"document_id": "already-superseded", "logical_document_key": "textbook", "is_active": False, "status": "COMPLETED"},
    ]

    class _Client:
        def table(self, name):
            return _FakeSelectQuery(rows)

    monkeypatch.setattr(upload_module, "supabase_client", _Client())

    result = upload_module.find_active_versions("textbook", exclude_document_id="new-1")

    assert result == []


def test_find_active_versions_returns_empty_list_on_supabase_error(monkeypatch):
    class _BoomClient:
        def table(self, name):
            raise ConnectionError("supabase unreachable")

    monkeypatch.setattr(upload_module, "supabase_client", _BoomClient())

    assert upload_module.find_active_versions("textbook", exclude_document_id="new-1") == []


def test_mark_superseded_sets_inactive_and_records_successor(monkeypatch):
    class _Query:
        def __init__(self):
            self.payload = None
            self.filter_column = None
            self.filter_value = None

        def update(self, payload):
            self.payload = payload
            return self

        def eq(self, column, value):
            self.filter_column, self.filter_value = column, value
            return self

        def execute(self):
            return None

    query = _Query()

    class _Client:
        def table(self, name):
            return query

    monkeypatch.setattr(upload_module, "supabase_client", _Client())

    result = upload_module.mark_superseded("old-doc", superseded_by="new-doc")

    assert result is True
    assert query.payload == {"is_active": False, "superseded_by": "new-doc"}
    assert (query.filter_column, query.filter_value) == ("document_id", "old-doc")
