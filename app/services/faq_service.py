from __future__ import annotations

import logging

from app.repositories.faq_repository import FaqRepository
from app.schemas.common import TicketCategories
from app.schemas.faq import FaqEntry, FaqListResponse, FaqSearchRequest

logger = logging.getLogger(__name__)


class FaqService:
    """Serves approved FAQ / policy entries.

    Services own the flow; repositories own storage and database access.

    Attributes:
        faq_repository: Repository for FAQ read operations.
    """

    def __init__(self, faq_repository: FaqRepository) -> None:
        self._faq_repository = faq_repository

    async def search(self, request: FaqSearchRequest) -> FaqListResponse:
        """Full-text search over approved FAQ entries.

        Args:
            request: The search query, optional category filter and result limit.

        Returns:
            Matching entries plus the total number of active entries.
        """
        items = await self._faq_repository.search(
            query=request.query,
            category=request.category,
            limit=request.limit,
        )
        logger.debug("FAQ search for %r returned %d entries", request.query, len(items))
        return FaqListResponse(
            items=items,
            total=await self._faq_repository.count_active(),
        )

    async def list_faqs(
        self,
        category: TicketCategories | None = None,
        limit: int = 20,
    ) -> FaqListResponse:
        """List active entries, used when there is no search query.

        Args:
            category: Optional ticket category filter. None lists every category.
            limit: Maximum number of entries to return.

        Returns:
            Matching active entries plus the total number of active entries.
        """
        return FaqListResponse(
            items=await self._faq_repository.list_active(category, limit=limit),
            total=await self._faq_repository.count_active(),
        )

    async def get_faq(self, faq_id: str) -> FaqEntry | None:
        """Retrieve a single FAQ entry by its ID.

        Args:
            faq_id: The unique identifier of the FAQ entry.

        Returns:
            The entry if found, None otherwise.
        """
        return await self._faq_repository.get_by_id(faq_id)
