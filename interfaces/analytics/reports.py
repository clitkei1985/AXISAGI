from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from core.database import get_db, User
from core.security import get_current_admin_user
from modules.analytics_reporting.analytics import get_analytics_collector
from .schemas import (
    ReportRequest,
    SystemOverviewReport,
    UserEngagementReport,
    PerformanceReport,
    ContentAnalysisReport
)

logger = logging.getLogger(__name__)
reports_router = APIRouter()

@reports_router.post("/reports/generate")
async def generate_report(
    report_request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    collector = get_analytics_collector(db)
    try:
        report = await collector.generate_report(
            report_request.report_type,
            report_request.start_date,
            report_request.end_date,
            report_request.filters
        )
        if "error" in report:
            raise HTTPException(status_code=400, detail=report["error"])
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail="Report generation failed")

@reports_router.get("/reports/system-overview")
async def get_system_overview_report(
    start_date: datetime = Query(..., description="Start date for the report"),
    end_date: datetime = Query(..., description="End date for the report"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    collector = get_analytics_collector(db)
    report = await collector.generate_report("system_overview", start_date, end_date)
    return SystemOverviewReport(**report)

@reports_router.get("/reports/user-engagement")
async def get_user_engagement_report(
    start_date: datetime = Query(..., description="Start date for the report"),
    end_date: datetime = Query(..., description="End date for the report"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    collector = get_analytics_collector(db)
    report = await collector.generate_report("user_engagement", start_date, end_date)
    return UserEngagementReport(**report)

@reports_router.get("/reports/performance")
async def get_performance_report(
    start_date: datetime = Query(..., description="Start date for the report"),
    end_date: datetime = Query(..., description="End date for the report"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    collector = get_analytics_collector(db)
    report = await collector.generate_report("performance", start_date, end_date)
    return PerformanceReport(**report)

@reports_router.get("/reports/content-analysis")
async def get_content_analysis_report(
    start_date: datetime = Query(..., description="Start date for the report"),
    end_date: datetime = Query(..., description="End date for the report"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    collector = get_analytics_collector(db)
    report = await collector.generate_report("content_analysis", start_date, end_date)
    return ContentAnalysisReport(**report) 