#!/usr/bin/env python3
"""Detailed debug of search API."""

import asyncio
import os
import httpx
import base64
import json
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

async def detailed_debug():
    """Detailed debug of search request."""
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
    
    # Use the working timestamp format from earlier
    now = datetime.now(timezone.utc)
    from_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    to_time = datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
    
    payload = {
        "query": "*",
        "from": from_time.isoformat(),
        "to": to_time.isoformat(),
        "timeZone": "UTC"
    }
    
    print(f"🔍 Testing with payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    url = f"{endpoint}/api/v1/search/jobs"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 202:
                print("✅ Success!")
                data = response.json()
                print(f"Job ID: {data.get('id')}")
                print(f"State: {data.get('state')}")
            else:
                print("❌ Failed")
                print("Response text:")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(detailed_debug())