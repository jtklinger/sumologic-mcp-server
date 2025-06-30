#!/usr/bin/env python3
"""Detailed exploration of VMware data."""

import asyncio
import os
import httpx
import base64
import json
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

async def explore_vmware_detailed():
    """Explore VMware data structure in detail."""
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
    
    # Create timestamps - wider range
    now = datetime.now(timezone.utc)
    from_time = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    to_time = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Multiple queries to explore VMware data
    queries = [
        ("Count messages", "*vmware* | count"),
        ("Source categories", "*vmware* | count by _sourceCategory | sort by _count desc"),
        ("Source hosts", "*vmware* | count by _sourceHost | sort by _count desc | limit 10"),
        ("Sample messages", "*vmware* | limit 5"),
        ("Look for metrics", "metric=*vmware* | limit 5"),
        ("Look for vcenter", "*vcenter* | limit 5"),
        ("OTel sources", "_sourceCategory=*otel* | limit 5")
    ]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for query_name, query in queries:
            print(f"\n🔍 {query_name}: {query}")
            
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
                    
                    for attempt in range(30):
                        await asyncio.sleep(1)
                        
                        status_response = await client.get(status_url, headers=headers)
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            state = status_data.get("state", "unknown")
                            
                            if state == "DONE GATHERING RESULTS":
                                message_count = status_data.get("messageCount", 0)
                                record_count = status_data.get("recordCount", 0)
                                print(f"   ✅ Completed: {message_count} messages, {record_count} records")
                                
                                # Get results based on query type
                                if "count" in query or "by" in query:
                                    # Aggregation query - use records
                                    records_url = f"{endpoint}/api/v1/search/jobs/{job_id}/records?offset=0&limit=10"
                                    records_response = await client.get(records_url, headers=headers)
                                    
                                    if records_response.status_code == 200:
                                        records_data = records_response.json()
                                        records = records_data.get("records", [])
                                        
                                        print(f"   📊 Results:")
                                        for record in records:
                                            print(f"      {record}")
                                else:
                                    # Raw query - use messages
                                    messages_url = f"{endpoint}/api/v1/search/jobs/{job_id}/messages?offset=0&limit=3"
                                    messages_response = await client.get(messages_url, headers=headers)
                                    
                                    if messages_response.status_code == 200:
                                        messages_data = messages_response.json()
                                        messages = messages_data.get("messages", [])
                                        
                                        print(f"   📄 Sample messages:")
                                        for i, msg in enumerate(messages):
                                            print(f"      Message {i+1}:")
                                            print(f"        Source Category: {msg.get('_sourceCategory', 'N/A')}")
                                            print(f"        Source Host: {msg.get('_sourceHost', 'N/A')}")
                                            print(f"        Raw: {str(msg.get('_raw', 'N/A'))[:100]}...")
                                            # Show other interesting fields
                                            other_fields = {k: v for k, v in msg.items() if not k.startswith('_') and k not in ['_raw']}
                                            if other_fields:
                                                print(f"        Other fields: {list(other_fields.keys())}")
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
    asyncio.run(explore_vmware_detailed())