from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import TicketServiceDep
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketListResponse,
    TicketResponse,
)
from app.services.claude_service import ClaudeResponseError

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    input: TicketCreateRequest,
    ticket_service: TicketServiceDep,
) -> TicketResponse:
    """Analyse an incoming customer message and store the resulting ticket."""
    try:
        return await ticket_service.create_ticket(input)
    except ClaudeResponseError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    ticket_service: TicketServiceDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> TicketListResponse:
    """List stored tickets, newest first insertion order, with pagination."""
    return ticket_service.list_tickets(skip=skip, limit=limit)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    ticket_service: TicketServiceDep,
) -> TicketResponse:
    """Retrieve a single ticket by id."""
    ticket = ticket_service.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket


@router.post("/{ticket_id}/close", response_model=TicketResponse)
async def close_ticket(
    ticket_id: str,
    ticket_service: TicketServiceDep,
) -> TicketResponse:
    """Close a ticket."""
    ticket = ticket_service.close_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket
