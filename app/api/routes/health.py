from fastapi import APIRouter

from app.schemas.common import healthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=healthResponse)
async def health_check() -> healthResponse:
    """
    Health check endpoint to verify the API is running.
    """
    return healthResponse(status="ok")
