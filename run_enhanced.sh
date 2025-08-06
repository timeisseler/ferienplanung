#!/bin/bash

# Install dependencies if needed
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run the enhanced Streamlit app
echo "🚀 Starting Enhanced Load Profile Simulator..."
streamlit run app_enhanced.py