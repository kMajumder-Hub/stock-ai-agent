# ── config.py ──────────────────────────────────────────────────────────────────

# Helper function to get secrets from Streamlit Cloud or .env
def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment variable."""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except ImportError:
        pass  # Streamlit not installed or not in Streamlit environment
    return os.getenv(key, default)

# Central configuration for the Stock AI Agent.
# Edit the values here to customise universe, lookback, and API settings.
# ────────────────────────────────────────────────────────────────────────────────

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env file if present


class UniverseConfig:
    """Tickers to scan every day."""

    # --- US equities & ETFs ---
    US_TICKERS = [
        # Large-cap tech
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
        # Financials
        "JPM", "BAC", "GS",
        # Healthcare
        "JNJ", "PFE", "UNH",
        # Energy
        "XOM", "CVX",
        # ETFs
        "SPY", "QQQ", "IWM", "XLF", "XLE", "XLK", "ARKK",
    ]

    # --- Canadian equities & ETFs (Yahoo Finance uses .TO suffix) ---
    CA_TICKERS = [
        # Banks
        "RY.TO", "TD.TO", "BNS.TO", "BMO.TO", "CM.TO",
        # Energy
        "CNQ.TO", "SU.TO", "TRP.TO",
        # Tech / diversified
        "SHOP.TO", "CSU.TO",
        # ETFs
        "XIU.TO", "XGRO.TO", "ZSP.TO", "VFV.TO",
    ]

    @classmethod
    def all_tickers(cls):
        return cls.US_TICKERS + cls.CA_TICKERS


class DataConfig:
    """Data-fetching parameters."""
    LOOKBACK_DAYS: int = 60        # calendar days of price history to fetch
    INTRADAY_INTERVAL: str = "1d"  # yfinance interval: 1d | 1h | 30m
    GROQ_API_KEY: str = get_secret("GROQ_API_KEY", "")
    FINNHUB_API_KEY: str = get_secret("FINNHUB_API_KEY", "")

class SignalConfig:
    """Signal and scoring weights."""
    MOMENTUM_WEIGHT: float = 0.40
    
    SENTIMENT_WEIGHT: float = 0.30
    VOLATILITY_WEIGHT: float = 0.20  # lower vol = higher score
    VOLUME_WEIGHT: float = 0.10

    # Minimum average daily dollar volume (USD/CAD) to include a ticker
    MIN_AVG_DOLLAR_VOLUME: float = 5_000_000

    # Maximum annualised volatility allowed
    MAX_ANNUALISED_VOL: float = 0.80  # 80 %

    TOP_N: int = 3  # number of daily recommendations


class ScheduleConfig:
    """Cron / schedule timings (24-hour ET times)."""
    PRE_MARKET_RUN_HOUR: int = 8    # 08:00 ET  – morning signal run
    POST_MARKET_RUN_HOUR: int = 17  # 17:00 ET  – EOD logging


class PathConfig:
    """Local file-system paths."""
    DATA_DIR: str = "data"
    PRICES_DIR: str = "data/prices"
    NEWS_DIR: str = "data/news"
    RESULTS_DIR: str = "data/results"
    LOG_FILE: str = "data/agent.log"
