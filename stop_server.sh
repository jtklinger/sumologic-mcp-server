#!/bin/bash

# Stop Sumo Logic MCP Server

echo "🛑 Stopping Sumo Logic MCP Server..."

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

# Check if PID file exists
if [ -f "mcp_server.pid" ]; then
    MCP_PID=$(cat mcp_server.pid)
    
    if kill -0 $MCP_PID 2>/dev/null; then
        echo "🔄 Stopping server with PID: $MCP_PID"
        kill $MCP_PID
        sleep 1
        
        if kill -0 $MCP_PID 2>/dev/null; then
            echo "⚡ Force killing server..."
            kill -9 $MCP_PID
        fi
        
        echo "✅ Server stopped"
    else
        echo "ℹ️  Server was not running"
    fi
    
    rm -f mcp_server.pid
else
    echo "ℹ️  No PID file found"
    # Try to kill any running servers
    pkill -f "sumologic_mcp_server.server" && echo "✅ Killed running servers" || echo "ℹ️  No servers found"
fi

echo "🏁 Done"