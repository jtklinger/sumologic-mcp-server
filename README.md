# Sumo Logic MCP Server

Model Context Protocol (MCP) server for Sumo Logic query execution and data exploration.

## Features

- Execute Sumo Logic search queries
- List source categories and metrics
- Stream real-time query results
- Validate query syntax
- Explore available data sources

## Setup

1. **Install dependencies:**
```bash
pip install -e .
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your Sumo Logic credentials
```

3. **Run the server:**
```bash
sumologic-mcp-server
```

## Configuration

Set these environment variables in `.env`:

```env
SUMO_ACCESS_ID=your_access_id
SUMO_ACCESS_KEY=your_access_key
SUMO_ENDPOINT=https://api.sumologic.com/api
```

## Usage with Claude Code

Once running, Claude Code can use these tools:

- `execute_query` - Run Sumo Logic searches
- `list_sources` - Show available source categories
- `validate_query` - Check query syntax
- `get_metrics` - List available metrics

## Tools Available

### execute_query
Execute a Sumo Logic search query with time range.

### list_source_categories  
List all available source categories in your environment.

### list_metrics
Get available metrics for a specific source category.

### validate_query_syntax
Validate Sumo Logic query syntax without executing.

### get_query_job_status
Check the status of a running query job.