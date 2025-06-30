#!/bin/bash

# Start Sumo Logic MCP Server in background

echo "🚀 Starting Sumo Logic MCP Server in background..."

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    exit 1
fi

# Start server in background and save PID
echo "🎯 Starting MCP server..."
python -m sumologic_mcp_server.server &
MCP_PID=$!

echo "✅ MCP Server started with PID: $MCP_PID"
echo "📝 Server PID saved to mcp_server.pid"
echo "$MCP_PID" > mcp_server.pid

echo ""
echo "🔧 To connect Claude Code to this server, use:"
echo "   Server command: python"
echo "   Server args: ['-m', 'sumologic_mcp_server.server']"
echo "   Working directory: $DIR"
echo ""
echo "🛑 To stop the server, run:"
echo "   ./stop_server.sh"
echo "   or kill $MCP_PID"

# Keep script running to show status
sleep 2
if kill -0 $MCP_PID 2>/dev/null; then
    echo "✅ Server is running and ready for connections"
else
    echo "❌ Server failed to start"
    exit 1
fi