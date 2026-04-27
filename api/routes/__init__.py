from fastapi import APIRouter
from routes.plans import router as plans_router
from routes.tasks import router as tasks_router
from routes.health import router as health_router

# Crear un router principal que agrupa todos los sub-routers
api_router = APIRouter()
api_router.include_router(plans_router, tags=["plans"])
api_router.include_router(tasks_router, tags=["tasks"])
api_router.include_router(health_router, tags=["health"])

__all__ = ["api_router"]
