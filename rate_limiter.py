"""Rate limiter utilities for Telegram API calls."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Deque


class RollingWindowLimiter:
    """Simple rolling-window limiter (e.g., 24h window)."""

    def __init__(self, max_calls: int, window_seconds: int) -> None:
        self.max_calls = max_calls
        self.window = window_seconds
        self._timestamps: Deque[float] = deque()
        self._lock = asyncio.Lock()

    async def throttle(self) -> float:
        """Ensure we don't exceed the rate limit.

        Returns the wait time (seconds) if we had to sleep, otherwise 0.
        """

        waited = 0.0
        while True:
            async with self._lock:
                now = time.time()
                self._purge_old(now)

                if self.max_calls <= 0:
                    # Treat as unlimited
                    self._timestamps.append(now)
                    return waited

                if len(self._timestamps) < self.max_calls:
                    self._timestamps.append(now)
                    return waited

                oldest = self._timestamps[0]
                wait_for = (oldest + self.window) - now + 0.1

            if wait_for > 0:
                waited += wait_for
                await asyncio.sleep(wait_for)
            else:
                await asyncio.sleep(0.1)

    def _purge_old(self, now: float) -> None:
        window_start = now - self.window
        while self._timestamps and self._timestamps[0] < window_start:
            self._timestamps.popleft()


