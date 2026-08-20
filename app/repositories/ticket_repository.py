from typing import Any

from pymongo import DESCENDING

from app.schemas.ticket import TicketResponse


# Exclude MongoDB's internal _id from application responses.
TICKET_PROJECTION = {
    "_id": 0,
}


class TicketRepository:
    def __init__(
        self,
        database: Any,
    ) -> None:
        self.collection = database.tickets

    async def insert(
        self,
        ticket: TicketResponse,
    ) -> TicketResponse:
        # Store a validated Pydantic model as a MongoDB document.
        await self.collection.insert_one(
            ticket.model_dump(
                mode="python"
            )
        )
        return ticket

    async def replace(
        self,
        ticket: TicketResponse,
    ) -> TicketResponse:
        # Replace the application-owned ticket by its stable ticket_id.
        result = (
            await self.collection.replace_one(
                {
                    "ticket_id":
                        ticket.ticket_id,
                },
                ticket.model_dump(
                    mode="python"
                ),
            )
        )

        if result.matched_count != 1:
            raise RuntimeError(
                "Ticket no longer exists."
            )

        return ticket

    async def get_by_id(
        self,
        ticket_id: str,
    ) -> TicketResponse | None:
        document = (
            await self.collection.find_one(
                {
                    "ticket_id":
                        ticket_id,
                },
                TICKET_PROJECTION,
            )
        )

        if document is None:
            return None

        # Validate persisted data when it re-enters the application layer.
        return TicketResponse.model_validate(
            document
        )

    async def list(
        self,
        *,
        customer_id: str | None = None,
        limit: int = 20,
        skip: int = 0,
    ) -> tuple[
        list[TicketResponse],
        int,
    ]:
        query: dict[str, object] = {}

        # Optional customer filter keeps this method reusable.
        if customer_id:
            query["customer_id"] = customer_id

        total = (
            await self.collection
            .count_documents(query)
        )

        # Newest tickets first, then apply pagination.
        cursor = (
            self.collection.find(
                query,
                TICKET_PROJECTION,
            )
            .sort(
                "created_at",
                DESCENDING,
            )
            .skip(skip)
            .limit(limit)
        )

        items: list[TicketResponse] = []

        async for document in cursor:
            items.append(
                TicketResponse
                .model_validate(document)
            )

        return items, total
