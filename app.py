import os
from fastmcp import FastMCP

from duckduckgo_search import DuckDuckGoSearcher
from goggles import GogglesApi
from web_wrapper import WebWrapper

# Get Goggles URL from environment variable, with fallback to default
GOGGLES_URL = os.getenv("GOGGLES_URL", "http://localhost:8001")

# Initialize the services
goggles = GogglesApi(GOGGLES_URL)
web_wrapper = WebWrapper(goggles)
searcher = DuckDuckGoSearcher()

# Create MCP server
mcp = FastMCP("Web Search MCP Server")

@mcp.tool
def search_web(query: str) -> dict:
    """Perform a web search using DuckDuckGo.
    
    Args:
        query: The search query string
        
    Returns:
        Dictionary containing the search query and results with titles, URLs, and snippets
    """
    try:
        results = searcher.search(query)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {
            "query": query,
            "results": [],
            "error": str(e)
        }


@mcp.tool
def get_url_content(url: str, offset: int = 0, limit: int = 10000) -> dict:
    """Retrieve the content from a given URL with pagination support.
    
    Args:
        url: The URL to fetch content from
        offset: Character position to start from (default: 0)
        limit: Maximum characters to return (default: 10000, max: 50000)
        
    Returns:
        Dictionary containing the URL, content (paginated), description, and pagination info
    """
    try:
        code, full_content, description = web_wrapper.get_markdown_for_url(url)
        
        # Apply pagination
        total_length = len(full_content)
        end_offset = min(offset + limit, total_length)
        paginated_content = full_content[offset:end_offset]
        
        return {
            "url": url,
            "status_code": code,
            "content": paginated_content,
            "description": description,
            "format": "markdown",
            "pagination": {
                "offset": offset,
                "limit": limit,
                "returned": len(paginated_content),
                "total": total_length,
                "has_more": end_offset < total_length
            }
        }
    except Exception as e:
        return {
            "url": url,
            "status_code": 500,
            "content": "",
            "error": str(e),
            "pagination": {
                "offset": offset,
                "limit": limit,
                "returned": 0,
                "total": 0,
                "has_more": False
            }
        }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
