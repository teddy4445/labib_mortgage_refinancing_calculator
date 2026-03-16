from __future__ import annotations

import hashlib
from collections import defaultdict, deque
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any

import httpx
from fastapi import HTTPException, status

from backend.app.schemas import MortgageInput, UserCreate


class CaptchaManager:
    def __init__(self, *, secret_key: str | None, verify_url: str) -> None:
        self._secret_key = secret_key
        self._verify_url = verify_url

    async def verify(self, token: str | None, remote_ip: str | None = None) -> bool:
        if not self._secret_key:
            return True
        if not token:
            return False

        payload = {"secret": self._secret_key, "response": token}
        if remote_ip:
            payload["remoteip"] = remote_ip

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self._verify_url, data=payload)
            response.raise_for_status()
            data = response.json()
        return bool(data.get("success"))


class ValidationManager:
    def validate_registration(self, payload: UserCreate) -> None:
        if " " in payload.username:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username cannot contain spaces.")
        if payload.phone_number and len(payload.phone_number) < 9:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Phone number is too short.")

    def validate_mortgage(self, payload: MortgageInput) -> None:
        if not payload.tracks:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one track is required.")
        if any(track.outstanding_balance <= 0 for track in payload.tracks):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Each track must have a positive outstanding balance.",
            )


class RateLimitManager:
    def __init__(self, *, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = timedelta(seconds=window_seconds)
        self._requests: dict[str, deque[datetime]] = defaultdict(deque)

    def _prune(self, bucket: deque[datetime], now: datetime) -> None:
        while bucket and now - bucket[0] > self._window:
            bucket.popleft()

    def build_key(self, parts: Iterable[Any]) -> str:
        raw = ":".join(str(part) for part in parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def check(self, *, key: str) -> None:
        now = datetime.utcnow()
        bucket = self._requests[key]
        self._prune(bucket, now)
        if len(bucket) >= self._limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests.")
        bucket.append(now)
