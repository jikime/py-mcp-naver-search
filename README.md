# Naver Search MCP Server

[![smithery badge](https://smithery.ai/badge/@jikime/py-mcp-naver-search)](https://smithery.ai/server/@jikime/py-mcp-naver-search) ![](https://badge.mcpx.dev?type=server 'MCP Server') ![Version](https://img.shields.io/badge/version-1.1.10-green) ![License](https://img.shields.io/badge/license-MIT-blue)

This MCP (Multi-platform Communication Protocol) server provides access to Naver Search APIs, allowing AI agents to search for various types of content on Naver.

## Overview

- Search for blogs, news, books, images, shopping items, and more
- Multiple search categories with pagination support
- Structured text responses optimized for LLM consumption
- Check for adult content
- Convert keyboard input errors (errata)

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configure MCP Settings](#configure-mcp-settings)
- [API Reference](#api-reference)
- [Acknowledgements](#acknowledgements)
- [License](#license)

## Setup

### Prerequisites

- Python 3.12+
- Naver Developer API credentials
  - You can obtain these credentials by signing up at the [Naver Developers](https://developers.naver.com/apps/#/register) portal.
  - And You can check my blog [Naver Search API MCP Server](https://devway.tistory.com/55), too.

### Installation

1. Clone the repository:
```bash
git clone https://github.com/jikime/py-mcp-naver-search.git
cd py-mcp-naver-search
```

2. uv installation
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Create a virtual environment and install dependencies:
```bash
uv venv -p 3.12
source .venv/bin/activate
pip install -r requirements.txt
```

4. Create a `.env` file with your Naver API credentials:
```
cp env.example .env
vi .env

NAVER_CLIENT_ID=your_client_id_here
NAVER_CLIENT_SECRET=your_client_secret_here
```


#### Using Docker

1. Build the Docker image:
```bash
docker build -t py-mcp-naver-search .
```

2. Run the container:
```bash
docker run py-mcp-naver-search
```

#### Using Local

1. Run the server:
```bash
mcp run server.py
```
2. Run the MCP Inspector
```bash
mcp dev server.py
```

## Configure MCP Settings
Add the server configuration to your MCP settings file:

#### Claude desktop app 
1. To install automatically via [Smithery](https://smithery.ai/server/@jikime/py-mcp-naver-search):

```bash
npx -y @smithery/cli install @jikime/py-mcp-naver-search --client claude
```

2. To install manually
open `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this to the `mcpServers` object:
```json
{
  "mcpServers": {
    "Google Toolbox": {
      "command": "/path/to/bin/uv",
      "args": [
        "--directory",
        "/path/to/py-mcp-naver-search",
        "run",
        "server.py"
      ]
    }
  }
}
```

#### Cursor IDE 
open `~/.cursor/mcp.json`

Add this to the `mcpServers` object:
```json
{
  "mcpServers": {
    "Google Toolbox": {
      "command": "/path/to/bin/uv",
      "args": [
        "--directory",
        "/path/to/py-mcp-naver-search",
        "run",
        "server.py"
      ]
    }
  }
}
```

#### for Docker
```json
{
  "mcpServers": {
    "Google Toolbox": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "py-mcp-naver-search"
      ]
    }
  }
}
```

### Using the Client

The repository includes a client script for testing:

```bash
# Basic search
uv run client.py blog "Python programming" display=5 page=1

# News search with sorting
uv run client.py news "AI" display=10 page=1 sort=date

# Image search with filtering
uv run client.py image "cat" display=10 filter=large

# Check for adult content
uv run client.py adult "your query"

# Errata correction
uv run client.py errata "spdlqj"
```

## Available Search Categories

The server supports the following search categories:

1. `blog` - Blog posts
2. `news` - News articles
3. `book` - Books
4. `adult` - Adult content check
5. `encyc` - Encyclopedia entries
6. `cafe_article` - Cafe articles
7. `kin` - Knowledge iN Q&A
8. `local` - Local business information
9. `errata` - Keyboard input error correction
10. `shop` - Shopping items
11. `doc` - Academic papers and documents
12. `image` - Images
13. `webkr` - Web documents

## API Reference

### Tools

#### Search Blog
```
search_blog(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str
```
Searches for blogs on Naver using the given keyword.

#### Search News
```
search_news(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str
```
Searches for news on Naver using the given keyword.

#### Search Book
```
search_book(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str
```
Searches for book information on Naver using the given keyword.

#### Check Adult Query
```
check_adult_query(query: str) -> str
```
Determines if the input query is an adult search term.

#### Search Encyclopedia
```
search_encyclopedia(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str
```
Searches for encyclopedia information on Naver using the given keyword.

#### Search Cafe Article
```
search_cafe_article(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str
```
Searches for cafe articles on Naver using the given keyword.

#### Search KnowledgeiN
```
search_kin(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str
```
Searches for Knowledge iN Q&A on Naver using the given keyword.

#### Search Local
```
search_local(query: str, display: int = 5, page: int = 1, sort: str = "random") -> str
```
Searches for local business information using the given keyword.

#### Correct Errata
```
correct_errata(query: str) -> str
```
Converts Korean/English keyboard input errors.

#### Search Shop
```
search_shop(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str
```
Searches for shopping product information on Naver using the given keyword.

#### Search Document
```
search_doc(query: str, display: int = 10, page: int = 1) -> str
```
Searches for academic papers, reports, etc. using the given keyword.

#### Search Image
```
search_image(query: str, display: int = 10, page: int = 1, sort: str = "sim", filter: str = "all") -> str
```
Searches for images using the given keyword.

#### Search Web Document
```
search_webkr(query: str, display: int = 10, page: int = 1) -> str
```
Searches for web documents using the given keyword.

### Resources

#### Available Search Categories
```
GET naver://available-search-categories
```
Returns a list of Naver search categories available on this MCP server.

## Response Format

All tools return responses in structured text format, optimized for LLM processing:

```
Naver Blog search results (total 12,345 of 1~10):

### Result 1
Title(title): Sample Blog Post
Link(link): https://blog.example.com/post1
Description(description): This is a sample blog post about...
Blogger name(bloggername): John Doe
Blogger link(bloggerlink): https://blog.example.com
Post date(postdate): 20250429

### Result 2
...
```

## Acknowledgements
- [Naver Search API MCP Server Blog](https://devway.tistory.com/55)
- [Naver Open API](https://developers.naver.com/docs/search/blog/)
- [MCP Protocol](https://github.com/mcp-foundation/mcp-spec)

## License

This project is licensed under the MIT License - see the LICENSE file for details.


