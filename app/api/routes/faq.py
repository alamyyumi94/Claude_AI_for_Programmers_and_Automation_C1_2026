from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import FaqServiceDep
from app.schemas.common import TicketCategories
from app.schemas.faq import FaqEntry, FaqListResponse, FaqSearchRequest

router = APIRouter(prefix="/faqs", tags=["FAQs"])


@router.post("/search", response_model=FaqListResponse)
async def search_faqs(
    input: FaqSearchRequest,
    faq_service: FaqServiceDep,
) -> FaqListResponse:
    """Full-text search over approved FAQ entries."""
    return await faq_service.search(input)


@router.get("", response_model=FaqListResponse)
async def list_faqs(
    faq_service: FaqServiceDep,
    category: Annotated[TicketCategories | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> FaqListResponse:
    """List active FAQ entries, optionally filtered by category."""
    return await faq_service.list_faqs(category, limit=limit)


@router.get("/{faq_id}", response_model=FaqEntry)
async def get_faq(
    faq_id: str,
    faq_service: FaqServiceDep,
) -> FaqEntry:
    """Retrieve a single FAQ entry by id."""
    faq = await faq_service.get_faq(faq_id)
    if faq is None:
        raise HTTPException(status_code=404, detail="FAQ not found.")
    return faq
