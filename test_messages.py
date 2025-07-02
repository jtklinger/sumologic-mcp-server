#!/usr/bin/env python3
"""
Test getting messages vs records from Sumo Logic API.
"""

import os
import asyncio
import json
import httpx
from sumologic_mcp_server.client import SumoLogicClient
from dotenv import load_dotenv

async def test_messages_vs_records():
    """Test both messages and records endpoints."""
    # Load environment variables
    load_dotenv()
    
    # Initialize Sumo Logic client
    client = SumoLogicClient(
        access_id=os.getenv('SUMO_ACCESS_ID'),
        access_key=os.getenv('SUMO_ACCESS_KEY'),
        endpoint=os.getenv('SUMO_ENDPOINT', 'https://api.sumologic.com')
    )
    
    print("🔍 Testing Messages vs Records")
    
    # Test with a query that might have VMware data
    query = '_sourceCategory=vmware*'
    
    try:
        # Create search job
        url = f"{client.endpoint}/api/v1/search/jobs"
        payload = {
            "query": query,
            "from": client._parse_time("-24h"),
            "to": client._parse_time("now"),
            "timeZone": "UTC"
        }
        
        print(f"Creating search job for: {query}")
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(url, headers=client.headers, json=payload)
            
            if response.status_code in [200, 202]:
                data = response.json()
                job_id = data["id"]
                print(f"✅ Job created: {job_id}")
            else:
                print(f"❌ Failed to create job: {response.status_code}")
                print(response.text)
                return
        
        # Wait for completion
        print("Waiting for job completion...")
        max_attempts = 30
        for attempt in range(max_attempts):
            status_url = f"{client.endpoint}/api/v1/search/jobs/{job_id}"
            
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                response = await http_client.get(status_url, headers=client.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    state = data.get("state", "UNKNOWN")
                    message_count = data.get("messageCount", 0)
                    record_count = data.get("recordCount", 0)
                    
                    print(f"Attempt {attempt + 1}: {state} (messages: {message_count}, records: {record_count})")
                    
                    if state == "DONE GATHERING RESULTS":
                        break
                    elif state in ["CANCELLED", "FORCE PAUSED", "FAILED"]:
                        print(f"❌ Job ended with state: {state}")
                        return
                else:
                    print(f"❌ Status check failed: {response.status_code}")
                    return
            
            await asyncio.sleep(2)
        
        if state != "DONE GATHERING RESULTS":
            print("❌ Job did not complete in time")
            return
        
        # Test messages endpoint
        print(f"\n{'='*50}")
        print("TESTING MESSAGES ENDPOINT")
        print(f"{'='*50}")
        
        messages_url = f"{client.endpoint}/api/v1/search/jobs/{job_id}/messages"
        params = {"offset": 0, "limit": 5}
        
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.get(messages_url, headers=client.headers, params=params)
            print(f"Messages response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                print(f"✅ Got {len(messages)} messages")
                
                if messages:
                    print("Sample messages:")
                    for i, message in enumerate(messages[:3]):
                        print(f"  Message {i+1}:")
                        print(f"    Raw: {message.get('raw_message', 'N/A')}")
                        print(f"    Time: {message.get('time', 'N/A')}")
                        print()
                else:
                    print("No messages found")
            else:
                print(f"❌ Messages request failed: {response.status_code}")
                print(response.text)
        
        # Test records endpoint
        print(f"\n{'='*50}")
        print("TESTING RECORDS ENDPOINT")
        print(f"{'='*50}")
        
        records_url = f"{client.endpoint}/api/v1/search/jobs/{job_id}/records"
        params = {"offset": 0, "limit": 5}
        
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.get(records_url, headers=client.headers, params=params)
            print(f"Records response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                records = data.get("records", [])
                print(f"✅ Got {len(records)} records")
                
                if records:
                    print("Sample records:")
                    for i, record in enumerate(records[:3]):
                        print(f"  Record {i+1}: {json.dumps(record, indent=4)}")
                else:
                    print("No records found")
            else:
                print(f"❌ Records request failed: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_messages_vs_records())