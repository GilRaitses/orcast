#!/bin/bash

# ORCAST Hackathon Demo Startup Script
# This script starts the Angular development server for the AI Agent Demo

echo "🚀 Starting ORCAST AI Agent Demo for Hackathon..."
echo "============================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Not in the Angular project directory"
    echo "Please run this script from the orcast-angular folder"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if Angular CLI is available
if ! command -v ng &> /dev/null; then
    echo "📦 Installing Angular CLI..."
    npm install -g @angular/cli
fi

echo "📦 Installing dependencies..."
npm install

echo "🔧 Building the application..."
ng build --configuration=development

echo "🌐 Starting development server..."
echo ""
echo "🎯 Demo will be available at:"
echo "   Dashboard: http://localhost:4200"
echo "   AI Agent Demo: http://localhost:4200/agent-demo"
echo ""
echo "👤 Demo User: Gil (pre-loaded with trip history)"
echo "🎪 Ready for hackathon presentation!"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the development server
ng serve --host 0.0.0.0 --port 4200 --open 