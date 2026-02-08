"""
Web Tool Handlers

Tools for searching the web and fetching web content.
"""

import asyncio
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from urllib.parse import urljoin, urlparse


class BaseWebHandler(ABC):
    """Base class for web handlers."""
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the web operation."""
        pass
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format and scheme."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ('http', 'https') and parsed.netloc
        except Exception:
            return False
    
    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL for safety."""
        url = url.strip()
        if not url.startswith('http'):
            url = 'https://' + url
        return url


class MLStripper(HTMLParser):
    """HTML tag stripper for web content."""
    
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    
    def handle_data(self, d):
        self.fed.append(d)
    
    def handle_charref(self, nr):
        self.fed.append(chr(int(nr[1:], 16)) if nr.startswith('&#x') else chr(int(nr[1:])))
    
    def handle_entityref(self, nr):
        self.fed.append(chr(name2codepoint[nr]) if nr in name2codepoint else '&' + nr)
    
    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html: str) -> str:
    """Remove HTML tags from string."""
    stripper = MLStripper()
    stripper.feed(html)
    return stripper.get_data()


# Blocked domains for security
BLOCKED_DOMAINS = {
    'localhost', '127.0.0.1', '0.0.0.0', '::1',
    'file://', 'ftp://', 'data:',
}


class WebFetchTool(BaseWebHandler):
    """
    Fetch web page content with HTML parsing.
    
    Parameters:
        url: URL to fetch (required)
        timeout: Timeout in seconds (default: 10)
        max_length: Maximum content length (default: 10000)
    
    Returns:
        Extracted text content from the page
    """
    
    def __init__(self):
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None:
            import aiohttp
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; RefactorBot/1.0)'
                }
            )
        return self.session
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Fetch web page content."""
        try:
            url = arguments.get("url")
            if not url:
                raise ValueError("Missing required parameter: url")
            
            url = self._sanitize_url(url)
            
            if not self._validate_url(url):
                raise ValueError(f"Invalid URL: {url}")
            
            # Check blocked domains
            parsed = urlparse(url)
            if parsed.netloc in BLOCKED_DOMAINS:
                raise SecurityError(f"Access to {parsed.netloc} is blocked")
            
            # Get parameters
            timeout = float(arguments.get("timeout", 10))
            max_length = int(arguments.get("max_length", 10000))
            
            # Fetch page
            session = await self._get_session()
            
            async with session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                
                content_type = response.headers.get('Content-Type', '')
                
                if 'text/html' in content_type:
                    html = await response.text()
                    text = strip_tags(html)
                else:
                    text = await response.text()
                
                # Truncate if needed
                if len(text) > max_length:
                    text = text[:max_length] + f"\n\n[Truncated to {max_length} characters]"
                
                return text
                
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request timed out after {timeout} seconds")
        except SecurityError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to fetch {url}: {e}")
    
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch"
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds",
                    "default": 10
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum content length",
                    "default": 10000
                }
            },
            "required": ["url"]
        }


class WebSearchTool(BaseWebHandler):
    """
    Search the web using Brave API or fallback.
    
    Parameters:
        query: Search query (required)
        num_results: Number of results (default: 5)
        timeout: Timeout in seconds (default: 10)
    
    Returns:
        JSON string with search results
    """
    
    def __init__(self, brave_api_key: Optional[str] = None):
        self.brave_api_key = brave_api_key
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Search the web."""
        try:
            query = arguments.get("query")
            if not query:
                raise ValueError("Missing required parameter: query")
            
            num_results = int(arguments.get("num_results", 5))
            timeout = float(arguments.get("timeout", 10))
            
            # Try Brave API first
            if self.brave_api_key:
                results = await self._brave_search(query, num_results, timeout)
            else:
                results = await self._fallback_search(query, num_results, timeout)
            
            import json
            return json.dumps(results, indent=2)
            
        except Exception as e:
            raise RuntimeError(f"Search failed: {e}")
    
    async def _brave_search(self, query: str, num_results: int, timeout: float) -> List[Dict]:
        """Search using Brave API."""
        import aiohttp
        
        url = "https://api.search.brave.com/v1/web_search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.brave_api_key
        }
        params = {
            "q": query,
            "count": min(num_results, 10),
            "search_type": "web"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=timeout) as response:
                if response.status != 200:
                    raise RuntimeError(f"Brave API error: {response.status}")
                
                data = await response.json()
                
                results = []
                for item in data.get('web', {}).get('results', []):
                    results.append({
                        "title": item.get('title', ''),
                        "url": item.get('url', ''),
                        "description": item.get('description', ''),
                        "displayed_url": item.get('displayedUrl', '')
                    })
                
                return results
    
    async def _fallback_search(self, query: str, num_results: int, timeout: float) -> List[Dict]:
        """Fallback search using DuckDuckGo HTML."""
        import aiohttp
        from urllib.parse import urlencode
        
        url = f"https://duckduckgo.com/html/?{urlencode({'q': query})}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    raise RuntimeError(f"DuckDuckGo error: {response.status}")
                
                html = await response.text()
                
                # Parse results
                results = []
                pattern = r'<a class="result__a" href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(pattern, html)
                
                for url, title in matches[:num_results]:
                    # Get description
                    desc_pattern = f'<a href="{re.escape(url)}"[^>]*</a>[^<]*<a[^>]*class="result__snippet"[^>]*>([^<]*)</a>'
                    desc_match = re.search(desc_pattern, html)
                    description = desc_match.group(1) if desc_match else ""
                    
                    results.append({
                        "title": strip_tags(title),
                        "url": url,
                        "description": strip_tags(description)
                    })
                
                return results
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results",
                    "default": 5
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds",
                    "default": 10
                }
            },
            "required": ["query"]
        }


class SecurityError(Exception):
    """Security violation exception."""
    pass


class TimeoutError(Exception):
    """Request timeout exception."""
    pass
