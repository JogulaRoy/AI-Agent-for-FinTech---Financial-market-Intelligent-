"""Final combined Financial Intelligence contract."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.fundamentals import Fundamentals
from app.schemas.market_data import DataAgentResult
from app.schemas.news_data import NewsAnalysis
from app.schemas.risk_data import RiskAnalysis
from app.schemas.security import CanonicalSecurity
from app.schemas.technical_data import TechnicalAnalysis


class AgentRunStatus(BaseModel):
    name: str
    status: str = "pending"            # pending | running | ok | partial | failed | skipped
    message: str = ""
    duration_ms: Optional[int] = None


class ReasoningOutput(BaseModel):
    """Natural-language synthesis produced by the LLM reasoning layer."""

    available: bool = False
    model: Optional[str] = None
    company_overview: str = ""
    cross_agent_insights: str = ""
    conflicting_signals: str = ""
    overall_intelligence: str = ""
    key_risks: list[str] = Field(default_factory=list)
    classification: Optional[str] = None      # Bullish | Neutral | Bearish (system signal)
    classification_rationale: str = ""
    uncertainty_notes: str = ""
    error: Optional[str] = None
    disclaimer: str = (
        "AI-generated financial analysis and intelligence for educational purposes. "
        "Not personalised financial advice. No guarantee of future performance."
    )


class SourceRecord(BaseModel):
    label: str
    provider: str
    as_of: Optional[str] = None
    note: str = ""


class FinancialIntelligenceReport(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_query: str = ""

    security: Optional[CanonicalSecurity] = None
    data: Optional[DataAgentResult] = None
    fundamentals: Optional[Fundamentals] = None
    technical: Optional[TechnicalAnalysis] = None
    risk: Optional[RiskAnalysis] = None
    news: Optional[NewsAnalysis] = None
    reasoning: ReasoningOutput = Field(default_factory=ReasoningOutput)

    agent_status: list[AgentRunStatus] = Field(default_factory=list)
    sources: list[SourceRecord] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    overall_classification: Optional[str] = None
    disclaimer: str = (
        "This report combines rule-based quantitative analysis with an AI reasoning "
        "layer. It is financial intelligence for educational use, not investment "
        "advice, and contains no guaranteed predictions."
    )
