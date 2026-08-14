import pytest

from core.retry import retry_with_backoff


def test_succeeds_first_try_without_sleeping(monkeypatch):
    monkeypatch.setattr("core.retry.time.sleep", lambda s: (_ for _ in ()).throw(AssertionError("should not sleep")))
    assert retry_with_backoff(lambda: 42) == 42


def test_retries_retryable_failure_then_succeeds(monkeypatch):
    monkeypatch.setattr("core.retry.time.sleep", lambda s: None)
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise ConnectionError("transient")
        return "ok"

    assert retry_with_backoff(flaky, max_attempts=3) == "ok"
    assert calls["n"] == 2


def test_exhausts_attempts_and_raises_last_error(monkeypatch):
    monkeypatch.setattr("core.retry.time.sleep", lambda s: None)

    def always_fails():
        raise ConnectionError("still down")

    with pytest.raises(ConnectionError):
        retry_with_backoff(always_fails, max_attempts=3)


def test_non_retryable_error_raises_immediately_without_retrying(monkeypatch):
    monkeypatch.setattr("core.retry.time.sleep", lambda s: (_ for _ in ()).throw(AssertionError("should not sleep/retry")))
    calls = {"n": 0}

    def fails_once():
        calls["n"] += 1
        raise ValueError("not retryable")

    with pytest.raises(ValueError):
        retry_with_backoff(fails_once, max_attempts=3, is_retryable=lambda e: isinstance(e, ConnectionError))

    assert calls["n"] == 1
