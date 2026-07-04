# data.py - Data fetching and feature engineering

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from .config import DataConfig, UniverseConfig


def fetch_prices(tickers: List[str], lookback_days: int = 60) -> Dict[str, pd.DataFrame]:
    """
    Fetch OHLCV data for all tickers using yfinance.
    Returns dict: {ticker: DataFrame with columns [Date, Open, High, Low, Close, Volume]}
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    price_data = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not df.empty:
                price_data[ticker] = df
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
    
    return price_data


def compute_features(price_df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute momentum, volatility, and volume features from OHLCV data.
    Returns a dict of features for the ticker.
    """
    if price_df.empty or len(price_df) < 10:
        return {}
    
    close = price_df['Close']
    volume = price_df['Volume']
    
    # Momentum features
    returns_1d = close.pct_change(1).iloc[-1]
    returns_5d = close.pct_change(5).iloc[-1]
    returns_10d = close.pct_change(10).iloc[-1]
    
    # Volatility
    daily_returns = close.pct_change()
    volatility = daily_returns.std()
    annualized_vol = volatility * np.sqrt(252)
    
    # Volume
    avg_volume = volume.mean()
    last_close = close.iloc[-1]
    avg_dollar_volume = avg_volume * last_close
    
    # Relative strength (vs 20-day MA)
    ma_20 = close.rolling(20).mean().iloc[-1]
    rel_strength = (last_close / ma_20 - 1) if ma_20 > 0 else 0
    
    return {
        'returns_1d': returns_1d,
        'returns_5d': returns_5d,
        'returns_10d': returns_10d,
        'volatility': volatility,
        'annualized_vol': annualized_vol,
        'avg_dollar_volume': avg_dollar_volume,
        'rel_strength': rel_strength,
        'last_close': last_close,
    }


def get_all_features() -> pd.DataFrame:
    """
    Main entry point: fetch prices for all tickers and compute features.
    Returns a DataFrame with one row per ticker and all computed features.
    """
    tickers = UniverseConfig.all_tickers()
    price_data = fetch_prices(tickers, DataConfig.LOOKBACK_DAYS)
    
    rows = []
    for ticker, df in price_data.items():
        features = compute_features(df)
        if features:
            features['ticker'] = ticker
            rows.append(features)
    
    return pd.DataFrame(rows)
