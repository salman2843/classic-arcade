"""Persistence with a browser backend and a safe in-memory fallback.

The browser passes ``js.localStorage`` into ``HighScores``. Tests, desktop dev
runs and private-mode browsers pass nothing (or a failing object), and everything
keeps working for the session without persisting.
"""

from __future__ import annotations

import json


class HighScores:
    KEY = "classic-games.v1"

    def __init__(self, backend=None) -> None:
        self._backend = backend
        self._data: dict[str, object] = {}
        self._load()

    def _load(self) -> None:
        if self._backend is None:
            return
        try:
            raw = self._backend.getItem(self.KEY)
            if raw:
                parsed = json.loads(str(raw))
                if isinstance(parsed, dict):
                    self._data = parsed
        except Exception:
            self._data = {}

    def get(self, key: str, default=0):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self._save()

    def _save(self) -> None:
        if self._backend is None:
            return
        try:
            self._backend.setItem(self.KEY, json.dumps(self._data))
        except Exception:
            pass
