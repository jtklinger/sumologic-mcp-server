"""Sumo Logic API client for MCP server."""

import asyncio
import base64
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel


class SearchJob(BaseModel):
    """Represents a Sumo Logic search job."""
    id: str
    state: str
    query: str
    from_time: str
    to_time: str
    message_count: Optional[int] = None
    record_count: Optional[int] = None


class SearchResult(BaseModel):
    """Represents search results from Sumo Logic."""
    records: List[Dict[str, Any]]
    fields: List[Dict[str, str]]
    total_count: int
    job_id: str


class SumoLogicClient:
    """Async client for Sumo Logic Search API."""
    
    def __init__(
        self, 
        access_id: str, 
        access_key: str, 
        endpoint: str = "https://api.sumologic.com/api",
        timeout: int = 300
    ):
        self.access_id = access_id
        self.access_key = access_key
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        
        # Create auth header
        credentials = f"{access_id}:{access_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _parse_time(self, time_str: str) -> str:
        """Convert relative time strings to absolute timestamps."""
        if time_str == "now":
            return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        
        # Handle relative times like "-1h", "-5m", "-24h"
        if time_str.startswith("-"):
            try:
                # Parse relative time
                if time_str.endswith("m"):
                    minutes = int(time_str[1:-1])
                    dt = datetime.now(timezone.utc) - timedelta(minutes=minutes)
                elif time_str.endswith("h"):
                    hours = int(time_str[1:-1])
                    dt = datetime.now(timezone.utc) - timedelta(hours=hours)
                elif time_str.endswith("d"):
                    days = int(time_str[1:-1])
                    dt = datetime.now(timezone.utc) - timedelta(days=days)
                else:
                    # Default to hours if no unit specified
                    hours = int(time_str[1:])
                    dt = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                return dt.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                # If parsing fails, return as-is (might be absolute timestamp)
                return time_str
        
        # If it looks like an absolute timestamp, return as-is
        return time_str
    
    async def create_search_job(
        self, 
        query: str, 
        from_time: str = "-1h", 
        to_time: str = "now",
        time_zone: str = "UTC"
    ) -> SearchJob:
        """Create a new search job."""
        url = f"{self.endpoint}/api/v1/search/jobs"
        
        # Convert relative times to absolute timestamps
        from_timestamp = self._parse_time(from_time)
        to_timestamp = self._parse_time(to_time)
        
        payload = {
            "query": query,
            "from": from_timestamp,
            "to": to_timestamp,
            "timeZone": time_zone
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return SearchJob(
                id=data["id"],
                state=data.get("state", "NOT_STARTED"),  # API doesn't return state initially
                query=query,
                from_time=from_time,
                to_time=to_time
            )
    
    async def get_search_job_status(self, job_id: str) -> SearchJob:
        """Get the status of a search job."""
        url = f"{self.endpoint}/api/v1/search/jobs/{job_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return SearchJob(
                id=data["id"],
                state=data["state"],
                query=data.get("query", ""),
                from_time=data.get("from", ""),
                to_time=data.get("to", ""),
                message_count=data.get("messageCount"),
                record_count=data.get("recordCount")
            )
    
    async def wait_for_job_completion(self, job_id: str, poll_interval: int = 2) -> SearchJob:
        """Wait for a search job to complete."""
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            job = await self.get_search_job_status(job_id)
            
            if job.state in ["DONE GATHERING RESULTS", "CANCELLED", "FORCE PAUSED"]:
                return job
            elif job.state == "FAILED":
                raise Exception(f"Search job {job_id} failed")
            
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Search job {job_id} timed out after {self.timeout} seconds")
    
    async def get_search_job_records(
        self, 
        job_id: str, 
        offset: int = 0, 
        limit: int = 1000
    ) -> SearchResult:
        """Get records from a completed search job."""
        url = f"{self.endpoint}/api/v1/search/jobs/{job_id}/records"
        
        params = {
            "offset": offset,
            "limit": limit
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return SearchResult(
                records=data.get("records", []),
                fields=data.get("fields", []),
                total_count=data.get("totalCount", 0),
                job_id=job_id
            )
    
    async def execute_query(
        self, 
        query: str, 
        from_time: str = "-1h", 
        to_time: str = "now",
        limit: int = 1000
    ) -> SearchResult:
        """Execute a query and return results."""
        # Create search job
        job = await self.create_search_job(query, from_time, to_time)
        
        # Wait for completion
        completed_job = await self.wait_for_job_completion(job.id)
        
        # Get results
        return await self.get_search_job_records(completed_job.id, limit=limit)
    
    async def get_collectors(self) -> List[Dict[str, Any]]:
        """Get list of collectors."""
        url = f"{self.endpoint}/api/v1/collectors"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("collectors", [])
    
    async def get_sources(self, collector_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of sources, optionally filtered by collector."""
        if collector_id:
            url = f"{self.endpoint}/api/v1/collectors/{collector_id}/sources"
        else:
            # Get all sources by iterating through collectors
            collectors = await self.get_collectors()
            all_sources = []
            
            for collector in collectors:
                try:
                    collector_url = f"{self.endpoint}/api/v1/collectors/{collector['id']}/sources"
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(collector_url, headers=self.headers)
                        if response.status_code == 200:
                            data = response.json()
                            sources = data.get("sources", [])
                            for source in sources:
                                source["collector_name"] = collector.get("name", "")
                                source["collector_id"] = collector["id"]
                            all_sources.extend(sources)
                except Exception:
                    # Skip collectors that can't be accessed
                    continue
            
            return all_sources
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("sources", [])
    
    async def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate query syntax without executing."""
        # For now, we'll do a dry run by creating a job with a very short time range
        # and immediately cancelling it. This is a workaround as Sumo doesn't have
        # a dedicated syntax validation endpoint.
        try:
            job = await self.create_search_job(query, "-1m", "now")
            
            # Try to cancel the job immediately
            cancel_url = f"{self.endpoint}/api/v1/search/jobs/{job.id}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.delete(cancel_url, headers=self.headers)
            
            return {"valid": True, "message": "Query syntax is valid"}
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    return {
                        "valid": False, 
                        "message": error_data.get("message", "Invalid query syntax")
                    }
                except:
                    return {"valid": False, "message": "Invalid query syntax"}
            else:
                raise e