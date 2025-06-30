#!/usr/bin/env python3
"""Test time parsing and search payload."""

import asyncio
import os
from dotenv import load_dotenv
from sumologic_mcp_server.client import SumoLogicClient

load_dotenv()

async def test_time_parsing():
    """Test time parsing functionality."""
    client = SumoLogicClient(
        os.getenv("SUMO_ACCESS_ID"),
        os.getenv("SUMO_ACCESS_KEY"),
        os.getenv("SUMO_ENDPOINT")
    )
    
    # Test time parsing
    print("🕐 Testing time parsing:")
    test_times = ["-5m", "-1h", "-24h", "now"]
    
    for time_str in test_times:
        parsed = client._parse_time(time_str)
        print(f"   {time_str} -> {parsed}")
    
    print()
    
    # Test with a simple query that should work
    print("🔍 Testing simple search with parsed times...")
    
    try:
        query = "_sourceCategory=*"  # More specific than just "*"
        from_time = "-1h"
        to_time = "now"
        
        print(f"Query: {query}")
        print(f"From: {from_time} -> {client._parse_time(from_time)}")
        print(f"To: {to_time} -> {client._parse_time(to_time)}")
        
        job = await client.create_search_job(query, from_time, to_time)
        print(f"✅ Search job created: {job.id}")
        print(f"   State: {job.state}")
        
        # Wait a bit and check status
        await asyncio.sleep(2)
        status = await client.get_search_job_status(job.id)
        print(f"   Updated state: {status.state}")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        
        # Try with an even simpler query
        print("🔄 Trying with minimal query...")
        try:
            simple_query = "*"
            job = await client.create_search_job(simple_query, from_time, to_time)
            print(f"✅ Simple search worked: {job.id}")
        except Exception as e2:
            print(f"❌ Simple search also failed: {e2}")

if __name__ == "__main__":
    asyncio.run(test_time_parsing())