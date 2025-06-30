#!/usr/bin/env python3
"""Explore VMware data structure."""

import asyncio
import os
import httpx
import base64
import json
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

async def explore_vmware_data():
    """Explore VMware data structure and source categories."""
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
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # First, get source categories for VMware data
        print("🔍 Finding VMware source categories...")
        
        payload = {
            "query": "*vmware* | count by _sourceCategory | sort by _count desc",
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
                            record_count = status_data.get("recordCount", 0)
                            print(f"   ✅ Found {record_count} source categories")
                            
                            # Get the records (aggregation results)
                            records_url = f"{endpoint}/api/v1/search/jobs/{job_id}/records?limit=20"
                            records_response = await client.get(records_url, headers=headers)
                            
                            if records_response.status_code == 200:
                                records_data = records_response.json()
                                records = records_data.get("records", [])
                                
                                print("📊 VMware Source Categories:")
                                for record in records:
                                    source_cat = record.get("_sourceCategory", "unknown")
                                    count = record.get("_count", 0)
                                    print(f"   - {source_cat}: {count:,} messages")
                                
                                print(f"Full records data: {json.dumps(records, indent=2)}")
                                
                                # Now explore the most active source category
                                if records:
                                    top_source = records[0].get("_sourceCategory")
                                    print(f"\n🔬 Exploring top source: {top_source}")
                                    
                                    # Get sample data from top source
                                    sample_payload = {
                                        "query": f'_sourceCategory="{top_source}" | limit 3',
                                        "from": from_time,
                                        "to": to_time,
                                        "timeZone": "UTC"
                                    }
                                    
                                    sample_response = await client.post(create_url, headers=headers, json=sample_payload)
                                    if sample_response.status_code == 202:
                                        sample_job_data = sample_response.json()
                                        sample_job_id = sample_job_data.get("id")
                                        
                                        # Wait for sample job
                                        for attempt in range(15):
                                            await asyncio.sleep(1)
                                            
                                            sample_status_response = await client.get(f"{endpoint}/api/v1/search/jobs/{sample_job_id}", headers=headers)
                                            if sample_status_response.status_code == 200:
                                                sample_status_data = sample_status_response.json()
                                                sample_state = sample_status_data.get("state", "unknown")
                                                
                                                if sample_state == "DONE GATHERING RESULTS":
                                                    # Get sample messages
                                                    messages_url = f"{endpoint}/api/v1/search/jobs/{sample_job_id}/messages?limit=3"
                                                    messages_response = await client.get(messages_url, headers=headers)
                                                    
                                                    if messages_response.status_code == 200:
                                                        messages_data = messages_response.json()
                                                        messages = messages_data.get("messages", [])
                                                        
                                                        print("📄 Sample Messages:")
                                                        for i, msg in enumerate(messages):
                                                            print(f"   Message {i+1}:")
                                                            print(f"     Raw: {str(msg.get('_raw', 'N/A'))[:100]}...")
                                                            print(f"     Fields: {list(msg.keys())[:10]}")
                                                            if 'metric' in msg:
                                                                print(f"     Metric: {msg.get('metric')}")
                                                            print()
                                                    break
                            break
                        elif state in ["CANCELLED", "FORCE PAUSED", "FAILED"]:
                            print(f"   ❌ Job {state}")
                            break
                else:
                    print(f"   ⏰ Timeout waiting for job completion")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(explore_vmware_data())