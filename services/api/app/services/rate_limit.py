import time
from collections import defaultdict, deque


class SlidingWindowRateLimiter:
    """Simple in-process 60s sliding-window limiter (section 9.1 / FR
    "rate limiting"). Sufficient for the single-instance onboarding MVP;
    a shared store (e.g. Redis) would be needed for multi-instance deploys."""

    def __init__(self, limit_per_minute: int):
        self.limit = limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> bool:
        now = time.monotonic()
        window = self._hits[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.limit:
            return False
        window.append(now)
        return True


_limiter: SlidingWindowRateLimiter | None = None


def get_rate_limiter(limit_per_minute: int) -> SlidingWindowRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = SlidingWindowRateLimiter(limit_per_minute)
    return _limiter
