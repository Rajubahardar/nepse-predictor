import requests
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import os
import random
from datetime import datetime, timedelta

# ... (keep your app initialization and BASE_PRICE) ...

def get_live_nepse_data(symbol="NABIL"):
    """Fetches real-time data from the NEPSE API."""
    try:
        # Direct API endpoint for current prices
        url = "https://nepse-data-api.adaptable.app/api/v1/prices/today"
        
        # Handle SSL issues by creating a session without verification
        session = requests.Session()
        session.verify = False
        
        response = session.get(url, timeout=5)
        response.raise_for_status()
        
        # Iterate through the list to find your specific symbol
        stocks = response.json()
        for stock in stocks:
            if stock.get('symbol') == symbol:
                return {
                    'price': float(stock.get('lastTradedPrice', BASE_PRICE)),
                    'change': float(stock.get('change', 0.0)),
                    'change_pct': float(stock.get('percentageChange', 0.0)),
                    'high': float(stock.get('high', 0.0)),
                    'low': float(stock.get('low', 0.0)),
                    'open': float(stock.get('open', 0.0)),
                }
                
        # Fallback if stock not found in list
        return {
            'price': BASE_PRICE,
            'change': -0.19,
            'change_pct': -0.02,
            'high': 800.0,
            'low': 790.0,
            'open': 795.0,
        }
        
    except Exception as e:
        print(f"Error fetching NEPSE data: {e}")
        # Fallback to BASE_PRICE if API fails
        return {
            'price': BASE_PRICE,
            'change': -0.19,
            'change_pct': -0.02,
            'high': 800.0,
            'low': 790.0,
            'open': 795.0,
        }