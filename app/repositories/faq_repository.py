from typing import Any

from app.schemas.common import TicketCategories
from app.schemas.faq import FaqEntry


# Projection is an allowlist of fields the repository returns to the app.
FAQ_PROJECTION = {
    "_id": 0,
    "faq_id": 1,
    "category": 1,
    "question": 1,
    "answer": 1,
    "keywords": 1,
    "active": 1,
    "updated_at": 1,
}


class FaqRepository:
    def __init__(
        self,
        database: Any,
    ) -> None:
        # Repositories own database access; ClaudeService does not.
        self.collection = database.faqs

    async def search(
        self,
        query: str,
        category: TicketCategories | None = None,
        limit: int = 5,
    ) -> list[FaqEntry]:
        """Full-text search over question, answer and keywords.

        Relies on the faq_text_search index created by scripts/seed_database.py.
        Inactive entries are never returned, so the AI cannot quote a
        withdrawn policy.
        """
        filters: dict[str, Any] = {
            "$text": {"$search": query},
            "active": True,
        }
        if category is not None:
            filters["category"] = category.value

        cursor = (
            self.collection.find(filters, projection=FAQ_PROJECTION)
            # Best text match first. Sorting on the meta field does not require
            # projecting the score, which would break FaqEntry's extra="forbid".
            .sort([("score", {"$meta": "textScore"})])
            .limit(limit)
        )

        return [FaqEntry.model_validate(document) async for document in cursor]

    async def get_by_id(
        self,
        faq_id: str,
    ) -> FaqEntry | None:
        document = await self.collection.find_one(
            {"faq_id": faq_id},
            projection=FAQ_PROJECTION,
        )
        return FaqEntry.model_validate(document) if document else None

    async def list_by_category(
        self,
        category: TicketCategories,
        limit: int = 20,
    ) -> list[FaqEntry]:
        """Active entries for one category, used when there is no search query."""
        cursor = (
            self.collection.find(
                {"category": category.value, "active": True},
                projection=FAQ_PROJECTION,
            )
            .sort("faq_id")
            .limit(limit)
        )

        return [FaqEntry.model_validate(document) async for document in cursor]

    async def count_active(self) -> int:
        """Total active entries, for FaqListResponse.total."""
        return await self.collection.count_documents({"active": True})
