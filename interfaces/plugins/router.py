from fastapi import APIRouter
from .list import list_router
from .manage import manage_router
from .execute import execute_router
from .hooks import hooks_router

router = APIRouter()
router.include_router(list_router)
router.include_router(manage_router)
router.include_router(execute_router)
router.include_router(hooks_router)
