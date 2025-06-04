import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from pathlib import Path

from core.config import settings

logger = logging.getLogger(__name__)

class WebSearchEngine:
    """Advanced web search and content extraction engine. (Features: 155, 156, 157, 158, 159, 160, 161, 162, 163, 164)"""
    
    def __init__(self):
        self.session = None
        self.search_apis = {
            "google": self._google_search,
            "bing": self._bing_search,
            "duckduckgo": self._duckduckgo_search,
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_web(
        self, 
        query: str, 
        engine: str = "duckduckgo",
        max_results: int = 10,
        include_content: bool = True
    ) -> Dict[str, Any]:
        """Perform web search and return results. (Features: 155, 161, 162, 163)"""
        try:
            if engine not in self.search_apis:
                raise ValueError(f"Unsupported search engine: {engine}")
            
            search_func = self.search_apis[engine]
            results = await search_func(query, max_results)
            
            # Enhance results with content if requested
            if include_content and results.get('results'):
                enhanced_results = []
                for result in results['results'][:max_results]:
                    try:
                        content_data = await self.extract_content(result['url'])
                        result.update(content_data)
                        enhanced_results.append(result)
                    except Exception as e:
                        logger.warning(f"Failed to extract content from {result['url']}: {e}")
                        enhanced_results.append(result)
                
                results['results'] = enhanced_results
            
            return {
                'query': query,
                'engine': engine,
                'timestamp': datetime.utcnow().isoformat(),
                'total_results': len(results.get('results', [])),
                'results': results.get('results', []),
                'search_time': results.get('search_time', 0)
            }
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {
                'query': query,
                'engine': engine,
                'error': str(e),
                'results': []
            }
    
    async def extract_content(self, url: str) -> Dict[str, Any]:
        """Extract content from a web page. (Features: 156, 157, 160)"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract metadata
                title = soup.find('title')
                title_text = title.get_text().strip() if title else ""
                
                meta_description = soup.find('meta', attrs={'name': 'description'})
                description = meta_description.get('content', '') if meta_description else ""
                
                # Extract main content
                content = self._extract_main_content(soup)
                
                # Extract links
                links = self._extract_links(soup, url)
                
                # Extract images
                images = self._extract_images(soup, url)
                
                # Extract structured data
                structured_data = self._extract_structured_data(soup)
                
                return {
                    'title': title_text,
                    'description': description,
                    'content': content,
                    'word_count': len(content.split()),
                    'links': links,
                    'images': images,
                    'structured_data': structured_data,
                    'extracted_at': datetime.utcnow().isoformat(),
                    'content_type': response.headers.get('content-type', ''),
                    'status_code': response.status
                }
                
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            return {
                'title': '',
                'description': '',
                'content': '',
                'error': str(e),
                'extracted_at': datetime.utcnow().isoformat()
            }
    
    async def analyze_website(self, url: str) -> Dict[str, Any]:
        """Perform comprehensive website analysis. (Features: 156, 157, 158, 161)"""
        try:
            # Extract main content
            content_data = await self.extract_content(url)
            
            # Analyze site structure
            site_analysis = await self._analyze_site_structure(url)
            
            # Check for research papers
            is_research = self._is_research_paper(content_data.get('content', ''))
            
            # Extract factual claims
            facts = self._extract_factual_claims(content_data.get('content', ''))
            
            # Classify content type
            content_type = self._classify_content(content_data)
            
            return {
                'url': url,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'content_data': content_data,
                'site_structure': site_analysis,
                'is_research_paper': is_research,
                'factual_claims': facts,
                'content_classification': content_type,
                'credibility_score': self._calculate_credibility_score(content_data, site_analysis)
            }
            
        except Exception as e:
            logger.error(f"Website analysis failed for {url}: {e}")
            return {'url': url, 'error': str(e)}
    
    async def scrape_structured_data(
        self, 
        url: str, 
        selectors: Dict[str, str]
    ) -> Dict[str, Any]:
        """Scrape structured data using CSS selectors. (Features: 158, 160)"""
        try:
            async with self.session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                extracted_data = {}
                for field, selector in selectors.items():
                    elements = soup.select(selector)
                    if elements:
                        if len(elements) == 1:
                            extracted_data[field] = elements[0].get_text().strip()
                        else:
                            extracted_data[field] = [el.get_text().strip() for el in elements]
                    else:
                        extracted_data[field] = None
                
                return {
                    'url': url,
                    'data': extracted_data,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Structured data scraping failed for {url}: {e}")
            return {'url': url, 'error': str(e)}
    
    async def retrieve_research_papers(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve research papers from academic sources. (Features: 159, 161)"""
        try:
            papers = []
            
            # Search arXiv
            arxiv_results = await self._search_arxiv(query, max_results // 2)
            papers.extend(arxiv_results)
            
            # Search other academic sources through general search
            academic_query = f"{query} site:arxiv.org OR site:scholar.google.com OR site:researchgate.net"
            web_results = await self.search_web(academic_query, max_results=max_results - len(papers))
            
            # Filter for academic sources
            for result in web_results.get('results', []):
                if self._is_academic_source(result.get('url', '')):
                    papers.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'abstract': result.get('description', ''),
                        'source': 'web_search',
                        'retrieved_at': datetime.utcnow().isoformat()
                    })
            
            return papers[:max_results]
            
        except Exception as e:
            logger.error(f"Research paper retrieval failed: {e}")
            return []
    
    async def autonomous_browse(
        self, 
        starting_url: str, 
        objective: str,
        max_depth: int = 3,
        max_pages: int = 10
    ) -> Dict[str, Any]:
        """Perform autonomous browsing to achieve an objective. (Features: 162, 164)"""
        try:
            visited_urls = set()
            to_visit = [(starting_url, 0)]  # (url, depth)
            results = []
            
            while to_visit and len(visited_urls) < max_pages:
                url, depth = to_visit.pop(0)
                
                if url in visited_urls or depth > max_depth:
                    continue
                
                visited_urls.add(url)
                
                # Analyze page
                page_analysis = await self.analyze_website(url)
                results.append(page_analysis)
                
                # Determine if objective is met
                objective_score = self._evaluate_objective_fulfillment(page_analysis, objective)
                
                if objective_score > 0.8:  # High confidence objective is met
                    break
                
                # Find relevant links to follow
                if depth < max_depth:
                    relevant_links = self._find_relevant_links(page_analysis, objective)
                    for link in relevant_links[:3]:  # Limit to top 3 relevant links
                        to_visit.append((link, depth + 1))
            
            return {
                'objective': objective,
                'starting_url': starting_url,
                'pages_visited': len(visited_urls),
                'max_depth_reached': max(result.get('depth', 0) for result in results) if results else 0,
                'results': results,
                'objective_achieved': any(
                    self._evaluate_objective_fulfillment(r, objective) > 0.8 
                    for r in results
                ),
                'browsed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Autonomous browsing failed: {e}")
            return {'objective': objective, 'error': str(e)}
    
    # Private methods
    async def _duckduckgo_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search using DuckDuckGo. (Features: 155)"""
        try:
            search_url = "https://html.duckduckgo.com/html/"
            params = {'q': query}
            
            async with self.session.get(search_url, params=params) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                results = []
                result_divs = soup.find_all('div', {'class': 'result'})
                
                for div in result_divs[:max_results]:
                    title_element = div.find('a', {'class': 'result__a'})
                    snippet_element = div.find('a', {'class': 'result__snippet'})
                    
                    if title_element:
                        title = title_element.get_text().strip()
                        url = title_element.get('href', '')
                        snippet = snippet_element.get_text().strip() if snippet_element else ""
                        
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'source': 'duckduckgo'
                        })
                
                return {'results': results, 'search_time': 0}
                
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return {'results': [], 'error': str(e)}
    
    async def _google_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search using Google (requires API key). (Features: 155)"""
        # This would require Google Custom Search API
        # For now, return empty results
        return {'results': [], 'note': 'Google search requires API key configuration'}
    
    async def _bing_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search using Bing (requires API key). (Features: 155)"""
        # This would require Bing Search API
        # For now, return empty results
        return {'results': [], 'note': 'Bing search requires API key configuration'}
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML. (Features: 157)"""
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '.content', '#content', 
            '.main-content', '.post-content', '.entry-content'
        ]
        
        for selector in main_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                return main_element.get_text(separator=' ', strip=True)
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract links from HTML. (Features: 157)"""
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(base_url, href)
            text = a_tag.get_text().strip()
            
            if text and absolute_url.startswith(('http://', 'https://')):
                links.append({
                    'url': absolute_url,
                    'text': text,
                    'title': a_tag.get('title', '')
                })
        
        return links[:50]  # Limit to first 50 links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract images from HTML. (Features: 157)"""
        images = []
        for img_tag in soup.find_all('img', src=True):
            src = img_tag['src']
            absolute_url = urljoin(base_url, src)
            
            images.append({
                'url': absolute_url,
                'alt': img_tag.get('alt', ''),
                'title': img_tag.get('title', '')
            })
        
        return images[:20]  # Limit to first 20 images
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract structured data (JSON-LD, microdata). (Features: 158)"""
        structured_data = []
        
        # Extract JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured_data.append({
                    'type': 'json-ld',
                    'data': data
                })
            except json.JSONDecodeError:
                continue
        
        return structured_data
    
    async def _analyze_site_structure(self, url: str) -> Dict[str, Any]:
        """Analyze website structure. (Features: 156, 161)"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Basic structure analysis
            structure = {
                'domain': domain,
                'protocol': parsed_url.scheme,
                'is_secure': parsed_url.scheme == 'https',
                'path_depth': len([p for p in parsed_url.path.split('/') if p]),
                'has_subdomain': len(domain.split('.')) > 2
            }
            
            return structure
            
        except Exception as e:
            logger.error(f"Site structure analysis failed: {e}")
            return {}
    
    def _is_research_paper(self, content: str) -> bool:
        """Determine if content is a research paper. (Features: 159)"""
        research_indicators = [
            'abstract', 'introduction', 'methodology', 'results', 
            'conclusion', 'references', 'doi:', 'arxiv:', 'citation'
        ]
        
        content_lower = content.lower()
        matches = sum(1 for indicator in research_indicators if indicator in content_lower)
        
        return matches >= 3
    
    def _extract_factual_claims(self, content: str) -> List[str]:
        """Extract factual claims from content. (Features: 163)"""
        # Simple pattern matching for factual statements
        fact_patterns = [
            r'[A-Z][^.!?]*(?:is|are|was|were|has|have|will|shows|demonstrates|proves)[^.!?]*\.',
            r'According to[^.!?]*\.',
            r'Research shows[^.!?]*\.',
            r'Studies indicate[^.!?]*\.'
        ]
        
        facts = []
        for pattern in fact_patterns:
            matches = re.findall(pattern, content)
            facts.extend(matches)
        
        return facts[:10]  # Limit to first 10 facts
    
    def _classify_content(self, content_data: Dict[str, Any]) -> str:
        """Classify content type. (Features: 161)"""
        content = content_data.get('content', '').lower()
        title = content_data.get('title', '').lower()
        
        if any(word in content for word in ['research', 'study', 'journal', 'paper']):
            return 'academic'
        elif any(word in content for word in ['news', 'breaking', 'report', 'today']):
            return 'news'
        elif any(word in content for word in ['tutorial', 'how to', 'guide', 'step']):
            return 'educational'
        elif any(word in content for word in ['product', 'buy', 'price', 'sale']):
            return 'commercial'
        else:
            return 'general'
    
    def _calculate_credibility_score(self, content_data: Dict[str, Any], site_analysis: Dict[str, Any]) -> float:
        """Calculate content credibility score. (Features: 161)"""
        score = 0.5  # Base score
        
        # Secure site bonus
        if site_analysis.get('is_secure'):
            score += 0.1
        
        # Content quality indicators
        word_count = content_data.get('word_count', 0)
        if word_count > 500:
            score += 0.1
        if word_count > 1000:
            score += 0.1
        
        # Academic source bonus
        domain = site_analysis.get('domain', '')
        if any(edu in domain for edu in ['.edu', '.ac.', 'scholar', 'arxiv']):
            score += 0.2
        
        return min(1.0, score)
    
    def _is_academic_source(self, url: str) -> bool:
        """Check if URL is from an academic source. (Features: 159)"""
        academic_domains = [
            'arxiv.org', 'scholar.google.com', 'researchgate.net',
            'ieee.org', 'acm.org', 'springer.com', 'nature.com',
            '.edu', '.ac.'
        ]
        
        return any(domain in url for domain in academic_domains)
    
    async def _search_arxiv(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search arXiv for research papers. (Features: 159)"""
        try:
            arxiv_url = "http://export.arxiv.org/api/query"
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results
            }
            
            async with self.session.get(arxiv_url, params=params) as response:
                xml_content = await response.text()
                # Basic XML parsing (would need more sophisticated parsing)
                papers = []
                # This is a simplified implementation
                return papers
                
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []
    
    def _evaluate_objective_fulfillment(self, page_analysis: Dict[str, Any], objective: str) -> float:
        """Evaluate how well a page fulfills the browsing objective. (Features: 162, 164)"""
        content = page_analysis.get('content_data', {}).get('content', '').lower()
        objective_lower = objective.lower()
        
        # Simple keyword matching
        objective_words = objective_lower.split()
        matches = sum(1 for word in objective_words if word in content)
        
        return matches / len(objective_words) if objective_words else 0
    
    def _find_relevant_links(self, page_analysis: Dict[str, Any], objective: str) -> List[str]:
        """Find links relevant to the browsing objective. (Features: 162, 164)"""
        links = page_analysis.get('content_data', {}).get('links', [])
        objective_lower = objective.lower()
        
        relevant_links = []
        for link in links:
            link_text = link.get('text', '').lower()
            if any(word in link_text for word in objective_lower.split()):
                relevant_links.append(link.get('url'))
        
        return relevant_links

# Singleton instance
_web_search_engine = None

async def get_web_search_engine() -> WebSearchEngine:
    """Get or create the WebSearchEngine instance."""
    global _web_search_engine
    if _web_search_engine is None:
        _web_search_engine = WebSearchEngine()
    return _web_search_engine 