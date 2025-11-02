import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP

from duckduckgo_search import DuckDuckGoSearcher
from goggles import GogglesApi
from web_wrapper import WebWrapper

# Get Goggles URL from environment variable, with fallback to default
GOGGLES_URL = os.getenv("GOGGLES_URL", "http://localhost:8001")

# Initialize the services
goggles = GogglesApi(GOGGLES_URL)
web_wrapper = WebWrapper(goggles)
searcher = DuckDuckGoSearcher()

# Create a FastAPI app
app = FastAPI(
    title="Web Search MCP Server",
    description="MCP server for web search and URL content retrieval",
    version="1.0.0"
)

# Add CORS middleware to handle preflight OPTIONS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MCP server usage
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
)


@app.get("/search", summary="Search the web", description="Perform a web search with the given search string")
async def search_web(
    query: str = Query(..., description="The search query string")
) -> dict:
    """
    Perform a web search using DuckDuckGo.
    
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


@app.get("/content", summary="Get URL content", description="Retrieve the content from a given URL with pagination support")
async def get_url_content(
    url: str = Query(..., description="The URL to fetch content from"),
    offset: int = Query(0, ge=0, description="Character offset to start from (for pagination)"),
    limit: int = Query(10000, ge=1, le=50000, description="Maximum number of characters to return (1-50000)")
) -> dict:
    """
    Get the content of a URL with pagination support.
    
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


# Create an MCP server based on this app
mcp = FastApiMCP(
    app,
    name="Web Search MCP Server",
    description="MCP server for web search and URL content retrieval",
)

# Mount the MCP server to the app
mcp.mount()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
