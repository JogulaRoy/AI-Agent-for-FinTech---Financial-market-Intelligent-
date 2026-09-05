# Agentic AI System for Financial Market Intelligence

A multi-agent financial-intelligence system. Enter a company name or ticker once
("TCS", "Tata Consultancy Services", "AAPL", "Apple"); an **orchestrator**
resolves the security, collects reliable data through a provider abstraction,
runs four specialised agents, and an **LLM reasoning layer** synthesises the
evidence into an integrated report shown in a Streamlit dashboard.

> Financial intelligence for educational use. **Not investment advice.**
> No guaranteed predictions.

---

## Architecture

```
User
 └─ Streamlit UI (app/streamlit_app.py)
     └─ LangGraph Orchestrator (app/orchestrator/)
         ├─ Stock Resolver        → CanonicalSecurity {name, symbol, exchange, country, currency, ISIN, provider ids}
         ├─ Data Agent            → profile + quote + OHLCV history + fundamentals + financial-health score
         │    └─ Provider Manager (primary + fallback, normalise, validate, cache, record source & freshness)
         │         ├─ FMP  ├─ Twelve Data  ├─ EODHD  └─ yfinance (fallback, e.g. Indian equities)
         ├─ Technical Agent  ┐
         ├─ Risk Agent       ├─ run in parallel on the Data Agent's normalized history
         └─ News Agent       ┘
         └─ Reasoning Agent (LLM)  → synthesis, cross-agent insight, conflicting signals, classification
     └─ Final Financial Intelligence Report (13 sections)
```

Shared state is a single typed object (`app/orchestrator/state.py`); every node
records its status and errors so one failing component never crashes the app.

## Project layout

```
app/
├── agents/         data / technical / news / risk / reasoning agents
├── analysis/       fundamentals health scoring, benchmarks
├── config/         settings (env-driven, no hardcoded secrets)
├── data/
│   ├── providers/  base + eodhd + fmp + twelve_data + yfinance_provider
│   ├── provider_manager.py   selection, fallback, error/rate-limit handling
│   ├── resolver.py           dynamic security resolution (no hardcoded ticker maps)
│   ├── normalizer.py  validator.py  cache.py (SQLite TTL)
├── llm/            provider-agnostic client (gemini implemented)
├── orchestrator/   LangGraph state / nodes / graph
├── reporting/      13-section Markdown report renderer
├── schemas/        Pydantic contracts for every layer
├── tools/          pure financial calculations (RSI, MACD, VaR, beta, ...)
├── ui/             charts + styles
├── data/store.py   analysis-run history (SQLite)
├── streamlit_app.py   dashboard (primary entry point)
└── main.py            thin CLI (debug / headless)
tests/              pytest suite (calculations, resolver, providers, health, reasoning)
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for tests

copy .env.example .env            # then fill in the keys
```

### API keys (`.env`)

| Variable | Used for | Free-tier notes |
|---|---|---|
| `FMP_API_KEY` | US profile / history / fundamentals / ratios | US listings only; `limit` ≤ 5 statements |
| `TWELVE_DATA_API_KEY` | US quote / history, global symbol search | US price data only on free |
| `EODHD_API_KEY` | Global search (ISIN), **news**, US EOD prices | fundamentals need a paid plan; EOD ~1 year on free |
| `LLM_API_KEY` | Reasoning layer | `LLM_PROVIDER=gemini`, `LLM_MODEL=gemini-flash-lite-latest` |
| `ALPHA_VANTAGE_API_KEY` | optional legacy news fallback | leave blank if unused |

`ENABLE_YFINANCE_FALLBACK=true` lets the system serve markets the paid APIs do
not cover on the free tier (notably Indian NSE/BSE equities). Every value is
tagged with its source provider in the UI.

## Run

```bash
streamlit run app/streamlit_app.py      # dashboard
python -m app.main "Tata Consultancy Services" --period 5y   # CLI
python -m app.main AAPL --json           # full report as JSON
```

### Dashboard features

- 9 tabs: Overview, Market, Fundamentals, Technical, Risk, News, AI Intelligence,
  **Full report** (the 13-section document), Sources.
- Live agent progress while the LangGraph runs.
- **Download** the report as Markdown or JSON.
- **Recent analyses** — every run is persisted to a local SQLite table
  (`app/data/store.py`); past reports reload instantly with no API calls.

## Tests

```bash
pytest
```

Covers: security resolution & scoring, provider-response normalization, provider
fallback, Wilder RSI / ATR / MACD / Bollinger, returns / volatility / drawdown /
VaR / CVaR / Sharpe / Sortino / beta, the project risk score, the financial-health
scorer, and the reasoning agent's rule-based fallback.

## Notes on trust & limitations

- **Financial health** and the **risk score** are transparent, project-specific
  measures with the contributing metrics shown — not regulated ratings.
- Support/resistance is an explicit approximation (rolling min/max), labelled as such.
- The LLM never calculates numbers and is instructed to use only supplied
  evidence; a deterministic classification is always computed as a fallback and
  cross-check.
- Indian-equity fundamentals are limited on the free API tier and the UI says so.
