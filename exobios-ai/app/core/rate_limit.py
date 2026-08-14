"""In-process, fixed-window rate limiter.

Deliberately not backed by Redis or any shared store: this service runs as
a single process today (see app/Dockerfile's note on why --workers stays at
1 — the graph/service singletons are constructed once at import time), so a
per-process in-memory limiter enforces the real limit correctly as-is.

Production limitation: if this service is ever scaled to multiple
processes/instances (multiple containers, or --workers > 1), each one
enforces its OWN window independently — N instances effectively multiply
the configured limit by N, since they don't share state. At that point,
enforcement belongs at the gateway/load-balancer layer (or this limiter
needs a shared backing store, e.g. Redis) — noted here rather than solved
preemptively, since introducing Redis for a single-instance deployment
would be exactly the kind of unnecessary infrastructure this project's
current stage doesn't need yet.
"""

import threading
import time

from core.exceptions import RateLimitExceededError


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        # key -> (window_start_epoch_seconds, count_in_window)
        self._windows: dict[str, tuple[float, int]] = {}

    def check(self, key: str) -> None:
        """Raises RateLimitExceededError if `key` has exceeded the limit for
        the current window; otherwise records this call and returns."""
        now = time.monotonic()
        with self._lock:
            window_start, count = self._windows.get(key, (now, 0))
            if now - window_start >= self.window_seconds:
                window_start, count = now, 0

            if count >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - window_start)))
                raise RateLimitExceededError(
                    f"rate limit exceeded: {self.max_requests} requests per {self.window_seconds}s",
                    retry_after_seconds=retry_after,
                )

            self._windows[key] = (window_start, count + 1)
