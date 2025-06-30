#!/usr/bin/env python3
"""Test different Sumo Logic endpoints."""

import asyncio
import os
import httpx
import base64
from dotenv import load_dotenv

load_dotenv()

async def test_endpoint(endpoint_url):
    """Test a specific endpoint."""
    access_id = os.getenv("SUMO_ACCESS_ID")
    access_key = os.getenv("SUMO_ACCESS_KEY")
    
    credentials = f"{access_id}:{access_key}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Test collectors endpoint first (simpler than search)
    test_url = f"{endpoint_url}/v1/collectors"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(test_url, headers=headers)
            if response.status_code == 200:
                print(f"✅ {endpoint_url} - Working!")
                data = response.json()
                print(f"   Found {len(data.get('collectors', []))} collectors")
                return True
            else:
                print(f"❌ {endpoint_url} - HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ {endpoint_url} - Error: {e}")
        return False

async def main():
    """Test common Sumo Logic endpoints."""
    print("🔍 Testing Sumo Logic API endpoints...")
    print("=" * 50)
    
    # Common Sumo Logic endpoints
    endpoints = [
        "https://api.sumologic.com/api",
        "https://api.us2.sumologic.com/api", 
        "https://api.eu.sumologic.com/api",
        "https://api.au.sumologic.com/api",
        "https://api.de.sumologic.com/api",
        "https://api.jp.sumologic.com/api",
        "https://api.ca.sumologic.com/api",
        "https://service.sumologic.com/api",
        "https://long-api-name.sumologic.com/api"
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints:
        if await test_endpoint(endpoint):
            working_endpoints.append(endpoint)
    
    print("\n" + "=" * 50)
    if working_endpoints:
        print(f"✅ Working endpoints:")
        for endpoint in working_endpoints:
            print(f"   {endpoint}")
        print(f"\nUpdate your .env file with the working endpoint!")
    else:
        print("❌ No working endpoints found. Check your credentials.")

if __name__ == "__main__":
    asyncio.run(main())