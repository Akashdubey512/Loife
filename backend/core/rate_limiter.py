import time
import threading
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status

from backend.core.config import settings

class InMemoryRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter.

    Note on Architecture: In-memory rate limiting is process-local. In multi-worker
    or multi-container production deployments, limits are tracked per process;
    for distributed multi-replica synchronization, a shared Redis backend should be
    configured using the existing REDIS_URL.
    """
    def __init__(
        self,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
        enabled: Optional[bool] = None
    ):
        self._lock = threading.Lock()
        self._records: Dict[str, List[float]] = {}
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.enabled = enabled

    def _get_max_requests(self) -> int:
        return self.max_requests if self.max_requests is not None else settings.AUTH_RATE_LIMIT_MAX_REQUESTS

    def _get_window_seconds(self) -> int:
        return self.window_seconds if self.window_seconds is not None else settings.AUTH_RATE_LIMIT_WINDOW_SECONDS

    def _is_enabled(self) -> bool:
        return self.enabled if self.enabled is not None else settings.AUTH_RATE_LIMIT_ENABLED

    def _get_client_identifier(self, request: Request) -> str:
        # Prioritize socket client host to prevent untrusted header spoofing
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    def check(self, request: Request) -> None:
        if not self._is_enabled():
            return

        client_id = self._get_client_identifier(request)
        max_req = self._get_max_requests()
        window = self._get_window_seconds()
        now = time.time()
        cutoff = now - window

        with self._lock:
            history = self._records.get(client_id, [])
            # Prune timestamps outside the sliding window
            history = [ts for ts in history if ts > cutoff]

            if len(history) >= max_req:
                retry_after = int(history[0] + window - now) + 1
                self._records[client_id] = history
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many authentication attempts. Please try again later.",
                    headers={"Retry-After": str(max(1, retry_after))}
                )

            history.append(now)
            self._records[client_id] = history

    def reset(self) -> None:
        """Clears all in-memory rate-limiting records (used for deterministic testing)."""
        with self._lock:
            self._records.clear()

auth_rate_limiter = InMemoryRateLimiter()

def check_auth_rate_limit(request: Request) -> None:
    auth_rate_limiter.check(request)
