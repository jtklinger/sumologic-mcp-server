#!/bin/bash

# Sumo Logic MCP Server Startup Script

echo "🚀 Starting Sumo Logic MCP Server"
echo "================================="

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -e ."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please configure your credentials:"
    echo "   cp .env.example .env"
    echo "   # Edit .env with your Sumo Logic credentials"
    exit 1
fi

# Check if required environment variables are set
echo "🔍 Checking environment variables..."
source .env

if [ -z "$SUMO_ACCESS_ID" ] || [ -z "$SUMO_ACCESS_KEY" ]; then
    echo "❌ Missing required environment variables in .env file:"
    echo "   SUMO_ACCESS_ID"
    echo "   SUMO_ACCESS_KEY"
    echo ""
    echo "Please edit .env and add your Sumo Logic credentials"
    exit 1
fi

echo "✅ Environment configured"
echo "🌐 Sumo Logic endpoint: ${SUMO_ENDPOINT:-https://api.sumologic.com/api}"
echo ""
echo "🎯 Starting MCP server..."
echo "   (Press Ctrl+C to stop)"
echo ""

# Start the server
python -m sumologic_mcp_server.server