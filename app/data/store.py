"""
Analysis-run history (SQLite).

Separate from the HTTP response cache: this persists the *outcome* of a full
multi-agent run so the UI can list and re-open past analyses without hitting any
provider again. The schema is intentionally plain so it can move to PostgreSQL
when a backend is introduced.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from app.config.settings import settings
from app.schemas.intelligence import FinancialIntelligenceReport

_LOCK = threading.Lock()
_DB_PATH = settings.project_root / ".cache" / "analysis_runs.db"


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at      REAL NOT NULL,
            user_query      TEXT NOT NULL,
            company_name    TEXT,
            symbol          TEXT,
            exchange        TEXT,
            classification  TEXT,
            report_json     TEXT NOT NULL
        )
        """
    )
    return conn


class RunSummary:
    __slots__ = ("id", "created_at", "user_query", "company_name", "symbol",
                 "exchange", "classification")

    def __init__(self, row: tuple):
        (self.id, self.created_at, self.user_query, self.company_name,
         self.symbol, self.exchange, self.classification) = row

    @property
    def label(self) -> str:
        name = self.company_name or self.user_query
        cls = f" · {self.classification}" if self.classification else ""
        return f"{name} ({self.symbol or '?'}){cls}"


def save_run(report: FinancialIntelligenceReport, when: Optional[float] = None) -> int:
    sec = report.security
    with _LOCK, _connect() as conn:
        cur = conn.execute(
            "INSERT INTO analysis_runs "
            "(created_at, user_query, company_name, symbol, exchange, classification, report_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                when if when is not None else time.time(),
                report.user_query,
                sec.company_name if sec else None,
                sec.symbol if sec else None,
                sec.exchange if sec else None,
                report.overall_classification,
                report.model_dump_json(),
            ),
        )
        return int(cur.lastrowid)


def list_runs(limit: int = 15) -> list[RunSummary]:
    with _LOCK, _connect() as conn:
        rows = conn.execute(
            "SELECT id, created_at, user_query, company_name, symbol, exchange, classification "
            "FROM analysis_runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [RunSummary(row) for row in rows]


def load_run(run_id: int) -> Optional[FinancialIntelligenceReport]:
    with _LOCK, _connect() as conn:
        row = conn.execute(
            "SELECT report_json FROM analysis_runs WHERE id = ?", (run_id,)
        ).fetchone()
    if not row:
        return None
    try:
        return FinancialIntelligenceReport.model_validate(json.loads(row[0]))
    except Exception:  # noqa: BLE001 - schema drift on old rows
        return None


def delete_run(run_id: int) -> None:
    with _LOCK, _connect() as conn:
        conn.execute("DELETE FROM analysis_runs WHERE id = ?", (run_id,))


def clear_runs() -> None:
    with _LOCK, _connect() as conn:
        conn.execute("DELETE FROM analysis_runs")
