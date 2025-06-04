# interfaces/web/router.py

import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from core.database import get_db, User
from core.security import get_current_active_user
from modules.web_search.engine import get_web_search_engine
from modules.frontend_ui.router import router as frontend_router
from .schemas import (
    WebSearchRequest, WebSearchResponse, ContentExtractionRequest, 
    ContentExtractionResponse, WebsiteAnalysisResponse, StructuredDataRequest,
    StructuredDataResponse, ResearchPaperRequest, ResearchPaperResponse,
    AutonomousBrowsingRequest, AutonomousBrowsingResponse
)

router = APIRouter()

# Mount the 'static' folder at the root URL path
router.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "..", "modules", "frontend_ui", "static")),
    name="static"
)

# Include frontend routes at root level
router.include_router(frontend_router)

@router.get("/", include_in_schema=False)
async def serve_ui():
    """
    Serve the main chat UI (index.html). Access by visiting http://<host>:8000/
    """
    root = os.path.dirname(__file__)
    index_path = os.path.join(root, "..", "..", "modules", "frontend_ui", "templates", "index.html")
    return FileResponse(index_path)

@router.post("/api/web/search", response_model=WebSearchResponse)
async def search_web(
    request: WebSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Perform comprehensive web search. (Features: 155, 161, 162, 163)"""
    try:
        async with await get_web_search_engine() as search_engine:
            results = await search_engine.search_web(
                query=request.query,
                engine=request.engine,
                max_results=request.max_results,
                include_content=request.include_content
            )
            
            return WebSearchResponse(**results)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/api/web/extract", response_model=ContentExtractionResponse)
async def extract_content(
    request: ContentExtractionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Extract content from a web page. (Features: 156, 157, 160)"""
    try:
        async with await get_web_search_engine() as search_engine:
            content_data = await search_engine.extract_content(request.url)
            
            return ContentExtractionResponse(**content_data)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content extraction failed: {str(e)}")

@router.post("/api/web/analyze", response_model=WebsiteAnalysisResponse)
async def analyze_website(
    url: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Perform comprehensive website analysis. (Features: 156, 157, 158, 161)"""
    try:
        async with await get_web_search_engine() as search_engine:
            analysis = await search_engine.analyze_website(url)
            
            return WebsiteAnalysisResponse(**analysis)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Website analysis failed: {str(e)}")

@router.post("/api/web/scrape", response_model=StructuredDataResponse)
async def scrape_structured_data(
    request: StructuredDataRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Scrape structured data using CSS selectors. (Features: 158, 160)"""
    try:
        async with await get_web_search_engine() as search_engine:
            data = await search_engine.scrape_structured_data(
                url=request.url,
                selectors=request.selectors
            )
            
            return StructuredDataResponse(**data)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data scraping failed: {str(e)}")

@router.post("/api/web/research", response_model=ResearchPaperResponse)
async def retrieve_research_papers(
    request: ResearchPaperRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve research papers from academic sources. (Features: 159, 161)"""
    try:
        async with await get_web_search_engine() as search_engine:
            papers = await search_engine.retrieve_research_papers(
                query=request.query,
                max_results=request.max_results
            )
            
            return ResearchPaperResponse(
                query=request.query,
                papers=papers,
                total_found=len(papers)
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research paper retrieval failed: {str(e)}")

@router.post("/api/web/browse", response_model=AutonomousBrowsingResponse)
async def autonomous_browse(
    request: AutonomousBrowsingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Perform autonomous browsing to achieve an objective. (Features: 162, 164)"""
    try:
        async with await get_web_search_engine() as search_engine:
            results = await search_engine.autonomous_browse(
                starting_url=request.starting_url,
                objective=request.objective,
                max_depth=request.max_depth,
                max_pages=request.max_pages
            )
            
            return AutonomousBrowsingResponse(**results)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autonomous browsing failed: {str(e)}")

@router.get("/api/web/status")
async def get_web_search_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get web search engine status and capabilities. (Features: 155, 164)"""
    return {
        "available_engines": ["duckduckgo", "google", "bing"],
        "features": {
            "web_search": True,
            "content_extraction": True,
            "website_analysis": True,
            "structured_scraping": True,
            "research_papers": True,
            "autonomous_browsing": True
        },
        "status": "operational"
    }

@router.post("/api/web/batch-analyze")
async def batch_analyze_urls(
    urls: List[str],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze multiple URLs in batch. (Features: 156, 161)"""
    if len(urls) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 URLs per batch request")
    
    try:
        async with await get_web_search_engine() as search_engine:
            results = []
            for url in urls:
                try:
                    analysis = await search_engine.analyze_website(url)
                    results.append(analysis)
                except Exception as e:
                    results.append({
                        'url': url,
                        'error': str(e),
                        'analyzed_at': 'failed'
                    })
            
            return {
                'batch_id': f"batch_{len(results)}_{hash(str(urls))}",
                'total_urls': len(urls),
                'successful_analyses': len([r for r in results if 'error' not in r]),
                'failed_analyses': len([r for r in results if 'error' in r]),
                'results': results
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.get("/api/web/trending")
async def get_trending_topics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get trending topics from various sources. (Features: 155, 161)"""
    try:
        async with await get_web_search_engine() as search_engine:
            trending_searches = [
                "artificial intelligence",
                "machine learning",
                "web development",
                "data science",
                "cybersecurity"
            ]
            
            trending_results = []
            for topic in trending_searches:
                try:
                    results = await search_engine.search_web(
                        query=topic,
                        max_results=3,
                        include_content=False
                    )
                    trending_results.append({
                        'topic': topic,
                        'results': results.get('results', [])
                    })
                except Exception:
                    continue
            
            return {
                'trending_topics': trending_results,
                'updated_at': 'real-time'
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trending topics: {str(e)}")
