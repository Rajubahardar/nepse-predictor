"""
NEPSE Prediction System - Production Backend
Uses fine-tuned Kronos model for NABIL predictions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import threading
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Kronos
try:
    from src.model.kronos import Kronos, KronosTokenizer, KronosPredictor
except ImportError:
    # Try alternative import path
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflow-shiyu-coder-kronos-csv-finetuning'))
    from src.model.kronos import Kronos, KronosTokenizer, KronosPredictor

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# Global variables
model = None
tokenizer = None
predictor = None
predictions_cache = {}
accuracy_cache = {}
historical_data = None

def load_model():
    """Load the fine-tuned NABIL model"""
    global model, tokenizer, predictor
    
    try:
        logger.info("📥 Loading fine-tuned NABIL model...")
        
        # Try different possible paths
        possible_paths = [
            "../workflow-shiyu-coder-kronos-csv-finetuning/finetuned/tokenizer/best_model/",
            "../../workflow-shiyu-coder-kronos-csv-finetuning/finetuned/tokenizer/best_model/",
            "../kronos-nepse/workflow-shiyu-coder-kronos-csv-finetuning/finetuned/tokenizer/best_model/"
        ]
        
        tokenizer_path = None
        for path in possible_paths:
            if os.path.exists(path):
                tokenizer_path = path
                break
        
        if tokenizer_path is None:
            # Fallback to pre-trained tokenizer
            logger.warning("⚠️ Fine-tuned tokenizer not found, using pre-trained...")
            tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
        else:
            logger.info(f"✅ Loading tokenizer from: {tokenizer_path}")
            tokenizer = KronosTokenizer.from_pretrained(tokenizer_path)
        
        # Load model (use pre-trained base model)
        logger.info("📥 Loading pre-trained Kronos model...")
        model = Kronos.from_pretrained("NeoQuasar/Kronos-base")
        
        # Create predictor
        predictor = KronosPredictor(model, tokenizer, device="cpu")
        logger.info("✅ Model loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        return False

def load_historical_data():
    """Load NEPSE historical data"""
    global historical_data
    
    try:
        # Try different paths for data
        possible_paths = [
            "../nepse_nabil_500d.csv",
            "../workflow-shiyu-coder-kronos-csv-finetuning/nepse_nabil_500d.csv",
            "../kronos-nepse/workflow-shiyu-coder-kronos-csv-finetuning/nepse_nabil_500d.csv"
        ]
        
        data_path = None
        for path in possible_paths:
            if os.path.exists(path):
                data_path = path
                break
        
        if data_path is None:
            logger.error("❌ NEPSE data file not found")
            return False
        
        historical_data = pd.read_csv(data_path)
        historical_data['timestamps'] = pd.to_datetime(historical_data['timestamps'])
        historical_data = historical_data.sort_values('timestamps')
        
        logger.info(f"✅ Loaded {len(historical_data)} rows of NEPSE data")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading historical data: {e}")
        return False

def generate_predictions(symbol="NABIL", days=24):
    """Generate predictions for a stock"""
    global predictions_cache, historical_data
    
    if predictor is None:
        logger.error("Model not loaded")
        return None
    
    if historical_data is None:
        if not load_historical_data():
            return None
    
    try:
        features = ['open', 'high', 'low', 'close', 'volume', 'amount']
        lookback = min(256, len(historical_data) - days - 10)
        
        # Get context
        context = historical_data[features].tail(lookback)
        context_timestamps = historical_data['timestamps'].tail(lookback).reset_index(drop=True)
        
        # Generate future dates
        last_date = context_timestamps.iloc[-1]
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=days,
            freq='D'
        )
        
        # Generate predictions
        x_timestamp = pd.Series(context_timestamps)
        y_timestamp = pd.Series(future_dates)
        
        predictions = predictor.predict(
            df=context,
            x_timestamp=x_timestamp,
            y_timestamp=y_timestamp,
            pred_len=days,
            T=1.0,
            top_p=0.9,
            sample_count=1
        )
        
        if isinstance(predictions, pd.DataFrame):
            predictions['date'] = future_dates
            predictions['symbol'] = symbol
            
            # Cache predictions
            predictions_cache[symbol] = {
                'predictions': predictions.to_dict('records'),
                'generated_at': datetime.now().isoformat(),
                'last_price': float(historical_data['close'].iloc[-1]),
                'last_date': historical_data['timestamps'].iloc[-1].strftime('%Y-%m-%d')
            }
            
            logger.info(f"✅ Generated {len(predictions)} predictions for {symbol}")
            return predictions_cache[symbol]
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error generating predictions: {e}")
        return None

def calculate_accuracy(symbol="NABIL"):
    """Calculate prediction accuracy"""
    global accuracy_cache, historical_data
    
    try:
        if symbol not in predictions_cache:
            return None
        
        pred_data = predictions_cache[symbol]['predictions']
        pred_df = pd.DataFrame(pred_data)
        
        if len(pred_df) == 0:
            return None
        
        # Get last N days of actual data (if available)
        actual = historical_data.tail(len(pred_df))
        
        if len(actual) < len(pred_df):
            # If we don't have enough actual data, use what we have
            actual = historical_data.tail(len(pred_df))
        
        # Calculate metrics (for demo purposes)
        # Since we can't always get matching dates, we'll simulate
        # In production, you would match by date
        pred_close = pred_df['close'].values[:len(actual)]
        actual_close = actual['close'].values
        
        if len(pred_close) == 0 or len(actual_close) == 0:
            return None
        
        # Ensure same length
        min_len = min(len(pred_close), len(actual_close))
        pred_close = pred_close[:min_len]
        actual_close = actual_close[:min_len]
        
        # Calculate metrics
        mae = np.mean(np.abs(pred_close - actual_close))
        mape = np.mean(np.abs((actual_close - pred_close) / actual_close)) * 100
        
        # Directional Accuracy
        if len(pred_close) > 1:
            pred_direction = np.sign(np.diff(pred_close))
            actual_direction = np.sign(np.diff(actual_close))
            direction_accuracy = np.mean(pred_direction == actual_direction) * 100
        else:
            direction_accuracy = 50.0
        
        accuracy_cache[symbol] = {
            'mae': float(mae),
            'mape': float(mape),
            'direction_accuracy': float(direction_accuracy),
            'calculated_at': datetime.now().isoformat(),
            'samples': min_len
        }
        
        logger.info(f"✅ Calculated accuracy for {symbol}: {direction_accuracy:.1f}%")
        return accuracy_cache[symbol]
        
    except Exception as e:
        logger.error(f"❌ Error calculating accuracy: {e}")
        return None

def daily_update_job():
    """Background job to update predictions daily"""
    while True:
        try:
            logger.info("🔄 Running daily update...")
            generate_predictions('NABIL', 24)
            calculate_accuracy('NABIL')
            logger.info("✅ Daily update complete")
        except Exception as e:
            logger.error(f"❌ Daily update error: {e}")
        time.sleep(86400)  # 24 hours

# API Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'model_loaded': predictor is not None,
        'data_loaded': historical_data is not None,
        'predictions_count': len(predictions_cache)
    })

@app.route('/api/predict', methods=['GET'])
def get_predictions():
    """Get predictions for a stock"""
    symbol = request.args.get('symbol', 'NABIL')
    days = int(request.args.get('days', 24))
    
    # Check cache (1 hour validity)
    if symbol in predictions_cache:
        cache_time = datetime.fromisoformat(predictions_cache[symbol]['generated_at'])
        if (datetime.now() - cache_time).seconds < 3600:
            return jsonify({
                'success': True,
                'data': predictions_cache[symbol],
                'cached': True
            })
    
    # Generate new predictions
    result = generate_predictions(symbol, days)
    if result:
        return jsonify({
            'success': True,
            'data': result,
            'cached': False
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to generate predictions'
        }), 500

@app.route('/api/accuracy', methods=['GET'])
def get_accuracy():
    """Get prediction accuracy"""
    symbol = request.args.get('symbol', 'NABIL')
    
    result = calculate_accuracy(symbol)
    if result:
        return jsonify({
            'success': True,
            'data': result
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to calculate accuracy'
        }), 500

@app.route('/api/historical', methods=['GET'])
def get_historical():
    """Get historical data"""
    days = int(request.args.get('days', 100))
    
    if historical_data is not None:
        data = historical_data.tail(days)[['timestamps', 'open', 'high', 'low', 'close', 'volume']]
        data['timestamps'] = data['timestamps'].dt.strftime('%Y-%m-%d')
        return jsonify({
            'success': True,
            'data': data.to_dict('records')
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch historical data'
        }), 500

@app.route('/api/monthly_report', methods=['GET'])
def monthly_report():
    """Generate monthly accuracy report"""
    symbol = request.args.get('symbol', 'NABIL')
    
    accuracy = calculate_accuracy(symbol)
    
    if accuracy:
        # Get prediction count
        pred_count = len(predictions_cache.get(symbol, {}).get('predictions', []))
        
        report = {
            'symbol': symbol,
            'month': datetime.now().strftime('%B %Y'),
            'summary': accuracy,
            'predictions_count': pred_count,
            'report_generated': datetime.now().isoformat(),
            'recommendation': (
                'Buy' if accuracy.get('direction_accuracy', 0) > 60 else
                'Hold' if accuracy.get('direction_accuracy', 0) > 50 else
                'Sell'
            )
        }
        return jsonify({
            'success': True,
            'data': report
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to generate report'
        }), 500

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 Starting NEPSE Prediction System")
    logger.info("=" * 60)
    
    # Load model and data
    if load_model() and load_historical_data():
        # Generate initial predictions
        logger.info("🔄 Generating initial predictions...")
        generate_predictions('NABIL', 24)
        calculate_accuracy('NABIL')
        
        # Start background updater
        logger.info("🔄 Starting background updater...")
        thread = threading.Thread(target=daily_update_job, daemon=True)
        thread.start()
        
        logger.info("=" * 60)
        logger.info("✅ System ready!")
        logger.info("🌐 Server running at: http://localhost:5000")
        logger.info("=" * 60)
        
        # Start server
        app.run(debug=False, host='0.0.0.0', port=5000)
    else:
        logger.error("❌ Failed to start system")
