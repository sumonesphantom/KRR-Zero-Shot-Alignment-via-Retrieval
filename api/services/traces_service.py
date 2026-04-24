"""Read trace JSON files and evaluation reports. Re-reads disk on every list call."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api.bootstrap.sys_paths import (
    TRACES_DIR,
    EVAL_JUDGE_PATH,
)


def list_traces() -> list[dict]:
    if not TRACES_DIR.exists():
        return []
    out: list[dict] = []
    for p in sorted(TRACES_DIR.glob("trace_*.json")):
        try:
            with open(p, "r") as f:
                data = json.load(f)
            stat = p.stat()
            created = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            revisions = data.get("revisions") or []
            out.append({
                "id": p.stem,
                "path": str(p.relative_to(p.parents[2])),
                "query": data.get("query", ""),
                "preference": data.get("preference", ""),
                "final_style_id": data.get("final_style_id", ""),
                "n_revisions": max(len(revisions) - 1, 0),
                "created_at": created,
            })
        except (json.JSONDecodeError, OSError):
            continue
    return out


def get_trace(trace_id: str) -> dict | None:
    if ".." in trace_id or "/" in trace_id or "\\" in trace_id:
        return None
    path = TRACES_DIR / f"{trace_id}.json"
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def get_evaluation(kind: str) -> dict | None:
    path = EVAL_JUDGE_PATH if kind == "judge" else None
    if path is None or not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def evaluations_available() -> dict[str, bool]:
    return {
        "judge": EVAL_JUDGE_PATH.exists(),
    }
