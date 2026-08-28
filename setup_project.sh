#!/bin/bash

echo "🚀 Setting up NEPSE Predictor Project..."

# Create project directory
mkdir -p nepse-predictor
cd nepse-predictor

# Create directory structure
mkdir -p backend/app/routes
mkdir -p backend/static/css
mkdir -p backend/static/js
mkdir -p backend/templates
mkdir -p frontend/static/css
mkdir -p frontend/static/js
mkdir -p frontend/templates
mkdir -p models/nabil
mkdir -p data
mkdir -p scripts
mkdir -p config
mkdir -p logs

# Find and copy model files
echo "📥 Copying model files..."
MODEL_PATH=$(find .. -type d -name "best_model" 2>/dev/null | grep -E "tokenizer|finetuned" | head -1)
if [ -n "$MODEL_PATH" ]; then
    cp -r "$MODEL_PATH" models/nabil/tokenizer/
    echo "✅ Model copied from: $MODEL_PATH"
else
    echo "⚠️ Model not found. You'll need to copy it manually."
fi

# Find and copy data file
DATA_PATH=$(find .. -name "nepse_nabil*.csv" 2>/dev/null | head -1)
if [ -n "$DATA_PATH" ]; then
    cp "$DATA_PATH" data/
    echo "✅ Data copied from: $DATA_PATH"
else
    echo "⚠️ Data file not found. You'll need to copy it manually."
fi

# Create __init__.py files
touch backend/app/__init__.py
touch backend/app/routes/__init__.py

echo "✅ Project structure created!"
echo "📁 Location: $(pwd)"
