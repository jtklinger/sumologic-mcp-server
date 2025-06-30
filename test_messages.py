#!/usr/bin/env python3
"""Test getting messages from completed job."""

import asyncio
import os
import httpx
import base64
from dotenv import load_dotenv

load_dotenv()

async def test_messages():
    """Test getting messages from search job."""
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
    job_id = "73F31E959E020D47"
    
    # Try messages endpoint
    messages_url = f"{endpoint}/api/v1/search/jobs/{job_id}/messages?offset=0&limit=5"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"🔍 Testing messages endpoint: {messages_url}")
        
        try:
            response = await client.get(messages_url, headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Success!")
                data = response.json()
                print(f"Messages: {len(data.get('messages', []))}")
                print(f"Total: {data.get('totalCount', 0)}")
                
                if data.get('messages'):
                    print("Sample message:")
                    sample_msg = data['messages'][0]
                    print(f"  Raw message: {sample_msg.get('_raw', 'N/A')[:100]}...")
                    print(f"  Source Category: {sample_msg.get('_sourceCategory', 'N/A')}")
                    print(f"  Source Host: {sample_msg.get('_sourceHost', 'N/A')}")
                    
            else:
                print(f"❌ Failed")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_messages())