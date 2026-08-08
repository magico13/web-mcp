import os
from fastmcp import FastMCP

from duckduckgo_search import DuckDuckGoSearcher
from goggles import GogglesApi
import nws_forecast
from web_wrapper import WebWrapper
from nws_forecast import get_nws_forecast

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
def open_url(url: str, page: int = 1, page_size: int = 25000) -> dict:
    """Open a URL and retrieve its content with pagination support.
    Use to get the most up-to-date (live) information from a specific URL (weather, news, etc.).
    
    Args:
        url: The URL to fetch content from
        page: Page number to retrieve (default: 1)
        page_size: Maximum characters to return per page (default: 25000)
        
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

@mcp.tool
def get_nws_forecast(lat: float, lon: float) -> str:
    """Get the 7-day National Weather Service forecast for a given latitude and longitude.
    Use this for weather information instead of the web search tool, as it provides a more structured and reliable forecast.
    Use the web search to find coordinates for location names if needed (e.g., "New York City coordinates").
    
    Args:
        lat: Latitude of the location
        lon: Longitude of the location
    Returns:
        National Weather Service forecast as a string
    """
    return nws_forecast.get_nws_forecast(lat, lon)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
