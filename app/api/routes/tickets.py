from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import AnalysisServiceDep, TicketServiceDep
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
    analysis_service: AnalysisServiceDep,
) -> TicketResponse:
    """Analyse an incoming customer message and store the resulting ticket."""
    try:
        # Analyse first; only validated analysis is persisted.
        analysis_result = await analysis_service.analyse(input.message)
    except ClaudeResponseError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return await ticket_service.create(input, analysis_result.data)


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    ticket_service: TicketServiceDep,
    customer_id: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> TicketListResponse:
    """List stored tickets with pagination, optionally scoped to one customer."""
    return await ticket_service.list(
        customer_id=customer_id,
        limit=limit,
        skip=skip,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    ticket_service: TicketServiceDep,
) -> TicketResponse:
    """Retrieve a single ticket by id."""
    ticket = await ticket_service.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket
