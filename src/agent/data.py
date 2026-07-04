# data.py - Data fetching and feature engineering
from groq import Groq

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
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

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.squeeze()
    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]
    volume = volume.squeeze()

    close = close.dropna()
    volume = volume.dropna()
    if close.empty or volume.empty or len(close) < 10:
        return {}

    def _to_scalar(value):
        if isinstance(value, (pd.Series, pd.Index, pd.DataFrame)):
            value = value.iloc[-1] if len(value) else np.nan
        return float(value) if pd.notna(value) else 0.0

    # Momentum features
    returns_1d = _to_scalar(close.pct_change(1).iloc[-1])
    returns_5d = _to_scalar(close.pct_change(5).iloc[-1])
    returns_10d = _to_scalar(close.pct_change(10).iloc[-1])

    # Volatility
    daily_returns = close.pct_change()
    volatility = float(daily_returns.std())
    annualized_vol = volatility * np.sqrt(252)

    # Volume
    avg_volume = float(volume.mean())
    last_close = _to_scalar(close.iloc[-1])
    avg_dollar_volume = avg_volume * last_close

    # Relative strength (vs 20-day MA)
    ma_20 = close.rolling(20).mean().iloc[-1]
    ma_20 = _to_scalar(ma_20)
    rel_strength = (last_close / ma_20 - 1) if ma_20 > 0 else 0.0

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
        raise ValueError(
            "FINNHUB_API_KEY is required but not set. "
            "Please add your Finnhub API key to .env file. "
            "Get a free key at https://finnhub.io/register"
        )    
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
        print(f"Error fetching Finnhub sentiment for {ticker}: {e}")
        raise  # Re-raise the error instead of returning default values

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
            sentiment_data = {'sentiment_score': 0.0, 'news_count': 0}
            if DataConfig.FINNHUB_API_KEY:
                try:
                    sentiment_data = fetch_finnhub_sentiment(ticker)
                except Exception as e:
                    print(f"Warning: failed sentiment fetch for {ticker}: {e}")

            features['sentiment_score'] = sentiment_data['sentiment_score']
            features['news_count'] = sentiment_data['news_count']
            features['ticker'] = ticker
            rows.append(features)

    return pd.DataFrame(rows)



def analyze_with_groq_llm(ticker: str, news_headlines: List[str]) -> Dict[str, Any]:
    """
    Use Groq LLM to analyze news headlines and generate sentiment + rationale.
    Returns dict with llm_sentiment_score and llm_rationale.
    """
    if not DataConfig.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is required but not set. "
            "Please add your Groq API key to .env file. "
            "Get a free key at https://console.groq.com/"
        )
    
    try:
        client = Groq(api_key=DataConfig.GROQ_API_KEY)
        
        # Prepare prompt with news headlines
        headlines_text = "\n".join([f"- {h}" for h in news_headlines[:10]]) if news_headlines else "No recent news"
        
        prompt = f"""Analyze the following news headlines for stock ticker {ticker} and provide:
1. A sentiment score from -1 (very negative) to +1 (very positive)
2. A brief rationale (1-2 sentences) explaining the sentiment

News headlines:
{headlines_text}

Respond in JSON format: {{"sentiment_score": <float>, "rationale": "<string>"}}"""
        
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",  # Free tier model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content
        
        # Parse JSON response
        import json
        try:
            result = json.loads(result_text)
            return {
                'llm_sentiment_score': float(result.get('sentiment_score', 0.0)),
                'llm_rationale': result.get('rationale', 'No rationale provided')
            }
        except json.JSONDecodeError:
            # If LLM doesn't return valid JSON, try to extract sentiment
            return {
                'llm_sentiment_score': 0.0,
                'llm_rationale': result_text[:200]  # Use raw response
            }
    
    except Exception as e:
        print(f"Error using Groq LLM for {ticker}: {e}")
        raise  # Re-raise the error instead of returning default values
