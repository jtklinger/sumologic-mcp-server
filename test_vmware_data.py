#!/usr/bin/env python3
"""Test for VMware data in Sumo Logic."""

import asyncio
import os
import httpx
import base64
import json
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

async def test_vmware_data():
    """Test for VMware metrics in Sumo Logic."""
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
    
    # Create timestamps for a wider time range
    now = datetime.now(timezone.utc)
    from_time = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    to_time = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Test queries for VMware data
    test_queries = [
        "_sourceCategory=*vmware*",
        "_sourceCategory=*vcenter*", 
        "_sourceCategory=*otel*",
        "metric=vcenter*",
        "vcenter.cluster",
        "*vmware*"
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for query in test_queries:
            print(f"🔍 Testing query: {query}")
            
            payload = {
                "query": query,
                "from": from_time,
                "to": to_time,
                "timeZone": "UTC"
            }
            
            try:
                # Create search job
                create_url = f"{endpoint}/api/v1/search/jobs"
                response = await client.post(create_url, headers=headers, json=payload)
                
                if response.status_code == 202:
                    job_data = response.json()
                    job_id = job_data.get("id")
                    print(f"   Job created: {job_id}")
                    
                    # Wait for completion
                    status_url = f"{endpoint}/api/v1/search/jobs/{job_id}"
                    
                    for attempt in range(15):
                        await asyncio.sleep(1)
                        
                        status_response = await client.get(status_url, headers=headers)
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            state = status_data.get("state", "unknown")
                            
                            if state == "DONE GATHERING RESULTS":
                                message_count = status_data.get("messageCount", 0)
                                record_count = status_data.get("recordCount", 0)
                                print(f"   ✅ Completed: {message_count} messages, {record_count} records")
                                
                                if message_count > 0:
                                    print(f"   🎯 Found VMware data with query: {query}")
                                break
                            elif state in ["CANCELLED", "FORCE PAUSED", "FAILED"]:
                                print(f"   ❌ Job {state}")
                                break
                    else:
                        print(f"   ⏰ Timeout waiting for job completion")
                        
                else:
                    print(f"   ❌ Job creation failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()

if __name__ == "__main__":
    asyncio.run(test_vmware_data())