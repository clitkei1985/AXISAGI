from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Request schemas
class WebSearchRequest(BaseModel):
    """Web search request schema. (Features: 155, 161, 162, 163)"""
    query: str = Field(..., description="Search query")
    engine: str = Field(default="duckduckgo", description="Search engine to use")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum results to return")
    include_content: bool = Field(default=True, description="Include full content extraction")

class ContentExtractionRequest(BaseModel):
    """Content extraction request schema. (Features: 156, 157, 160)"""
    url: HttpUrl = Field(..., description="URL to extract content from")
    extract_links: bool = Field(default=True, description="Extract links from page")
    extract_images: bool = Field(default=True, description="Extract images from page")
    extract_structured_data: bool = Field(default=True, description="Extract structured data")

class StructuredDataRequest(BaseModel):
    """Structured data scraping request schema. (Features: 158, 160)"""
    url: HttpUrl = Field(..., description="URL to scrape")
    selectors: Dict[str, str] = Field(..., description="CSS selectors for data extraction")

class ResearchPaperRequest(BaseModel):
    """Research paper retrieval request schema. (Features: 159, 161)"""
    query: str = Field(..., description="Research query")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum papers to retrieve")
    include_abstracts: bool = Field(default=True, description="Include paper abstracts")

class AutonomousBrowsingRequest(BaseModel):
    """Autonomous browsing request schema. (Features: 162, 164)"""
    starting_url: HttpUrl = Field(..., description="Starting URL for browsing")
    objective: str = Field(..., description="Browsing objective or goal")
    max_depth: int = Field(default=3, ge=1, le=5, description="Maximum depth to browse")
    max_pages: int = Field(default=10, ge=1, le=20, description="Maximum pages to visit")

# Response schemas
class SearchResult(BaseModel):
    """Individual search result schema. (Features: 155)"""
    title: str
    url: str
    snippet: str
    source: str
    content: Optional[str] = None
    word_count: Optional[int] = None
    extracted_at: Optional[str] = None

class WebSearchResponse(BaseModel):
    """Web search response schema. (Features: 155, 161, 162, 163)"""
    query: str
    engine: str
    timestamp: str
    total_results: int
    results: List[SearchResult]
    search_time: float
    error: Optional[str] = None

class LinkData(BaseModel):
    """Link data schema. (Features: 157)"""
    url: str
    text: str
    title: Optional[str] = None

class ImageData(BaseModel):
    """Image data schema. (Features: 157)"""
    url: str
    alt: Optional[str] = None
    title: Optional[str] = None

class StructuredDataItem(BaseModel):
    """Structured data item schema. (Features: 158)"""
    type: str
    data: Dict[str, Any]

class ContentExtractionResponse(BaseModel):
    """Content extraction response schema. (Features: 156, 157, 160)"""
    title: str
    description: str
    content: str
    word_count: int
    links: List[LinkData]
    images: List[ImageData]
    structured_data: List[StructuredDataItem]
    extracted_at: str
    content_type: str
    status_code: int
    error: Optional[str] = None

class SiteStructure(BaseModel):
    """Site structure analysis schema. (Features: 156, 161)"""
    domain: str
    protocol: str
    is_secure: bool
    path_depth: int
    has_subdomain: bool

class WebsiteAnalysisResponse(BaseModel):
    """Website analysis response schema. (Features: 156, 157, 158, 161)"""
    url: str
    analysis_timestamp: str
    content_data: ContentExtractionResponse
    site_structure: SiteStructure
    is_research_paper: bool
    factual_claims: List[str]
    content_classification: str
    credibility_score: float
    error: Optional[str] = None

class StructuredDataResponse(BaseModel):
    """Structured data scraping response schema. (Features: 158, 160)"""
    url: str
    data: Dict[str, Any]
    scraped_at: str
    error: Optional[str] = None

class ResearchPaper(BaseModel):
    """Research paper schema. (Features: 159)"""
    title: str
    url: str
    abstract: Optional[str] = None
    authors: Optional[List[str]] = None
    published_date: Optional[str] = None
    source: str
    retrieved_at: str

class ResearchPaperResponse(BaseModel):
    """Research paper retrieval response schema. (Features: 159, 161)"""
    query: str
    papers: List[ResearchPaper]
    total_found: int
    error: Optional[str] = None

class BrowsingResult(BaseModel):
    """Individual browsing result schema. (Features: 162, 164)"""
    url: str
    analysis_timestamp: str
    content_data: ContentExtractionResponse
    site_structure: SiteStructure
    is_research_paper: bool
    factual_claims: List[str]
    content_classification: str
    credibility_score: float
    objective_relevance: Optional[float] = None

class AutonomousBrowsingResponse(BaseModel):
    """Autonomous browsing response schema. (Features: 162, 164)"""
    objective: str
    starting_url: str
    pages_visited: int
    max_depth_reached: int
    results: List[BrowsingResult]
    objective_achieved: bool
    browsed_at: str
    error: Optional[str] = None

# Additional utility schemas
class TrendingTopic(BaseModel):
    """Trending topic schema. (Features: 155, 161)"""
    topic: str
    results: List[SearchResult]

class TrendingResponse(BaseModel):
    """Trending topics response schema. (Features: 155, 161)"""
    trending_topics: List[TrendingTopic]
    updated_at: str

class BatchAnalysisResult(BaseModel):
    """Batch analysis result schema. (Features: 156, 161)"""
    batch_id: str
    total_urls: int
    successful_analyses: int
    failed_analyses: int
    results: List[WebsiteAnalysisResponse]

class WebSearchStatus(BaseModel):
    """Web search engine status schema. (Features: 155, 164)"""
    available_engines: List[str]
    features: Dict[str, bool]
    status: str 