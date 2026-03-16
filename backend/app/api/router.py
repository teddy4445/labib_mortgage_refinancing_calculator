from fastapi import APIRouter

from backend.app.api.routes import admin, alerts, auth, health, mortgages


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(mortgages.router, prefix="/mortgages", tags=["mortgages"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
