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
    Snippets are from cached information, use the get_url_content tool to fetch the latest content from a specific URL
    when you need the most up-to-date information (weather, news, etc.).
    
    Args:
        query: The search query string
        
    Returns:
        Dictionary containing the search query and results with titles, URLs, and snippets
    """
    try:
        results = searcher.search(query)
        return {
            "query": query,
            "count": len(results),
            "results": results,
            "error": None
        }
    except Exception as e:
        return {
            "query": query,
            "count": 0,
            "results": [],
            "error": str(e)
        }


@mcp.tool
def get_url_content(url: str, page: int = 1, page_size: int = 50000) -> dict:
    """Retrieve the content from a given URL with pagination support.
    Use to get the most up-to-date (live) information from a specific URL (weather, news, etc.).
    
    Args:
        url: The URL to fetch content from
        page: Page number to retrieve (default: 1)
        page_size: Maximum characters to return per page (default: 50000)
        
    Returns:
        Dictionary containing the URL, content (paginated), description, and pagination info
    """
    try:
        code, full_content, description = web_wrapper.get_markdown_for_url(url)
        
        # Apply pagination
        total_length = len(full_content)
        total_pages = (total_length + page_size - 1) // page_size  # Calculate total pages
        start_offset = (page - 1) * page_size
        end_offset = min(start_offset + page_size, total_length)
        paginated_content = full_content[start_offset:end_offset]
        
        return {
            "url": url,
            "status_code": code,
            "description": description,
            "format": "markdown",
            "error": None,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_more": end_offset < total_length
            },
            "content": paginated_content
        }
    except Exception as e:
        return {
            "url": url,
            "status_code": 500,
            "description": "",
            "format": "markdown",
            "error": str(e),
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "has_more": False
            },
            "content": ""
        }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
