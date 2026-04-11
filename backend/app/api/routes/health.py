from fastapi import APIRouter, Request

from backend.app.api.response_utils import build_response_meta
from backend.app.schemas import HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def healthcheck(request: Request) -> HealthResponse:
    return HealthResponse(status="ok", meta=build_response_meta(request))
