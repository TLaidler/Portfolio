from __future__ import annotations

import json
import time
from pathlib import Path
from threading import Lock
from typing import Any


class JSONFileCache:
    """Cache simples em arquivo JSON com TTL por chave. Thread-safe."""

    def __init__(self, path: Path, default_ttl: int = 86400) -> None:
        self.path = Path(path)
        self.default_ttl = default_ttl
        self._lock = Lock()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, key: str) -> tuple[Any | None, bool]:
        """Retorna (valor, is_stale). valor=None se não existe; is_stale=True se expirado."""
        with self._lock:
            data = self._load()
            entry = data.get(key)
            if not entry:
                return None, False
            ttl = entry.get("ttl", self.default_ttl)
            age = time.time() - entry.get("fetched_at", 0)
            is_stale = age > ttl
            return entry.get("value"), is_stale

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        with self._lock:
            data = self._load()
            data[key] = {
                "value": value,
                "fetched_at": time.time(),
                "ttl": ttl if ttl is not None else self.default_ttl,
            }
            self._save(data)
