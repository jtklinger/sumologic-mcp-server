#!/usr/bin/env python3
"""Debug search request."""

import asyncio
import os
import httpx
import base64
import json
from dotenv import load_dotenv

load_dotenv()

async def debug_search():
    """Debug search request format."""
    access_id = os.getenv("SUMO_ACCESS_ID")
    access_key = os.getenv("SUMO_ACCESS_KEY")
    endpoint = os.getenv("SUMO_ENDPOINT")
    
    credentials = f"{access_id}:{access_key}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Test different payload formats
    payloads = [
        {
            "query": "*",
            "from": "-5m",
            "to": "now",
            "timeZone": "UTC"
        },
        {
            "query": "*",
            "from": "2024-01-01T00:00:00",
            "to": "2024-01-01T01:00:00",
            "timeZone": "UTC"
        },
        {
            "query": "_sourceCategory=*",
            "from": "-1h",
            "to": "now"
        }
    ]
    
    url = f"{endpoint}/api/v1/search/jobs"
    
    for i, payload in enumerate(payloads):
        print(f"🔍 Testing payload {i+1}: {json.dumps(payload)}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 202:  # Expected for search job creation
                    print(f"   ✅ Success!")
                    data = response.json()
                    print(f"   Job ID: {data.get('id', 'unknown')}")
                    break
                else:
                    print(f"   ❌ Failed")
                    print(f"   Response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    asyncio.run(debug_search())