#!/usr/bin/env python3
"""Test full search flow with proper error handling."""

import asyncio
import os
import httpx
import base64
import json
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

async def test_full_flow():
    """Test the complete search flow."""
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
    
    # Create timestamps
    now = datetime.now(timezone.utc)
    from_time = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    to_time = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    payload = {
        "query": "_sourceCategory=*",
        "from": from_time,
        "to": to_time,
        "timeZone": "UTC"
    }
    
    print(f"🔍 Creating search job...")
    print(f"Query: {payload['query']}")
    print(f"Time range: {from_time} to {to_time}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Create search job
        create_url = f"{endpoint}/api/v1/search/jobs"
        
        try:
            response = await client.post(create_url, headers=headers, json=payload)
            print(f"Create job status: {response.status_code}")
            
            if response.status_code != 202:
                print(f"❌ Job creation failed: {response.text}")
                return
            
            job_data = response.json()
            job_id = job_data.get("id")
            print(f"✅ Job created: {job_id}")
            print(f"Response: {json.dumps(job_data, indent=2)}")
            
            # Step 2: Check job status
            status_url = f"{endpoint}/api/v1/search/jobs/{job_id}"
            
            for attempt in range(10):  # Try up to 10 times
                await asyncio.sleep(1)
                
                status_response = await client.get(status_url, headers=headers)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    state = status_data.get("state", "unknown")
                    print(f"Attempt {attempt + 1}: State = {state}")
                    
                    if state in ["DONE GATHERING RESULTS", "CANCELLED", "FORCE PAUSED"]:
                        print(f"✅ Job completed with state: {state}")
                        
                        # Step 3: Get results if completed successfully
                        if state == "DONE GATHERING RESULTS":
                            records_url = f"{endpoint}/api/v1/search/jobs/{job_id}/records?offset=0&limit=5"
                            
                            records_response = await client.get(records_url, headers=headers)
                            if records_response.status_code == 200:
                                records_data = records_response.json()
                                print(f"✅ Got {len(records_data.get('records', []))} records")
                                print(f"Total count: {records_data.get('totalCount', 0)}")
                                
                                if records_data.get('records'):
                                    print("Sample record keys:")
                                    sample_keys = list(records_data['records'][0].keys())[:10]
                                    for key in sample_keys:
                                        print(f"   - {key}")
                            else:
                                print(f"❌ Failed to get records: {records_response.status_code}")
                        
                        break
                    elif state == "FAILED":
                        print(f"❌ Job failed")
                        break
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    break
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_full_flow())