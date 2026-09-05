import io
import time
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# NSE OFFICIAL EQUITY SECURITY MASTER
# ============================================================

NSE_EQUITY_URL = (
    "https://nsearchives.nseindia.com/"
    "content/equities/EQUITY_L.csv"
)

CACHE_DIR = Path(".cache")
CACHE_FILE = CACHE_DIR / "nse_equity.csv"

# Refresh the security master every 12 hours.
CACHE_TTL = 60 * 60 * 12


# ============================================================
# DOWNLOAD NSE EQUITY MASTER
# ============================================================

def download_nse_equity_master() -> pd.DataFrame:

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        ),
        "Accept": (
            "text/csv,text/plain,"
            "application/octet-stream,*/*"
        ),
        "Referer": "https://www.nseindia.com/",
    }

    response = requests.get(
        NSE_EQUITY_URL,
        headers=headers,
        timeout=20,
    )

    response.raise_for_status()

    df = pd.read_csv(
        io.BytesIO(response.content)
    )

    return df


# ============================================================
# LOAD NSE EQUITY MASTER
# ============================================================

def load_nse_equity_master() -> pd.DataFrame:

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Use cache if recent
    # --------------------------------------------------------

    if CACHE_FILE.exists():

        age = (
            time.time()
            - CACHE_FILE.stat().st_mtime
        )

        if age < CACHE_TTL:

            try:

                return pd.read_csv(
                    CACHE_FILE
                )

            except Exception:
                pass

    # --------------------------------------------------------
    # Download fresh data
    # --------------------------------------------------------

    df = download_nse_equity_master()

    # --------------------------------------------------------
    # Save cache
    # --------------------------------------------------------

    try:

        df.to_csv(
            CACHE_FILE,
            index=False,
        )

    except Exception:
        pass

    return df


# ============================================================
# NORMALIZE COLUMNS
# ============================================================

def normalize_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    df.columns = [
        str(column)
        .strip()
        .upper()
        for column in df.columns
    ]

    return df


# ============================================================
# FIND COLUMN
# ============================================================

def find_column(
    df: pd.DataFrame,
    possible_names: list[str],
) -> str | None:

    for name in possible_names:

        if name in df.columns:

            return name

    return None


# ============================================================
# SEARCH INDIAN EQUITY
# ============================================================

def search_indian_equity(
    user_input: str,
) -> dict | None:

    query = (
        user_input
        .strip()
        .upper()
    )

    if not query:
        return None

    try:

        df = load_nse_equity_master()

    except Exception:

        # NSE unavailable.
        # Caller can use another resolver.
        return None

    df = normalize_columns(
        df
    )

    # ========================================================
    # IDENTIFY COLUMNS
    # ========================================================

    symbol_col = find_column(
        df,
        [
            "SYMBOL",
        ],
    )

    name_col = find_column(
        df,
        [
            "NAME OF COMPANY",
            "COMPANY NAME",
            "NAME",
        ],
    )

    series_col = find_column(
        df,
        [
            "SERIES",
        ],
    )

    isin_col = find_column(
        df,
        [
            "ISIN NUMBER",
            "ISIN",
        ],
    )

    if symbol_col is None:
        return None

    # ========================================================
    # CLEAN DATA
    # ========================================================

    df[symbol_col] = (
        df[symbol_col]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    if name_col:

        df[name_col] = (
            df[name_col]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # ========================================================
    # IMPORTANT:
    #
    # NSE's Equity file contains securities from the equity
    # segment. We specifically prefer normal EQ shares.
    #
    # This helps prevent ETF/fund instruments from becoming
    # the result when a company is requested.
    # ========================================================

    if series_col:

        df[series_col] = (
            df[series_col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        equity_df = df[
            df[series_col] == "EQ"
        ].copy()

        # If the official file happens to use another
        # structure, don't completely fail.
        if equity_df.empty:
            equity_df = df.copy()

    else:

        equity_df = df.copy()

    # ========================================================
    # BUILD CANDIDATES
    # ========================================================

    candidates = []

    for _, row in equity_df.iterrows():

        symbol = str(
            row[symbol_col]
        ).strip().upper()

        if not symbol:
            continue

        name = ""

        if name_col:

            name = str(
                row[name_col]
            ).strip()

        isin = ""

        if isin_col:

            isin = str(
                row[isin_col]
            ).strip()

        candidates.append(
            {
                "symbol": symbol,
                "name": name,
                "isin": isin,
            }
        )

    if not candidates:
        return None

    # ========================================================
    # SCORE CANDIDATES
    # ========================================================

    scored = []

    for candidate in candidates:

        symbol = candidate["symbol"]

        name = candidate["name"].upper()

        score = 0

        # ----------------------------------------------------
        # Exact NSE symbol
        # ----------------------------------------------------

        if query == symbol:

            score += 5000

        # ----------------------------------------------------
        # Symbol begins with query
        #
        # SBI -> SBIN
        # INFY -> INFY
        # TCS -> TCS
        # ----------------------------------------------------

        elif symbol.startswith(query):

            score += 2500

        # ----------------------------------------------------
        # Company name exact
        # ----------------------------------------------------

        if query == name:

            score += 4000

        # ----------------------------------------------------
        # Company name begins with query
        # ----------------------------------------------------

        if name.startswith(query):

            score += 2000

        # ----------------------------------------------------
        # Company name contains query
        # ----------------------------------------------------

        if query in name:

            score += 1000

        # ----------------------------------------------------
        # Prefer shorter symbols when user enters an
        # abbreviation.
        #
        # SBI:
        #
        # SBIN      ← preferred
        # SBILIFE   ← less preferred
        # SBICARD   ← less preferred
        # ----------------------------------------------------

        if symbol.startswith(query):

            extra_length = (
                len(symbol)
                - len(query)
            )

            if extra_length <= 1:

                score += 4000

            elif extra_length <= 3:

                score += 1500

            elif extra_length <= 6:

                score += 500

        if score > 0:

            candidate_copy = (
                candidate.copy()
            )

            candidate_copy["score"] = score

            scored.append(
                candidate_copy
            )

    # ========================================================
    # NO MATCH
    # ========================================================

    if not scored:

        return None

    # ========================================================
    # SORT
    # ========================================================

    scored.sort(
        key=lambda item: (
            item["score"],
            -len(item["symbol"]),
        ),
        reverse=True,
    )

    best = scored[0]

    # ========================================================
    # RETURN VERIFIED INDIAN EQUITY
    # ========================================================

    return {
        "name": best["name"],
        "symbol": best["symbol"],
        "exchange": "NSE",
        "currency": "INR",
        "currency_symbol": "₹",
        "market": "India",
        "asset_type": "EQUITY",
        "isin": best["isin"],
        "confidence": 0.99,
        "source": "NSE Security Master",
    }