#!/usr/bin/env python3
"""Test getting records from completed job."""

import asyncio
import os
import httpx
import base64
from dotenv import load_dotenv

load_dotenv()

async def test_records():
    """Test getting records with different parameters."""
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
    
    # Use the job ID from the previous successful run
    job_id = "73F31E959E020D47"  # From previous test
    
    # Try different record request formats
    record_urls = [
        f"{endpoint}/api/v1/search/jobs/{job_id}/records",
        f"{endpoint}/api/v1/search/jobs/{job_id}/records?offset=0&limit=5",
        f"{endpoint}/api/v1/search/jobs/{job_id}/records?limit=5"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in record_urls:
            print(f"🔍 Testing: {url}")
            
            try:
                response = await client.get(url, headers=headers)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ Success!")
                    data = response.json()
                    print(f"   Records: {len(data.get('records', []))}")
                    print(f"   Total: {data.get('totalCount', 0)}")
                    break
                else:
                    print(f"   ❌ Failed")
                    print(f"   Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()

if __name__ == "__main__":
    asyncio.run(test_records())