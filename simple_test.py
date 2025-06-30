#!/usr/bin/env python3
"""Simple test to see VMware source categories."""

import asyncio
import os
import httpx
import base64
import json
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

async def simple_test():
    """Simple test to debug the issue."""
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
    from_time = (now - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S")
    to_time = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    payload = {
        "query": "*vmware* | count by _sourceCategory | sort by _count desc",
        "from": from_time,
        "to": to_time,
        "timeZone": "UTC"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Create search job
        create_url = f"{endpoint}/api/v1/search/jobs"
        response = await client.post(create_url, headers=headers, json=payload)
        
        if response.status_code == 202:
            job_data = response.json()
            job_id = job_data.get("id")
            print(f"Job created: {job_id}")
            
            # Wait for completion
            status_url = f"{endpoint}/api/v1/search/jobs/{job_id}"
            
            for attempt in range(30):
                await asyncio.sleep(2)
                
                status_response = await client.get(status_url, headers=headers)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    state = status_data.get("state", "unknown")
                    print(f"Attempt {attempt}: State = {state}")
                    
                    if state == "DONE GATHERING RESULTS":
                        record_count = status_data.get("recordCount", 0)
                        print(f"Found {record_count} source categories")
                        
                        # Get the records
                        records_url = f"{endpoint}/api/v1/search/jobs/{job_id}/records?offset=0&limit=20"
                        records_response = await client.get(records_url, headers=headers)
                        
                        print(f"Records response status: {records_response.status_code}")
                        if records_response.status_code == 200:
                            records_data = records_response.json()
                            print(f"Records data keys: {list(records_data.keys())}")
                            records = records_data.get("records", [])
                            print(f"Number of records: {len(records)}")
                            
                            print("VMware Source Categories:")
                            for record in records:
                                source_cat = record.get("_sourceCategory", "unknown")
                                count = record.get("_count", 0)
                                print(f"  - {source_cat}: {count:,} messages")
                        else:
                            print(f"Records request failed: {records_response.text}")
                        break
                    elif state in ["CANCELLED", "FORCE PAUSED", "FAILED"]:
                        print(f"Job {state}")
                        break
            else:
                print("Timeout waiting for job completion")
        else:
            print(f"Job creation failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(simple_test())