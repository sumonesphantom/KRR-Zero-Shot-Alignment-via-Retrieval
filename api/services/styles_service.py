"""Load and cache style cards. Read-only."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from api.bootstrap.sys_paths import STYLE_CARDS_PATH


_cache: list[dict] | None = None
_lock = Lock()


def load_cards(force: bool = False) -> list[dict]:
    global _cache
    with _lock:
        if _cache is not None and not force:
            return _cache
        if not STYLE_CARDS_PATH.exists():
            raise FileNotFoundError(f"style cards file not found: {STYLE_CARDS_PATH}")
        cards: list[dict] = []
        with open(STYLE_CARDS_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    cards.append(json.loads(line))
        _cache = cards
        return cards


def get_card(style_id: str) -> dict | None:
    for c in load_cards():
        if c.get("id") == style_id:
            return c
    return None
