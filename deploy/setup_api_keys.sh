#!/bin/bash

# OrCast API Keys Setup Script
# Run this script to set up your API keys as environment variables

echo "🔑 OrCast API Keys Setup"
echo "========================"
echo

# OpenWeather API
echo "1. OpenWeather API Key:"
echo "   - Go to: https://openweathermap.org/api"
echo "   - Sign up and get your API key"
echo "   - Then run: export OPENWEATHER_API_KEY='your_key_here'"
echo

# eBird API
echo "2. eBird API Key:"
echo "   - Go to: https://ebird.org/api/keygen"
echo "   - Request your API key"
echo "   - Then run: export EBIRD_API_KEY='your_key_here'"
echo

# World Weather Online API
echo "3. World Weather Online API Key:"
echo "   - Go to: https://www.worldweatheronline.com/developer/api/"
echo "   - Sign up for developer account"
echo "   - Then run: export WORLDWEATHERONLINE_API_KEY='your_key_here'"
echo

echo "📝 To make these permanent, add them to your ~/.zshrc file:"
echo "   echo 'export OPENWEATHER_API_KEY=\"your_key_here\"' >> ~/.zshrc"
echo "   echo 'export EBIRD_API_KEY=\"your_key_here\"' >> ~/.zshrc"
echo "   echo 'export WORLDWEATHERONLINE_API_KEY=\"your_key_here\"' >> ~/.zshrc"
echo

echo "✅ To test if keys are working, run:"
echo "   python scripts/data_processing/production_data_pipeline.py"
echo

echo "🚀 The pipeline works fine without these keys using only free APIs!"
echo "   These just add extra weather and bird observation data." 