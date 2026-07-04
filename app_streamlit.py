
import sys
import os
# Add the project root to the Python path for Streamlit Cloud
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# app_streamlit.py - Streamlit UI for Stock AI Agent

import streamlit as st
import pandas as pd
from datetime import datetime
from src.agent.signals import get_daily_recommendations
from src.agent.config import UniverseConfig

st.set_page_config(page_title="Stock AI Agent", page_icon="📈", layout="wide")

st.title("📈 Stock AI Agent - Daily Recommendations")
st.markdown("AI-powered stock scanner for US and Canadian markets")

st.sidebar.header("Settings")
st.sidebar.markdown(f"**Universe**: {len(UniverseConfig.all_tickers())} tickers")
st.sidebar.markdown(f"**Markets**: US (NYSE/Nasdaq) + Canada (TSX)")
st.sidebar.markdown(f"**Last run**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if st.button("🔄 Run Daily Scan", type="primary"):
    with st.spinner("Fetching data and computing signals..."):
        try:
            recommendations = get_daily_recommendations()
            
            if recommendations is None or recommendations.empty:
                                st.warning("No recommendations found. Check data availability.")
            else:
                                st.success(f"Found {len(recommendations)} top candidates")               
                for i, rec in enumerate(recommendations, 1):
                    with st.expander(f"#{i} - {rec['ticker']} (Score: {rec['score']})", expanded=True):
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Ticker", rec['ticker'])
                        col2.metric("Score", rec['score'])
                        col3.metric("5d Return", f"{rec['returns_5d']}%")
                        col4.metric("Volatility", f"{rec['volatility']}%")
                        
                        st.write(f"**Last Close**: ${rec['last_close']}")
                        st.write(f"**Rationale**: {rec['rationale']}")
        
        except Exception as e:
            st.error(f"Error running scan: {str(e)}")

st.markdown("---")
st.markdown("""**About**: This agent scans US and Canadian stocks/ETFs daily using momentum, 
volatility, and volume signals. Powered by `yfinance` and customizable via `src/agent/config.py`.""")
