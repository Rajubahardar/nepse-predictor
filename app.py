import os
import random
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

# Import the scraper library
from nepse_scraper import NepseScraper

app = Flask(__name__)
CORS(app)

# Initialize scraper (with SSL verification off due to NEPSE's known SSL issues)
scraper = NepseScraper(verify_ssl=False)

def get_live_nepse_data(symbol="NABIL"):
    """Fetches live data directly from NEPSE using the nepse-scraper library."""
    try:
        # Fetch today's price data for all companies
        today_prices = scraper.get_today_price()
        if today_prices:
            # Find the specific stock (e.g., NABIL)
            stock_data = next((item for item in today_prices if item['symbol'] == symbol), None)
            if stock_data:
                return {
                    'price': float(stock_data.get('lastTradedPrice', 0)),
                    'change': float(stock_data.get('change', 0)),
                    'change_pct': float(stock_data.get('percentageChange', 0)),
                    'high': float(stock_data.get('high', 0)),
                    'low': float(stock_data.get('low', 0)),
                    'open': float(stock_data.get('open', 0)),
                }
    except Exception as e:
        print(f"Error fetching live data: {e}")
    return None

@app.route('/')
def home():
    live_data = get_live_nepse_data()
    
    # If data is successfully fetched, use it. Otherwise, return an error message.
    if not live_data:
        return render_template_string("<h1 style='font-family:sans-serif; color:red;'>Unable to fetch live NEPSE data. Please try again later.</h1>")
    
    change_class = "text-up" if live_data['change_pct'] >= 0 else "text-down"
    change_str = f"{live_data['change_pct']:.2f}%"
    
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>NEPSE Stock Predictor</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg-deep: #0a3d91; --bg-light: #1a5cb5; --text-main: #ffffff; --text-muted: #d0dcf0; --up-color: #4ade80; --down-color: #f87171; --card-bg: rgba(255, 255, 255, 0.1); --border: rgba(255, 255, 255, 0.2); }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif; }
        body { background: linear-gradient(135deg, var(--bg-deep) 0%, var(--bg-light) 100%); color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 40px; }
        header { margin-bottom: 30px; text-align: center; } h1 { font-size: 42px; font-weight: 700; margin-bottom: 10px; }
        .badge { background: var(--up-color); color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; font-weight: 600; display: inline-block; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; width: 100%; max-width: 1000px; margin-bottom: 40px; }
        .stat-card { background: var(--card-bg); backdrop-filter: blur(10px); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center; }
        .stat-card h2 { font-size: 18px; color: var(--text-muted); margin-bottom: 10px; } .stat-card p { font-size: 28px; font-weight: 700; }
        .text-up { color: var(--up-color); } .text-down { color: var(--down-color); }
        .table-section { width: 100%; max-width: 1000px; background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 40px; }
        .table-section h2 { margin-bottom: 20px; font-size: 24px; } table { width: 100%; border-collapse: collapse; color: var(--text-main); }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.1); } th { background: rgba(255, 255, 255, 0.1); font-weight: 600; }
    </style>
</head>
<body>
    <header><h1>NEPSE Stock Predictor</h1><span class="badge">LIVE</span></header>
    <div class="stats-grid">
        <div class="stat-card"><h2>Current Price</h2><p>{{ live_data.price }}</p></div>
        <div class="stat-card"><h2>Change %</h2><p class="{{ change_class }}">{{ change_str }}</p></div>
        <div class="stat-card"><h2>Open</h2><p>{{ live_data.open }}</p></div>
        <div class="stat-card"><h2>High / Low</h2><p style="font-size: 18px;">{{ live_data.high }} / {{ live_data.low }}</p></div>
    </div>
</body>
</html>'''
    return render_template_string(html, live_data=live_data, change_class=change_class, change_str=change_str)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
