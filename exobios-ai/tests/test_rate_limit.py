"""Rate limiting tests. tests/conftest.py disables the limiter by default
(RATE_LIMIT__ENABLED=false) so the rest of the suite's many /analyze calls
don't trip it — these tests explicitly re-enable it and swap in a small,
fast-to-exhaust RateLimiter instance for the duration of each test."""

import uuid

from api import dependencies as dependencies_module
from config.settings import settings
from core.rate_limit import RateLimiter


def _body() -> dict:
    return {"assessmentId": str(uuid.uuid4()), "patientId": str(uuid.uuid4()), "symptoms": []}


def test_rate_limiter_unit_allows_up_to_the_limit_then_blocks():
    from core.exceptions import RateLimitExceededError

    limiter = RateLimiter(max_requests=3, window_seconds=60)
    limiter.check("key-a")
    limiter.check("key-a")
    limiter.check("key-a")
    try:
        limiter.check("key-a")
        assert False, "4th call within the window should have raised"
    except RateLimitExceededError as e:
        assert e.status_code == 429
        assert e.headers["Retry-After"]


def test_rate_limiter_unit_tracks_keys_independently():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter.check("key-a")  # consumes key-a's only slot
    limiter.check("key-b")  # independent budget — must not raise


def test_analyze_returns_429_with_retry_after_once_limit_exceeded(client, api_key, monkeypatch):
    monkeypatch.setattr(settings.rate_limit, "enabled", True)
    monkeypatch.setattr(dependencies_module, "_analyze_limiter", RateLimiter(max_requests=2, window_seconds=60))

    headers = {"X-Api-Key": api_key}
    r1 = client.post("/analyze", json=_body(), headers=headers)
    r2 = client.post("/analyze", json=_body(), headers=headers)
    r3 = client.post("/analyze", json=_body(), headers=headers)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429
    assert "Retry-After" in r3.headers
    body = r3.json()
    assert body["error_code"] == "rate_limit_exceeded"
    assert "request_id" in body


def test_rate_limit_is_scoped_per_api_key_not_global(client, api_key, monkeypatch):
    monkeypatch.setattr(settings.rate_limit, "enabled", True)
    monkeypatch.setattr(dependencies_module, "_analyze_limiter", RateLimiter(max_requests=1, window_seconds=60))

    r1 = client.post("/analyze", json=_body(), headers={"X-Api-Key": api_key})
    assert r1.status_code == 200

    # A different (here: invalid) key must not share the first key's budget —
    # it gets its own 401 from auth, not a 429 from an exhausted shared bucket.
    r2 = client.post("/analyze", json=_body(), headers={"X-Api-Key": "some-other-key"})
    assert r2.status_code == 401


def test_invalid_api_key_rejected_before_touching_rate_limiter(client, monkeypatch):
    monkeypatch.setattr(settings.rate_limit, "enabled", True)
    monkeypatch.setattr(dependencies_module, "_analyze_limiter", RateLimiter(max_requests=1, window_seconds=60))

    # Exhaust the (shared, since no valid key is ever used here) limiter budget
    # with invalid-key requests — they must all still 401, never 429, because
    # verify_api_key runs first and rejects before check_rate_limit runs.
    for _ in range(3):
        r = client.post("/analyze", json=_body(), headers={"X-Api-Key": "wrong"})
        assert r.status_code == 401


def test_rate_limit_disabled_by_default_in_tests(client, api_key):
    # Sanity check that the default test environment (RATE_LIMIT__ENABLED=false,
    # set in conftest.py) really does disable enforcement — many other tests
    # in this suite depend on that being true.
    for _ in range(5):
        r = client.post("/analyze", json=_body(), headers={"X-Api-Key": api_key})
        assert r.status_code == 200


def test_health_endpoints_are_never_rate_limited(client, monkeypatch):
    monkeypatch.setattr(settings.rate_limit, "enabled", True)
    monkeypatch.setattr(dependencies_module, "_analyze_limiter", RateLimiter(max_requests=1, window_seconds=60))

    for _ in range(10):
        assert client.get("/health").status_code == 200
        assert client.get("/health/ready").status_code in (200, 503)
