# signals.py - Signal scoring and ranking logic

import pandas as pd
import numpy as np
from typing import List, Dict
from .config import SignalConfig
from .data import get_all_features_with_sentiment


def apply_risk_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove tickers that don't meet minimum liquidity or volatility thresholds.
    """
    filtered = df[
        (df['avg_dollar_volume'] >= SignalConfig.MIN_AVG_DOLLAR_VOLUME) &
        (df['annualized_vol'] <= SignalConfig.MAX_ANNUALISED_VOL)
    ].copy()
    return filtered


def compute_signal_score(row: pd.Series) -> float:
    """
    Combine momentum, volatility, and volume into a single score.
    Higher score = better candidate.
    """
    # Momentum component (average of 1d, 5d, 10d returns)
    momentum = (row['returns_1d'] + row['returns_5d'] + row['returns_10d']) / 3
    momentum_score = momentum * 100  # scale to percentage points
    
    # Volatility component (penalize high volatility)
    vol_score = -row['annualized_vol'] * 100
    
    # Volume score (reward higher liquidity)
    volume_score = np.log10(row['avg_dollar_volume']) - 6  # normalized around 1M
    
    # Sentiment score (from Finnhub news)
    sentiment_score = row.get('sentiment_score', 0.0) * 100  # scale to -100 to +100
    
    # Weighted combination
    score = (
        SignalConfig.MOMENTUM_WEIGHT * momentum_score +
        SignalConfig.VOLATILITY_WEIGHT * vol_score +
        SignalConfig.VOLUME_WEIGHT * volume_score +
        SignalConfig.SENTIMENT_WEIGHT * sentiment_score
    )
    
    return score


def rank_candidates() -> pd.DataFrame:
    """
    Main entry point:
    1. Get all features
    2. Apply risk filters
    3. Compute signal scores
    4. Rank and return top N
    """
        df = get_all_features_with_sentiment()
    
    if df.emp
    # Apply filters
    df = apply_risk_filters(df)
    
    # Compute scores
    df['signal_score'] = df.apply(compute_signal_score, axis=1)
    
    # Sort by score descending
    df = df.sort_values('signal_score', ascending=False)
    
    # Return top N
    top_n = df.head(SignalConfig.TOP_N)
    
    return top_n[['ticker', 'signal_score', 'returns_5d', 'annualized_vol', 
                  'sentiment_score', 'news_count',
                  'avg_dollar_volume', 'last_close']]


def get_daily_recommendations() -> List[Dict]:
    """
    Returns daily top 3 recommendations as a list of dicts.
    Each dict has: ticker, score, rationale.
    """
    ranked = rank_candidates()
    
    recommendations = []
    for _, row in ranked.iterrows():
        rec = {
            'ticker': row['ticker'],
            'score': round(row['signal_score'], 2),
            'returns_5d': round(row['returns_5d'] * 100, 2),
            'volatility': round(row['annualized_vol'] * 100, 1),
            'last_close': round(row['last_close'], 2),
                        'sentiment_score': round(row.get('sentiment_score', 0.0), 2),
            'news_count': int(row.get('news_count', 0)),
            'rationale': f"Strong momentum ({row['returns_5d']*100:.1f}% 5d return), "
                        f"moderate volatility ({row['annualized_vol']*100:.1f}%)"
        }
        recommendations.append(rec)
    
    return recommendations
