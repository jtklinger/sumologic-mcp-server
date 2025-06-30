"""MCP server for Sumo Logic integration."""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Sequence

from dotenv import load_dotenv
from mcp.server import Server
from mcp import McpError
from mcp.types import (
    EmptyResult,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)

from .client import SumoLogicClient


# Load environment variables
load_dotenv()

app = Server("sumologic-mcp-server")

# Initialize Sumo Logic client
sumo_client = None


def get_sumo_client() -> SumoLogicClient:
    """Get or create Sumo Logic client."""
    global sumo_client
    
    if sumo_client is None:
        access_id = os.getenv("SUMO_ACCESS_ID")
        access_key = os.getenv("SUMO_ACCESS_KEY")
        endpoint = os.getenv("SUMO_ENDPOINT", "https://api.sumologic.com/api")
        timeout = int(os.getenv("QUERY_TIMEOUT", "300"))
        
        if not access_id or not access_key:
            raise ValueError(
                "SUMO_ACCESS_ID and SUMO_ACCESS_KEY environment variables must be set"
            )
        
        sumo_client = SumoLogicClient(access_id, access_key, endpoint, timeout)
    
    return sumo_client


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="execute_query",
            description="Execute a Sumo Logic search query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The Sumo Logic search query to execute"
                    },
                    "from_time": {
                        "type": "string",
                        "description": "Start time for the search (e.g., '-1h', '-24h', '2023-01-01T00:00:00')",
                        "default": "-1h"
                    },
                    "to_time": {
                        "type": "string", 
                        "description": "End time for the search (e.g., 'now', '2023-01-01T23:59:59')",
                        "default": "now"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 1000,
                        "minimum": 1,
                        "maximum": 10000
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_source_categories",
            description="List all available source categories",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Optional pattern to filter source categories (e.g., 'otel', 'vmware')"
                    }
                }
            }
        ),
        Tool(
            name="list_metrics",
            description="Get available metrics for a source category",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_category": {
                        "type": "string",
                        "description": "Source category to analyze (e.g., 'otel/vmware')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of metrics to return",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["source_category"]
            }
        ),
        Tool(
            name="validate_query_syntax",
            description="Validate Sumo Logic query syntax without executing",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The Sumo Logic query to validate"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_sample_data",
            description="Get sample data from a source category to understand structure",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_category": {
                        "type": "string",
                        "description": "Source category to sample (e.g., 'otel/vmware')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of sample records to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["source_category"]
            }
        ),
        Tool(
            name="explore_vmware_metrics",
            description="Explore available VMware metrics and their attributes",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_category": {
                        "type": "string",
                        "description": "VMware source category (default: 'otel/vmware')",
                        "default": "otel/vmware"
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle tool calls."""
    try:
        client = get_sumo_client()
        
        if name == "execute_query":
            return await execute_query_tool(client, arguments)
        elif name == "list_source_categories":
            return await list_source_categories_tool(client, arguments)
        elif name == "list_metrics":
            return await list_metrics_tool(client, arguments)
        elif name == "validate_query_syntax":
            return await validate_query_syntax_tool(client, arguments)
        elif name == "get_sample_data":
            return await get_sample_data_tool(client, arguments)
        elif name == "explore_vmware_metrics":
            return await explore_vmware_metrics_tool(client, arguments)
        else:
            raise McpError(INVALID_PARAMS, f"Unknown tool: {name}")
            
    except Exception as e:
        raise McpError(INTERNAL_ERROR, f"Tool execution failed: {str(e)}")


async def execute_query_tool(
    client: SumoLogicClient, 
    arguments: Dict[str, Any]
) -> Sequence[TextContent]:
    """Execute a Sumo Logic query."""
    query = arguments["query"]
    from_time = arguments.get("from_time", "-1h")
    to_time = arguments.get("to_time", "now")
    limit = arguments.get("limit", 1000)
    
    result = await client.execute_query(query, from_time, to_time, limit)
    
    # Format results for better readability
    output = []
    output.append(f"Query: {query}")
    output.append(f"Time range: {from_time} to {to_time}")
    output.append(f"Total results: {result.total_count}")
    output.append(f"Returned: {len(result.records)}")
    output.append("=" * 50)
    
    if result.fields:
        output.append("Fields:")
        for field in result.fields[:10]:  # Show first 10 fields
            output.append(f"  - {field.get('name', 'unknown')}: {field.get('fieldType', 'unknown')}")
        if len(result.fields) > 10:
            output.append(f"  ... and {len(result.fields) - 10} more fields")
        output.append("")
    
    if result.records:
        output.append("Sample Records:")
        for i, record in enumerate(result.records[:5]):  # Show first 5 records
            output.append(f"Record {i + 1}:")
            record_json = json.dumps(record, indent=2, default=str)
            output.append(record_json)
            output.append("")
        
        if len(result.records) > 5:
            output.append(f"... and {len(result.records) - 5} more records")
    
    return [TextContent(type="text", text="\n".join(output))]


async def list_source_categories_tool(
    client: SumoLogicClient,
    arguments: Dict[str, Any]
) -> Sequence[TextContent]:
    """List available source categories."""
    pattern = arguments.get("pattern", "")
    
    sources = await client.get_sources()
    
    # Extract unique source categories
    categories = set()
    for source in sources:
        category = source.get("category", "")
        if category and (not pattern or pattern.lower() in category.lower()):
            categories.add(category)
    
    output = []
    output.append(f"Found {len(categories)} source categories")
    if pattern:
        output.append(f"Filtered by pattern: '{pattern}'")
    output.append("=" * 50)
    
    for category in sorted(categories):
        output.append(f"  - {category}")
    
    return [TextContent(type="text", text="\n".join(output))]


async def list_metrics_tool(
    client: SumoLogicClient,
    arguments: Dict[str, Any]
) -> Sequence[TextContent]:
    """List available metrics for a source category."""
    source_category = arguments["source_category"]
    limit = arguments.get("limit", 100)
    
    # Query to get distinct metrics
    query = f'_sourceCategory="{source_category}" | distinct metric | limit {limit}'
    
    result = await client.execute_query(query, "-24h", "now", limit)
    
    output = []
    output.append(f"Metrics in source category: {source_category}")
    output.append(f"Found {len(result.records)} unique metrics")
    output.append("=" * 50)
    
    for record in result.records:
        metric = record.get("metric", "unknown")
        output.append(f"  - {metric}")
    
    return [TextContent(type="text", text="\n".join(output))]


async def validate_query_syntax_tool(
    client: SumoLogicClient,
    arguments: Dict[str, Any]
) -> Sequence[TextContent]:
    """Validate query syntax."""
    query = arguments["query"]
    
    validation_result = await client.validate_query(query)
    
    output = []
    output.append(f"Query: {query}")
    output.append("=" * 50)
    
    if validation_result["valid"]:
        output.append("✅ Query syntax is valid")
    else:
        output.append("❌ Query syntax is invalid")
        output.append(f"Error: {validation_result['message']}")
    
    return [TextContent(type="text", text="\n".join(output))]


async def get_sample_data_tool(
    client: SumoLogicClient,
    arguments: Dict[str, Any]
) -> Sequence[TextContent]:
    """Get sample data from a source category."""
    source_category = arguments["source_category"]
    limit = arguments.get("limit", 10)
    
    query = f'_sourceCategory="{source_category}" | limit {limit}'
    
    result = await client.execute_query(query, "-1h", "now", limit)
    
    output = []
    output.append(f"Sample data from: {source_category}")
    output.append(f"Showing {len(result.records)} records")
    output.append("=" * 50)
    
    if result.fields:
        output.append("Available Fields:")
        for field in result.fields:
            output.append(f"  - {field.get('name', 'unknown')}: {field.get('fieldType', 'unknown')}")
        output.append("")
    
    for i, record in enumerate(result.records):
        output.append(f"Record {i + 1}:")
        record_json = json.dumps(record, indent=2, default=str)
        output.append(record_json)
        output.append("")
    
    return [TextContent(type="text", text="\n".join(output))]


async def explore_vmware_metrics_tool(
    client: SumoLogicClient,
    arguments: Dict[str, Any]
) -> Sequence[TextContent]:
    """Explore VMware metrics and attributes."""
    source_category = arguments.get("source_category", "otel/vmware")
    
    output = []
    output.append(f"Exploring VMware metrics in: {source_category}")
    output.append("=" * 50)
    
    # Get available metrics
    metrics_query = f'_sourceCategory="{source_category}" | distinct metric | limit 50'
    metrics_result = await client.execute_query(metrics_query, "-24h", "now", 50)
    
    output.append(f"Available Metrics ({len(metrics_result.records)}):")
    for record in metrics_result.records:
        metric = record.get("metric", "unknown")
        output.append(f"  - {metric}")
    output.append("")
    
    # Get available resource attributes for VM metrics
    if metrics_result.records:
        sample_metric = metrics_result.records[0].get("metric", "")
        if sample_metric:
            attrs_query = f'_sourceCategory="{source_category}" metric="{sample_metric}" | limit 5'
            attrs_result = await client.execute_query(attrs_query, "-1h", "now", 5)
            
            if attrs_result.records:
                output.append("Sample Record with Attributes:")
                sample_record = attrs_result.records[0]
                
                # Extract resource attributes (keys starting with 'vcenter.')
                resource_attrs = {k: v for k, v in sample_record.items() if k.startswith('vcenter.')}
                
                if resource_attrs:
                    output.append("VMware Resource Attributes:")
                    for attr, value in resource_attrs.items():
                        output.append(f"  - {attr}: {value}")
                
                output.append("")
                output.append("Full Sample Record:")
                record_json = json.dumps(sample_record, indent=2, default=str)
                output.append(record_json)
    
    return [TextContent(type="text", text="\n".join(output))]


def main():
    """Main entry point for the MCP server."""
    import sys
    from mcp.server.stdio import stdio_server
    
    # Validate environment variables
    if not os.getenv("SUMO_ACCESS_ID") or not os.getenv("SUMO_ACCESS_KEY"):
        print("Error: SUMO_ACCESS_ID and SUMO_ACCESS_KEY environment variables must be set", file=sys.stderr)
        print("Please copy .env.example to .env and configure your credentials", file=sys.stderr)
        return 1
    
    print(f"Starting Sumo Logic MCP Server", file=sys.stderr)
    print(f"Sumo Logic endpoint: {os.getenv('SUMO_ENDPOINT', 'https://api.sumologic.com/api')}", file=sys.stderr)
    print("Server ready for connections...", file=sys.stderr)
    
    # Run the MCP server
    asyncio.run(stdio_server(app))
    return 0


if __name__ == "__main__":
    exit(main())