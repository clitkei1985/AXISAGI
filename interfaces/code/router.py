from fastapi import APIRouter
from .analysis import analysis_router
from .review import review_router
from .refactor import refactor_router
from .formatting import formatting_router
from .complexity import complexity_router
from .duplication import duplication_router
from .search import search_router

router = APIRouter()
router.include_router(analysis_router)
router.include_router(review_router)
router.include_router(refactor_router)
router.include_router(formatting_router)
router.include_router(complexity_router)
router.include_router(duplication_router)
router.include_router(search_router)
