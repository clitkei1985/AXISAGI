from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from core.database import get_db, User
from core.security import get_current_active_user
from .schemas import Dashboard, DashboardWidget

logger = logging.getLogger(__name__)
dashboards_router = APIRouter()

@dashboards_router.get("/dashboards/", response_model=List[Dashboard])
async def list_dashboards(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # In a real implementation, this would fetch from database
    default_dashboard = Dashboard(
        dashboard_id="default",
        name="System Overview",
        description="Main system metrics and KPIs",
        widgets=[
            DashboardWidget(
                widget_id="system_metrics",
                title="System Metrics",
                type="metrics_grid",
                data={}
            ),
            DashboardWidget(
                widget_id="user_growth",
                title="User Growth",
                type="line_chart",
                data={}
            ),
        ]
    )
    return [default_dashboard]

@dashboards_router.get("/dashboards/{dashboard_id}", response_model=Dashboard)
async def get_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # In a real implementation, fetch dashboard by ID
    if dashboard_id == "default":
        return await list_dashboards(current_user, db)[0]
    raise HTTPException(status_code=404, detail="Dashboard not found") 