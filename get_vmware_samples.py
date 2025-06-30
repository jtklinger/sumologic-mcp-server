#!/usr/bin/env python3
"""Get actual VMware message samples."""

import asyncio
import os
import httpx
import base64
import json
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

async def get_vmware_samples():
    """Get actual VMware message samples."""
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
    from_time = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
    to_time = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Queries for the different source categories we found
    queries = [
        ("VMware Metrics", '_sourceCategory="vmware/metrics"'),
        ("VMware Events", '_sourceCategory="vmware/events"')
    ]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for query_name, query in queries:
            print(f"\n🔍 {query_name}")
            print(f"Query: {query} | limit 3")
            
            payload = {
                "query": f"{query} | limit 3",
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
                    
                    for attempt in range(20):
                        await asyncio.sleep(1)
                        
                        status_response = await client.get(status_url, headers=headers)
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            state = status_data.get("state", "unknown")
                            
                            if state == "DONE GATHERING RESULTS":
                                message_count = status_data.get("messageCount", 0)
                                print(f"   ✅ Found {message_count} messages")
                                
                                # Get raw messages
                                messages_url = f"{endpoint}/api/v1/search/jobs/{job_id}/messages?offset=0&limit=3"
                                messages_response = await client.get(messages_url, headers=headers)
                                
                                if messages_response.status_code == 200:
                                    messages_data = messages_response.json()
                                    messages = messages_data.get("messages", [])
                                    
                                    print(f"   📄 Sample messages ({len(messages)}):")
                                    for i, msg in enumerate(messages):
                                        print(f"\n      Message {i+1}:")
                                        print(f"        Full message structure:")
                                        print(f"        {json.dumps(msg, indent=8, default=str)}")
                                else:
                                    print(f"   ❌ Messages request failed: {messages_response.status_code}")
                                break
                            elif state in ["CANCELLED", "FORCE PAUSED", "FAILED"]:
                                print(f"   ❌ Job {state}")
                                break
                    else:
                        print(f"   ⏰ Timeout")
                else:
                    print(f"   ❌ Job creation failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_vmware_samples())