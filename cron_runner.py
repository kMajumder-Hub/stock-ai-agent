#!/usr/bin/env python3
# cron_runner.py - Autonomous daily runner for Stock AI Agent
# Schedule this via cron/Task Scheduler for automated daily runs

import sys
import json
from datetime import datetime
from pathlib import Path

from src.agent.signals import get_daily_recommendations
from src.agent.config import PathConfig


def run_daily_agent():
    """
    Execute daily stock scan and save recommendations to JSON.
    """
    print(f"[{datetime.now()}] Starting Stock AI Agent daily run...")
    
    try:
        # Ensure output directory exists
        Path(PathConfig.RESULTS_DIR).mkdir(parents=True, exist_ok=True)
        
        # Get recommendations
        recs = get_daily_recommendations()
        
        if not recs:
            print("No recommendations generated.")
            return
        
        # Save to JSON file with timestamp
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = Path(PathConfig.RESULTS_DIR) / f"recommendations_{today}.json"
        
        with open(output_file, 'w') as f:
            json.dump({
                'date': today,
                'timestamp': datetime.now().isoformat(),
                'recommendations': recs
            }, f, indent=2)
        
        print(f"Saved {len(recs)} recommendations to {output_file}")
        
        # Print to console
        for i, rec in enumerate(recs, 1):
            print(f"  #{i} {rec['ticker']}: score={rec['score']}, "
                  f"5d_return={rec['returns_5d']}%")
    
    except Exception as e:
        print(f"Error during agent run: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_daily_agent()
