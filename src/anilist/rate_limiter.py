"""Token bucket rate limiter for the AniList API (~90 req/min)."""

from __future__ import annotations

import time
import threading


class RateLimiter:
    """Token bucket rate limiter — thread-safe.

    AniList allows ~90 requests per minute. This limiter defaults to
    80 req/min to stay safely under the cap, with burst support.
    """

    def __init__(self, rate: float = 80.0, burst: int = 10) -> None:
        """
        Args:
            rate: Sustained requests per minute.
            burst: Maximum burst size (instantaneous requests).
        """
        self._rate = rate / 60.0  # tokens per second
        self._burst = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a token is available."""
        with self._lock:
            while self._tokens < 1.0:
                self._refill()
                if self._tokens < 1.0:
                    sleep_time = (1.0 - self._tokens) / self._rate
                    time.sleep(sleep_time)
            self._tokens -= 1.0

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._last_refill = now

    @property
    def available(self) -> float:
        """Current number of available tokens."""
        with self._lock:
            self._refill()
            return self._tokens
