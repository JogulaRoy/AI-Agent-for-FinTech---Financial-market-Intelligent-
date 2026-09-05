"""
Thin command-line entry point for the multi-agent system (debug / headless use).

The primary interface is the Streamlit dashboard:

    streamlit run app/streamlit_app.py

This CLI just runs the same LangGraph orchestrator and prints a summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.orchestrator.graph import run_analysis


def main() -> None:
    parser = argparse.ArgumentParser(description="Financial Market Intelligence (CLI)")
    parser.add_argument("query", nargs="?", help="Company name or ticker (e.g. 'TCS')")
    parser.add_argument("--period", default="5y", help="History window: 1y,2y,5y,10y,max")
    parser.add_argument("--news-days", type=int, default=7)
    parser.add_argument("--json", action="store_true", help="Emit the full report as JSON")
    args = parser.parse_args()

    query = args.query or input("Enter a company name or ticker: ").strip()
    if not query:
        print("Nothing to analyse.")
        return

    report = run_analysis(query, period=args.period, news_hours=args.news_days * 24)

    if args.json:
        print(report.model_dump_json(indent=2))
        return

    sec = report.security
    print("\n" + "=" * 64)
    if sec:
        print(f"{sec.company_name}  ({sec.symbol} · {sec.exchange or 'n/a'} · {sec.currency or 'n/a'})")
    print(f"System classification: {report.overall_classification}")
    print("=" * 64)

    for status in report.agent_status:
        print(f"  [{status.status:8}] {status.name:18} {status.message}")

    if report.data:
        q = report.data.quote
        print(f"\nPrice: {q.price} {q.currency}  ({(q.change_percent or 0) * 100:+.2f}%)")
        print(f"Financial health: {report.data.fundamentals.health.classification} "
              f"({report.data.fundamentals.health.score})")
    if report.technical:
        print(f"Technical signal: {report.technical.overall_signal}")
    if report.risk:
        print(f"Risk: {report.risk.classification.level} "
              f"(score {report.risk.classification.score})")
    if report.news:
        print(f"News sentiment: {report.news.sentiment.overall_sentiment} "
              f"({report.news.articles_analyzed} articles)")

    print("\n--- AI Financial Intelligence ---")
    print(report.reasoning.overall_intelligence or "(unavailable)")
    if report.reasoning.conflicting_signals:
        print("\nConflicting signals:", report.reasoning.conflicting_signals)

    print("\n" + report.disclaimer)


if __name__ == "__main__":
    main()
