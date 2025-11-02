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


@app.get("/content", summary="Get URL content", description="Retrieve the content from a given URL")
async def get_url_content(
    url: str = Query(..., description="The URL to fetch content from")
) -> dict:
    """
    Get the content of a URL.
    
    Args:
        url: The URL to fetch content from
        
    Returns:
        Dictionary containing the URL, content, description
    """
    try:
        code, content, description = web_wrapper.get_markdown_for_url(url)
        return {
            "url": url,
            "status_code": code,
            "content": content,
            "description": description,
            "format": "markdown"
        }
    except Exception as e:
        return {
            "url": url,
            "status_code": 500,
            "content": "",
            "error": str(e)
        }


# Create an MCP server based on this app
mcp = FastApiMCP(app)

# Mount the MCP server to the app
mcp.mount_http()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
