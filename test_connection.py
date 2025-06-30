#!/usr/bin/env python3
"""Test Sumo Logic connection."""

import asyncio
import os
from dotenv import load_dotenv
from sumologic_mcp_server.client import SumoLogicClient

load_dotenv()

async def test_connection():
    """Test connection to Sumo Logic."""
    print("🔍 Testing Sumo Logic connection...")
    
    access_id = os.getenv("SUMO_ACCESS_ID")
    access_key = os.getenv("SUMO_ACCESS_KEY")
    endpoint = os.getenv("SUMO_ENDPOINT", "https://api.sumologic.com/api")
    
    if not access_id or not access_key:
        print("❌ Missing credentials in .env file")
        return False
    
    try:
        client = SumoLogicClient(access_id, access_key, endpoint)
        
        # Test with a simple query to get source categories
        print("📊 Executing test query...")
        query = "_sourceCategory=* | limit 1"
        result = await client.execute_query(query, "-1h", "now", 1)
        
        print(f"✅ Connection successful!")
        print(f"📈 Found {result.total_count} total records")
        print(f"🏷️  Available fields: {len(result.fields)}")
        
        if result.records:
            print("📋 Sample record fields:")
            for key in list(result.records[0].keys())[:5]:
                print(f"   - {key}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)