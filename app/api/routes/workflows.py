from fastapi import (
    APIRouter,
    status,
)

# Provides access to the application's database connection.
from app.database import get_database

# Repository used to retrieve trusted FAQ data from the database.
from app.repositories.faq_repository import FAQRepository

# Repository used to retrieve trusted order data from the database.
from app.repositories.order_repository import OrderRepository

# Repository used to create and update ticket records.
from app.repositories.ticket_repository import TicketRepository

# Request and response schemas for the ticket-processing workflow endpoint.
from app.schemas.workflow import (
    ProcessTicketRequest,
    ProcessTicketResponse,
)

# Service responsible for analysing the incoming customer message.
from app.services.analysis_service import AnalysisService

# Low-level service responsible for communicating with Claude.
from app.services.claude_service import ClaudeService

# Service responsible for generating the final customer-facing draft response.
from app.services.response_service import ResponseService

# Service responsible for ticket-related application logic and persistence.
from app.services.ticket_service import TicketService

# Main orchestration service that coordinates the complete ticket workflow.
from app.services.workflow_service import WorkflowService


# Group workflow-related endpoints under /workflows in the API.
router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
)


# Create a POST /workflows/process-ticket endpoint.
# A successful workflow creates a ticket, so the endpoint returns HTTP 201.
@router.post(
    "/process-ticket",
    response_model=ProcessTicketResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def process_ticket(
    # FastAPI/Pydantic validates the incoming JSON as a ProcessTicketRequest.
    request: ProcessTicketRequest,
) -> ProcessTicketResponse:

    # Get the shared application database dependency.
    database = get_database()

    # Create the Claude client used by both analysis and response generation.
    claude_service = ClaudeService()

    # Assemble the complete workflow and inject all required services/repositories.
    service = WorkflowService(

        # Analyses the ticket and returns structured decisions.
        analysis_service=AnalysisService(claude_service),

        # Generates the final draft using Claude and retrieved context.
        response_service=ResponseService(claude_service),

        # TicketService uses TicketRepository to persist ticket data.
        ticket_service=TicketService(TicketRepository(database)),

        # Provides trusted order lookups.
        order_repository=OrderRepository(database),

        # Provides trusted FAQ retrieval/search.
        faq_repository=FAQRepository(database),
    )

    try:
        # Hand the entire request to WorkflowService to execute the workflow.
        result = await service.process(
            request
        )
    finally:
        # Always close the Claude client, even if any workflow step fails.
        await claude_service.close()

    # Convert the internal workflow result into the API response model.
    return ProcessTicketResponse(

        # Final ticket after all workflow processing and database updates.
        ticket=result.ticket,

        # Ordered record of which workflow steps actually executed.
        executed_steps=(result.executed_steps),

        # Claude model/token usage from the analysis call.
        analysis_usage=(result.analysis_usage),

        # Claude model/token usage from response generation.
        response_usage=(result.response_usage),
    )
