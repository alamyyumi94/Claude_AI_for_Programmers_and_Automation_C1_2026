from datetime import datetime, timezone

from app.core.ids import new_ticket_id
from app.schemas.common import TicketStatus
from app.schemas.ticket import TicketResponse


class TicketRepository:
    """In-memory repository for ticket data operations."""

    def __init__(self) -> None:
        # Keyed by ticket_id so lookups are O(1) and ids stay unique.
        self._tickets: dict[str, TicketResponse] = {}

    def create(self, ticket_data: dict) -> TicketResponse:
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
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def get_by_id(self, ticket_id: str) -> TicketResponse | None:
        """Get a ticket by id."""
        return self._tickets.get(ticket_id)

    def get_all(self, skip: int = 0, limit: int = 50) -> list[TicketResponse]:
        """Get a page of tickets. Returns a copy, not the internal store."""
        return list(self._tickets.values())[skip : skip + limit]

    def count(self) -> int:
        """Total tickets held, for TicketListResponse.total."""
        return len(self._tickets)

    def update(self, ticket_id: str, ticket_data: dict) -> TicketResponse | None:
        """Update a ticket by id. Re-validates the whole model."""
        existing = self._tickets.get(ticket_id)
        if existing is None:
            return None
        updated = TicketResponse.model_validate(
            {
                **existing.model_dump(),
                **ticket_data,
                # id is immutable; updated_at is repository-owned.
                "ticket_id": ticket_id,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._tickets[ticket_id] = updated
        return updated

    def delete(self, ticket_id: str) -> bool:
        """Delete a ticket by id."""
        return self._tickets.pop(ticket_id, None) is not None
