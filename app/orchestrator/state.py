"""Shared state for the LangGraph financial-analysis run."""

from __future__ import annotations

import operator
from typing import Annotated, Optional, TypedDict

from app.schemas.fundamentals import Fundamentals
from app.schemas.intelligence import AgentRunStatus
from app.schemas.market_data import DataAgentResult
from app.schemas.news_data import NewsAnalysis
from app.schemas.risk_data import RiskAnalysis
from app.schemas.security import CanonicalSecurity
from app.schemas.technical_data import TechnicalAnalysis
from app.schemas.intelligence import ReasoningOutput


class FinancialAnalysisState(TypedDict, total=False):
    # inputs
    user_query: str
    period: str
    news_hours: int

    # progressive results
    security: Optional[CanonicalSecurity]
    market_data: Optional[DataAgentResult]
    fundamentals: Optional[Fundamentals]
    technical_analysis: Optional[TechnicalAnalysis]
    risk_analysis: Optional[RiskAnalysis]
    news_analysis: Optional[NewsAnalysis]
    financial_reasoning: Optional[ReasoningOutput]
    overall_classification: Optional[str]

    # accumulated across (possibly parallel) nodes
    errors: Annotated[list[str], operator.add]
    agent_status: Annotated[list[AgentRunStatus], operator.add]
    sources: Annotated[list[str], operator.add]
