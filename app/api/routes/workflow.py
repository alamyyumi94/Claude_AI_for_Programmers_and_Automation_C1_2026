from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import WorkflowServiceDep
from app.schemas.workflow import (
    ProcessTicketRequest,
    ProcessTicketResponse,
)
from app.services.claude_service import ClaudeResponseError

router = APIRouter(
    prefix="/workflow",
    tags=["Workflow"],
)


@router.post(
    "/process",
    response_model=ProcessTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def process_ticket(
    request: ProcessTicketRequest,
    workflow_service: WorkflowServiceDep,
) -> ProcessTicketResponse:
    """Run the full support workflow and store the resulting ticket."""
    try:
        result = await workflow_service.process(request)
    except ClaudeResponseError as e:
        # A bad or unusable Claude reply is an upstream failure, not a client error.
        raise HTTPException(status_code=502, detail=str(e)) from e

    return ProcessTicketResponse(
        ticket=result.ticket,
        executed_steps=result.executed_steps,
        analysis_usage=result.analysis_usage,
        response_usage=result.response_usage,
    )
