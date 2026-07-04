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



# ────────────────────────────────────────────────────────────────────────────────
# Finnhub News & Sentiment Integration
# ────────────────────────────────────────────────────────────────────────────────

def fetch_finnhub_sentiment(ticker: str) -> Dict[str, float]:
    """
    Fetch news sentiment for a ticker from Finnhub.
    Returns dict with sentiment_score and news_count.
    """
    if not DataConfig.FINNHUB_API_KEY:
        return {'sentiment_score': 0.0, 'news_count': 0}
    
    try:
        import finnhub
        finnhub_client = finnhub.Client(api_key=DataConfig.FINNHUB_API_KEY)
        
        # Clean ticker symbol (remove .TO suffix for Canadian stocks)
        clean_ticker = ticker.replace('.TO', '')
        
        # Get company news from last 7 days
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        news = finnhub_client.company_news(clean_ticker, _from=from_date, to=to_date)
        
        if not news:
            return {'sentiment_score': 0.0, 'news_count': 0}
        
        # Get sentiment for each news article
        sentiments = []
        for article in news[:10]:  # Limit to 10 most recent
            headline = article.get('headline', '')
            summary = article.get('summary', '')
            
            if headline or summary:
                # Use Finnhub's sentiment analysis
                sentiment_result = finnhub_client.news_sentiment([clean_ticker])
                if sentiment_result and 'sentiment' in sentiment_result:
                    sentiment = sentiment_result['sentiment']
                    # Finnhub returns buzz and sentiment scores
                    if 'sentimentScore' in sentiment:
                        sentiments.append(sentiment['sentimentScore'])
        
        # If sentiment API not available, use simple heuristic
        if not sentiments:
            # Count positive/negative keywords as fallback
            positive_words = ['beat', 'surge', 'gain', 'profit', 'growth', 'upgrade', 'strong']
            negative_words = ['miss', 'drop', 'loss', 'decline', 'downgrade', 'weak', 'warning']
            
            for article in news[:10]:
                text = (article.get('headline', '') + ' ' + article.get('summary', '')).lower()
                pos_count = sum(1 for word in positive_words if word in text)
                neg_count = sum(1 for word in negative_words if word in text)
                
                if pos_count + neg_count > 0:
                    score = (pos_count - neg_count) / (pos_count + neg_count)
                    sentiments.append(score)
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        return {
            'sentiment_score': avg_sentiment,
            'news_count': len(news)
        }
    
    except Exception as e:
        print(f"Error fetching Finnhub sentiment for {ticker}: {e}")
        return {'sentiment_score': 0.0, 'news_count': 0}


def get_all_features_with_sentiment() -> pd.DataFrame:
    """
    Main entry point with Finnhub sentiment integration.
    Fetches prices and sentiment for all tickers.
    """
    tickers = UniverseConfig.all_tickers()
    price_data = fetch_prices(tickers, DataConfig.LOOKBACK_DAYS)
    
    rows = []
    for ticker, df in price_data.items():
        features = compute_features(df)
        if features:
            # Add sentiment data
            sentiment_data = fetch_finnhub_sentiment(ticker)
            features['sentiment_score'] = sentiment_data['sentiment_score']
            features['news_count'] = sentiment_data['news_count']
            features['ticker'] = ticker
            rows.append(features)
    
    return pd.DataFrame(rows)
