#!/usr/bin/env python3
"""Test Sumo Logic search functionality."""

import asyncio
import os
from dotenv import load_dotenv
from sumologic_mcp_server.client import SumoLogicClient

load_dotenv()

async def test_search():
    """Test search functionality."""
    print("🔍 Testing Sumo Logic search...")
    
    access_id = os.getenv("SUMO_ACCESS_ID")
    access_key = os.getenv("SUMO_ACCESS_KEY")
    endpoint = os.getenv("SUMO_ENDPOINT")
    
    try:
        client = SumoLogicClient(access_id, access_key, endpoint)
        
        # Test with a simple query to get any data
        print("📊 Executing test search...")
        query = "*"  # Simplest possible query
        result = await client.execute_query(query, "-5m", "now", 5)
        
        print(f"✅ Search successful!")
        print(f"📈 Total records found: {result.total_count}")
        print(f"📋 Returned records: {len(result.records)}")
        print(f"🏷️  Available fields: {len(result.fields)}")
        
        if result.fields:
            print("📄 Available fields:")
            for field in result.fields[:10]:  # Show first 10 fields
                print(f"   - {field.get('name', 'unknown')}: {field.get('fieldType', 'unknown')}")
        
        if result.records:
            print("📋 Sample record keys:")
            sample_keys = list(result.records[0].keys())[:10]
            for key in sample_keys:
                print(f"   - {key}")
        
        return True
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_search())
    exit(0 if success else 1)