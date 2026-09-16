"""
Web Search Tool.
Searches the web for current information.
"""
import json
from typing import Optional
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
 

from app.core.config import settings

@tool
def search_web(query: str, max_results: int = 5) -> str:
    """
    Use this tool when current, recent, or external web information is required.
    
    Args:
        query: The search query.
        max_results: Number of web results to retrieve.
    """
    if settings.TAVILY_API_KEY:
        try:
            search_tool = TavilySearchResults(
                max_results=max_results,
                tavily_api_key=settings.TAVILY_API_KEY
            )
            # Tavily returns a list of dicts with 'url' and 'content'
            results = search_tool.invoke({"query": query})
            
            if not results:
                return json.dumps({"content": "No web results found.", "sources": []})
                
            formatted_content = []
            structured_sources = []
            
            for r in results:
                url = r.get('url', '')
                title = url  # Tavily often doesn't give a distinct title in the basic response, but we'll use URL
                content = r.get('content', '')
                
                formatted_content.append(f"Title/URL: {url}\nContent: {content}")
                structured_sources.append({
                    "type": "web",
                    "title": title,
                    "url": url,
                    "snippet": content[:200] + "..."
                })
                
            return json.dumps({
                "content": "\n\n---\n\n".join(formatted_content),
                "sources": structured_sources
            })
        except Exception as e:
            return json.dumps({"content": f"Web search provider error (Tavily): {str(e)}", "sources": []})
    
    # Fallback to duckduckgo-search if tavily is not available, but since we only have tavily-python
    # installed by default (and it's standard), we can either use DDGS or just return an error.
    # The instructions said: "If no Tavily key exists and fallback search cannot be used: return a clear structured configuration result."
    return json.dumps({
        "content": "Error: Web search is unavailable because TAVILY_API_KEY is not configured.",
        "sources": []
    })
