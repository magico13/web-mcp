# Web MCP Server

A Model Context Protocol (MCP) server for web search and URL content retrieval, built with FastAPI and fastapi-mcp.

## Features

- **Web Search**: Search the web using DuckDuckGo
- **URL Content Retrieval**: Fetch and parse content from any URL as markdown
  - HTML pages: Convert to clean markdown format
  - Files: Extract text from various file types via Goggles API (PDF, DOCX, etc.)

## Running Locally

### Prerequisites
- Python 3.13+
- Virtual environment (recommended)

### Setup
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source .venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

The server will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MCP Endpoint: http://localhost:8000/mcp

## Running with Docker

### Build and run with Docker Compose (Recommended)
```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Build and run with Docker directly
```bash
# Build the image
docker build -t web-mcp-server .

# Run the container
docker run -d -p 8000:8000 --name web-mcp-server web-mcp-server

# View logs
docker logs -f web-mcp-server

# Stop the container
docker stop web-mcp-server
docker rm web-mcp-server
```

## API Endpoints

### `/search` - Web Search
Search the web using DuckDuckGo.

**Parameters:**
- `query` (string, required): The search query

**Example:**
```bash
curl "http://localhost:8000/search?query=python+programming"
```

### `/content` - Get URL Content
Retrieve and parse content from a URL, returned as markdown with pagination support.

**Parameters:**
- `url` (string, required): The URL to fetch content from
- `offset` (integer, optional): Character offset to start from (default: 0)
- `limit` (integer, optional): Maximum characters to return (default: 10000, max: 50000)

**Examples:**
```bash
# Get first 10,000 characters (default)
curl "http://localhost:8000/content?url=https://example.com"

# Get specific range
curl "http://localhost:8000/content?url=https://example.com&offset=10000&limit=10000"

# Get more content (up to 50,000 characters)
curl "http://localhost:8000/content?url=https://example.com&limit=50000"
```

**Response includes pagination info:**
- `total`: Total content length
- `returned`: Characters returned in this response
- `has_more`: Whether more content is available

## MCP Integration

Connect this server to any MCP client (Claude Desktop, Cursor, Windsurf) using:

```json
{
  "mcpServers": {
    "web-mcp": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Configuration

### Goggles API Endpoint

The Goggles API endpoint can be configured via the `GOGGLES_URL` environment variable.

**Default:** `http://localhost:8001`

**Set via environment variable:**
```bash
# Linux/Mac
export GOGGLES_URL=http://your-goggles-instance:8001

# Windows PowerShell
$env:GOGGLES_URL="http://your-goggles-instance:8001"

# Docker
docker run -e GOGGLES_URL=http://your-goggles-instance:8001 -p 8000:8000 web-mcp-server

# Docker Compose
# Create a .env file in the project root:
echo "GOGGLES_URL=http://your-goggles-instance:8001" > .env
```

## Docker Hub Deployment

This repository includes a GitHub Actions workflow that automatically builds and pushes Docker images to Docker Hub when code is pushed to the `main` branch.

### Setup GitHub Secrets and Variables

To enable automatic Docker Hub deployment, configure the following in your GitHub repository settings:

**Secrets** (Settings → Secrets and variables → Actions → New repository secret):
- `DOCKER_PASSWORD`: Your Docker Hub password or access token

**Variables** (Settings → Secrets and variables → Actions → New repository variable):
- `DOCKER_USERNAME`: Your Docker Hub username

Once configured, every push to `main` will automatically build and push a new Docker image tagged with both `latest` and the commit SHA.

## Dependencies

- fastapi - Web framework
- fastapi-mcp - MCP integration
- uvicorn - ASGI server
- requests - HTTP client
- beautifulsoup4 - HTML parsing
- markdownify - HTML to markdown conversion
