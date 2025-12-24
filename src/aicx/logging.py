"""Verbose audit logging."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any


_is_verbose = False


def configure_logging(verbose: bool) -> None:
    global _is_verbose
    _is_verbose = verbose


def log_event(event: str, *, payload: dict[str, Any] | None = None, round_index: int | None = None, model: str | None = None) -> None:
    if not _is_verbose:
        return

    record = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "round": round_index,
        "model": model,
        "payload": payload or {},
    }
    sys.stderr.write(json.dumps(record, sort_keys=True) + "\n")
