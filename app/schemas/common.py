"""Shared schema fragments used across agents."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class DataProvenance(BaseModel):
    """Where a piece of data came from and how fresh it is."""

    provider: str
    endpoint: Optional[str] = None
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    as_of: Optional[str] = None          # the data's own timestamp / period label
    currency: Optional[str] = None
    frequency: Optional[str] = None      # e.g. "daily", "annual", "ttm"
    adjusted: Optional[bool] = None
    note: Optional[str] = None

    def freshness_label(self) -> str:
        if not self.as_of:
            return "unknown"
        return str(self.as_of)


class AgentError(BaseModel):
    """A non-fatal problem recorded by a node so the run can continue."""

    agent: str
    message: str
    severity: str = "warning"           # "warning" | "error"
