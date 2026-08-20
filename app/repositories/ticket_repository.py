from datetime import datetime, timezone
from typing import Any

from bson.codec_options import CodecOptions
from pymongo import DESCENDING

from app.core.ids import new_ticket_id
from app.schemas.common import TicketStatus
from app.schemas.ticket import TicketResponse


# Projection is an allowlist of fields the repository returns to the app.
# _id is excluded so documents validate against TicketResponse directly.
TICKET_PROJECTION = {
    "_id": 0,
    "ticket_id": 1,
    "customer_id": 1,
    "order_id": 1,
    "message": 1,
    "analysis": 1,
    "order_context": 1,
    "faq_query": 1,
    "faq_context": 1,
    "status": 1,
    "escalation_reason": 1,
    "processing_error": 1,
    "created_at": 1,
    "updated_at": 1,
}


class TicketRepository:
    """MongoDB repository for ticket data operations."""

    def __init__(
        self,
        database: Any,
    ) -> None:
        # Repositories own database access; services do not.
        # tz_aware keeps datetimes UTC-aware on read, matching what we write.
        self.collection = database.get_collection(
            "tickets",
            codec_options=CodecOptions(tz_aware=True, tzinfo=timezone.utc),
        )

    async def create(self, ticket_data: dict) -> TicketResponse:
        """Create a new ticket. The repository owns id and timestamps."""
        now = datetime.now(timezone.utc)
        ticket = TicketResponse(
            **{
                "ticket_id": new_ticket_id(),
                "status": TicketStatus.NEW,
                "faq_query": [],
                "created_at": now,
                "updated_at": now,
                **ticket_data,
            }
        )
        # Validate first, then persist, so a bad payload never reaches Mongo.
        await self.collection.insert_one(ticket.model_dump())
        return ticket

    async def get_by_id(self, ticket_id: str) -> TicketResponse | None:
        """Get a ticket by id."""
        document = await self.collection.find_one(
            {"ticket_id": ticket_id},
            projection=TICKET_PROJECTION,
        )
        return TicketResponse.model_validate(document) if document else None

    async def get_all(self, skip: int = 0, limit: int = 50) -> list[TicketResponse]:
        """Get a page of tickets, newest first."""
        cursor = (
            self.collection.find({}, projection=TICKET_PROJECTION)
            # Matches the (customer_id, created_at DESC) index built by the seed script.
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return [TicketResponse.model_validate(document) async for document in cursor]

    async def count(self) -> int:
        """Total tickets held, for TicketListResponse.total."""
        return await self.collection.count_documents({})

    async def update(self, ticket_id: str, ticket_data: dict) -> TicketResponse | None:
        """Update a ticket by id. Re-validates the whole model."""
        existing = await self.get_by_id(ticket_id)
        if existing is None:
            return None

        # Merge and validate before writing, so a rejected update leaves the
        # stored document untouched.
        updated = TicketResponse.model_validate(
            {
                **existing.model_dump(),
                **ticket_data,
                # id is immutable; updated_at is repository-owned.
                "ticket_id": ticket_id,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        await self.collection.replace_one(
            {"ticket_id": ticket_id},
            updated.model_dump(),
        )
        return updated

    async def delete(self, ticket_id: str) -> bool:
        """Delete a ticket by id."""
        result = await self.collection.delete_one({"ticket_id": ticket_id})
        return result.deleted_count > 0
