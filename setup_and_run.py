#!/usr/bin/env python3
"""Setup and run script for Sumo Logic MCP Server."""

import os
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 10):
        print("Error: Python 3.10 or higher is required")
        return False
    return True


def install_dependencies():
    """Install dependencies using pip."""
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def check_environment():
    """Check if environment variables are set."""
    required_vars = ["SUMO_ACCESS_ID", "SUMO_ACCESS_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables or create a .env file")
        print("You can copy .env.example to .env and fill in your credentials")
        return False
    
    print("✅ Environment variables are set")
    return True


def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from .env.example...")
        env_file.write_text(env_example.read_text())
        print("✅ Created .env file")
        print("Please edit .env and add your Sumo Logic credentials")
        return False
    
    return True


def run_server():
    """Run the MCP server."""
    print("Starting Sumo Logic MCP Server...")
    try:
        subprocess.run([sys.executable, "-m", "sumologic_mcp_server.server"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        return True


def main():
    """Main setup and run function."""
    print("🚀 Sumo Logic MCP Server Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create .env file if needed
    if not create_env_file():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Check environment
    if not check_environment():
        return 1
    
    # Run server
    if not run_server():
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())