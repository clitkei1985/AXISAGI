import asyncio
import logging
from typing import List, Dict, Optional, Union
from datetime import datetime
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from core.database import User
from modules.memory.memory_manager import get_memory_manager
from modules.llm_engine.llama_integration import get_llama_manager

logger = logging.getLogger(__name__)

class IntelligentWebSearch:
    """Intelligent web search system with memory integration and AI-powered analysis."""
    
    def __init__(self, db: Session):
        self.db = db
        self.memory_manager = get_memory_manager(db)
        self.llama_manager = get_llama_manager()
        
        # Search engines configuration
        self.search_engines = {
            "duckduckgo": {
                "url": "https://api.duckduckgo.com/",
                "headers": {"User-Agent": "AXIS-AI/1.0 Research Assistant"}
            },
            "searx": {
                "url": "https://searx.be/search",
                "headers": {"User-Agent": "AXIS-AI/1.0 Research Assistant"}
            }
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AXIS-AI/1.0 Research Assistant",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
    
    async def perform_intelligent_search(
        self,
        query: str,
        user: User,
        max_results: int = 10,
        include_memory: bool = True,
        deep_analysis: bool = True
    ) -> Dict:
        """Perform intelligent web search with memory integration and AI analysis."""
        try:
            # Step 1: Search internal memory first
            memory_results = []
            if include_memory:
                memory_results = await self._search_memory(query, user)
            
            # Step 2: Perform web search
            web_results = await self._search_web(query, max_results)
            
            # Step 3: Analyze and synthesize results using AI
            if deep_analysis and (memory_results or web_results):
                synthesis = await self._synthesize_results(
                    query, memory_results, web_results, user
                )
            else:
                synthesis = None
            
            # Step 4: Save search results to memory for future reference
            await self._save_search_to_memory(query, web_results, synthesis, user)
            
            return {
                "query": query,
                "memory_results": memory_results,
                "web_results": web_results,
                "synthesis": synthesis,
                "total_sources": len(memory_results) + len(web_results),
                "timestamp": datetime.utcnow(),
                "search_type": "intelligent_search"
            }
            
        except Exception as e:
            logger.error(f"Error in intelligent search: {e}")
            return {
                "query": query,
                "error": str(e),
                "memory_results": [],
                "web_results": [],
                "synthesis": None,
                "timestamp": datetime.utcnow()
            }
    
    async def _search_memory(self, query: str, user: User) -> List[Dict]:
        """Search internal memory for relevant information."""
        try:
            memories = self.memory_manager.search_memories(
                query=query,
                user=user,
                k=5,
                min_similarity=0.6
            )
            
            return [{
                "title": f"Memory: {memory.content[:60]}...",
                "content": memory.content,
                "url": None,
                "source": "memory",
                "timestamp": memory.timestamp,
                "relevance": float(similarity),
                "tags": memory.tags
            } for memory, similarity in memories]
            
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []
    
    async def _search_web(self, query: str, max_results: int) -> List[Dict]:
        """Perform web search using available search engines."""
        all_results = []
        
        # Try DuckDuckGo first
        try:
            ddg_results = await self._search_duckduckgo(query, max_results // 2)
            all_results.extend(ddg_results)
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
        
        # Try alternative search methods
        try:
            alt_results = await self._search_alternative(query, max_results // 2)
            all_results.extend(alt_results)
        except Exception as e:
            logger.warning(f"Alternative search failed: {e}")
        
        # Remove duplicates and limit results
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.get("url") and result["url"] not in seen_urls:
                seen_urls.add(result["url"])
                unique_results.append(result)
                if len(unique_results) >= max_results:
                    break
        
        return unique_results
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict]:
        """Search using DuckDuckGo API."""
        try:
            # DuckDuckGo instant answer API
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            response = self.session.get(
                self.search_engines["duckduckgo"]["url"],
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Process instant answer
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", "DuckDuckGo Answer"),
                    "content": data.get("Abstract"),
                    "url": data.get("AbstractURL"),
                    "source": "duckduckgo",
                    "type": "instant_answer"
                })
            
            # Process related topics
            for topic in data.get("RelatedTopics", [])[:max_results-1]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:60] + "...",
                        "content": topic.get("Text", ""),
                        "url": topic.get("FirstURL"),
                        "source": "duckduckgo",
                        "type": "related_topic"
                    })
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    async def _search_alternative(self, query: str, max_results: int) -> List[Dict]:
        """Alternative search method using web scraping."""
        try:
            # Simple web scraping approach (for demonstration)
            # In production, you'd want to use proper APIs
            
            search_url = f"https://www.startpage.com/sp/search?query={query.replace(' ', '+')}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # This is a simplified example - you'd need to adapt to actual HTML structure
            search_results = soup.find_all('div', class_='w-gl__result')[:max_results]
            
            for result in search_results:
                title_elem = result.find('h3')
                link_elem = result.find('a')
                snippet_elem = result.find('p')
                
                if title_elem and link_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "content": snippet_elem.get_text(strip=True) if snippet_elem else "",
                        "url": link_elem.get('href'),
                        "source": "web_search",
                        "type": "search_result"
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Alternative search error: {e}")
            return []
    
    async def _synthesize_results(
        self,
        query: str,
        memory_results: List[Dict],
        web_results: List[Dict],
        user: User
    ) -> Optional[str]:
        """Use AI to synthesize and analyze search results."""
        try:
            # Prepare context from all results
            context_parts = []
            
            if memory_results:
                context_parts.append("**From Memory:**")
                for i, result in enumerate(memory_results[:3]):
                    context_parts.append(f"{i+1}. {result['content'][:300]}...")
            
            if web_results:
                context_parts.append("\n**From Web Search:**")
                for i, result in enumerate(web_results[:5]):
                    content = result.get('content', result.get('title', ''))
                    context_parts.append(f"{i+1}. {content[:300]}...")
            
            context = "\n".join(context_parts)
            
            # Use LLaMA for synthesis if available
            if self.llama_manager.is_loaded:
                synthesis_prompt = f"""Based on the search results below, provide a comprehensive and intelligent analysis for the query: "{query}"

{context}

Please:
1. Synthesize the key information
2. Identify the most important points
3. Provide insights and connections
4. Note any contradictions or gaps
5. Give a well-reasoned conclusion

Analysis:"""

                synthesis = await self.llama_manager.generate_intelligent_response(
                    prompt=synthesis_prompt,
                    max_tokens=1500,
                    temperature=0.4
                )
                
                return synthesis
            else:
                # Simple text-based synthesis fallback
                return self._simple_synthesis(query, memory_results, web_results)
                
        except Exception as e:
            logger.error(f"Error synthesizing results: {e}")
            return None
    
    def _simple_synthesis(
        self,
        query: str,
        memory_results: List[Dict],
        web_results: List[Dict]
    ) -> str:
        """Simple text-based synthesis when AI is not available."""
        synthesis_parts = [f"Search Analysis for: {query}\n"]
        
        if memory_results:
            synthesis_parts.append(f"Found {len(memory_results)} relevant items in memory.")
        
        if web_results:
            synthesis_parts.append(f"Found {len(web_results)} web results.")
            
            # Extract key themes
            all_text = " ".join([
                result.get('content', result.get('title', ''))
                for result in web_results
            ]).lower()
            
            # Simple keyword extraction
            words = re.findall(r'\b\w+\b', all_text)
            word_freq = {}
            for word in words:
                if len(word) > 4:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if top_keywords:
                synthesis_parts.append(f"\nKey themes: {', '.join([word for word, _ in top_keywords[:5]])}")
        
        return "\n".join(synthesis_parts)
    
    async def _save_search_to_memory(
        self,
        query: str,
        web_results: List[Dict],
        synthesis: Optional[str],
        user: User
    ):
        """Save search results to memory for future reference."""
        try:
            # Save search query and synthesis
            if synthesis:
                self.memory_manager.add_memory(
                    user=user,
                    content=f"Search for '{query}': {synthesis}",
                    metadata={
                        "type": "search_synthesis",
                        "query": query,
                        "result_count": len(web_results)
                    },
                    source="web_search",
                    tags=["search", "synthesis", "research"],
                    privacy_level="private"
                )
            
            # Save top web results
            for i, result in enumerate(web_results[:3]):
                self.memory_manager.add_memory(
                    user=user,
                    content=f"Web result for '{query}': {result.get('title', '')} - {result.get('content', '')}",
                    metadata={
                        "type": "search_result",
                        "query": query,
                        "url": result.get('url'),
                        "source_type": result.get('source')
                    },
                    source="web_search",
                    tags=["search", "web_result"],
                    privacy_level="private"
                )
                
        except Exception as e:
            logger.error(f"Error saving search to memory: {e}")
    
    async def research_topic(
        self,
        topic: str,
        user: User,
        depth: str = "normal"
    ) -> Dict:
        """Perform comprehensive research on a topic using multiple approaches."""
        try:
            # Determine search strategy based on depth
            if depth == "quick":
                max_results = 5
                deep_analysis = False
            elif depth == "deep":
                max_results = 20
                deep_analysis = True
            else:  # normal
                max_results = 10
                deep_analysis = True
            
            # Perform initial search
            initial_results = await self.perform_intelligent_search(
                query=topic,
                user=user,
                max_results=max_results,
                deep_analysis=deep_analysis
            )
            
            # For deep research, perform follow-up searches on key themes
            if depth == "deep" and initial_results.get("synthesis"):
                # Extract key themes for follow-up searches
                follow_up_queries = self._extract_follow_up_queries(topic, initial_results["synthesis"])
                
                follow_up_results = []
                for query in follow_up_queries[:3]:
                    result = await self.perform_intelligent_search(
                        query=query,
                        user=user,
                        max_results=5,
                        deep_analysis=False
                    )
                    follow_up_results.append(result)
                
                initial_results["follow_up_research"] = follow_up_results
            
            return initial_results
            
        except Exception as e:
            logger.error(f"Error in topic research: {e}")
            return {"error": str(e), "topic": topic}
    
    def _extract_follow_up_queries(self, original_topic: str, synthesis: str) -> List[str]:
        """Extract follow-up queries from synthesis for deeper research."""
        # Simple approach - in practice, you'd use NLP
        queries = []
        
        # Look for question words and related topics
        words = synthesis.lower().split()
        
        # Find potential follow-up topics
        key_phrases = []
        for i, word in enumerate(words):
            if word in ["what", "how", "why", "when", "where"] and i < len(words) - 3:
                phrase = " ".join(words[i:i+4])
                key_phrases.append(phrase)
        
        # Create follow-up queries
        for phrase in key_phrases[:2]:
            queries.append(f"{original_topic} {phrase}")
        
        # Add related terms
        if "application" in synthesis.lower():
            queries.append(f"{original_topic} applications")
        if "benefit" in synthesis.lower():
            queries.append(f"{original_topic} benefits")
        if "challenge" in synthesis.lower():
            queries.append(f"{original_topic} challenges")
        
        return queries[:3]

# Global instance
_intelligent_search = None

def get_intelligent_search(db: Session) -> IntelligentWebSearch:
    """Get the global intelligent search instance."""
    global _intelligent_search
    if _intelligent_search is None or _intelligent_search.db != db:
        _intelligent_search = IntelligentWebSearch(db)
    return _intelligent_search 