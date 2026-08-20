from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.database import get_database
from app.repositories.ticket_repository import (
    TicketRepository,
)
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketListResponse,
    TicketResponse,
)
from app.services.analysis_service import (
    AnalysisService,
)
from app.services.claude_service import (
    ClaudeService,
)
from app.services.ticket_service import (
    TicketService,
)


router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
)


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    request: TicketCreateRequest,
) -> TicketResponse:
    database = get_database()

    # Repository/service objects keep database logic out of the route itself.
    ticket_service = TicketService(
        TicketRepository(database)
    )

    claude_service = ClaudeService()
    analysis_service = AnalysisService(
        claude_service
    )

    try:
        # Analyse first; only validated analysis is persisted.
        analysis_result = (
            await analysis_service.analyse(
                request.message
            )
        )
    finally:
        await claude_service.close()

    return await ticket_service.create(
        request,
        analysis_result.data,
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
async def get_ticket(
    ticket_id: str,
) -> TicketResponse:
    service = TicketService(
        TicketRepository(
            get_database()
        )
    )

    ticket = await service.get(
        ticket_id
    )

    # Convert a missing database record into a normal HTTP 404.
    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found.",
        )

    return ticket


@router.get(
    "",
    response_model=TicketListResponse,
)
async def list_tickets(
    customer_id: str | None = Query(
        default=None,
        min_length=3,
        max_length=50,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
) -> TicketListResponse:
    service = TicketService(
        TicketRepository(
            get_database()
        )
    )

    return await service.list(
        customer_id=customer_id,
        limit=limit,
        skip=skip,
    )
