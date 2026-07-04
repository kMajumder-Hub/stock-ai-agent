# 📈 Stock AI Agent

**AI-powered stock market agent** that scans US and Canadian markets daily and recommends top 3 stocks/ETFs based on momentum, volatility, and volume signals.

---

## Features

- 🔍 **Daily scans** of 40+ US and Canadian tickers (configurable)
- 📊 **Technical signals**: momentum (1d/5d/10d returns), volatility, relative strength, dollar volume
- 🎯 **Top 3 daily picks** ranked by composite score
- 🚀 **Streamlit UI** for interactive browsing
- ⏰ **Cron-ready** autonomous runner
- 🆓 **100% free data sources**: `yfinance` + optional Finnhub free tier

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/kMajumder-Hub/stock-ai-agent.git
cd stock-ai-agent
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Streamlit app

```bash
streamlit run app_streamlit.py
```

Open your browser at `http://localhost:8501`, click "Run Daily Scan", and see the top 3 recommendations.

### 3. (Optional) Set up daily automation

Add to your crontab (Linux/Mac) or Task Scheduler (Windows):

```bash
# Run every day at 8 AM ET
0 8 * * * /path/to/venv/bin/python /path/to/stock-ai-agent/cron_runner.py
```

Results are saved to `data/results/recommendations_YYYY-MM-DD.json`.

---

## Project Structure

```
stock-ai-agent/
├── src/agent/
│   ├── __init__.py
│   ├── config.py          # Universe, weights, API keys
│   ├── data.py            # yfinance price fetching + feature engineering
│   └── signals.py         # Scoring and ranking logic
├── app_streamlit.py       # Interactive Streamlit UI
├── cron_runner.py         # Autonomous daily runner
├── requirements.txt       # Python dependencies
└── README.md
```

---

## Configuration

Edit `src/agent/config.py` to customize:

- **UniverseConfig**: Add/remove tickers (US tickers + Canadian `.TO` suffix for TSX)
- **DataConfig**: Lookback period, Finnhub API key (optional)
- **SignalConfig**: Momentum/volatility/volume weights, risk filters
- **ScheduleConfig**: Cron timings (default 8 AM ET)

---

## How it works

1. **Data ingestion** (`data.py`):  
   - Fetches 60 days of OHLCV from Yahoo Finance via `yfinance`  
   - Computes features: 1d/5d/10d returns, volatility, dollar volume, relative strength vs 20-day MA

2. **Risk filters** (`signals.py`):  
   - Removes low-liquidity tickers (< $5M avg daily volume)  
   - Removes high-volatility names (annualized vol > 80%)

3. **Scoring & ranking** (`signals.py`):  
   - Combines momentum (40%), sentiment (30%), volatility penalty (20%), volume (10%)  
   - Sorts by score descending, returns top 3

4. **Output**:  
   - Streamlit app: visual cards with ticker, score, 5d return, volatility, rationale  
   - Cron runner: JSON file with timestamp and full recommendations

---

## Future enhancements

- [ ] Add Finnhub news/sentiment integration
- [ ] Backtest framework with historical performance metrics
- [ ] Support for ML-based ranking (gradient boosting)
- [ ] IBKR paper-trading integration
- [ ] Email/Slack notifications
- [ ] Sector rotation and ETF-specific signals

---

## License

MIT

---

## Disclaimer

This tool is for **research and educational purposes only**. It is not financial advice. Always do your own due diligence before making any investment decisions.
