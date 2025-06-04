from fastapi import APIRouter
from core.performance_monitor import PerformanceMonitor

router = APIRouter(prefix="/api/performance", tags=["performance"])

@router.get("/", response_model=dict)
def get_performance():
    return {"metrics": PerformanceMonitor.get_current_metrics()}
