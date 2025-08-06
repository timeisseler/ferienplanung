#!/bin/bash

# Install dependencies if needed
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run the Streamlit app
echo "🚀 Starting Load Profile Simulator..."
streamlit run app.py