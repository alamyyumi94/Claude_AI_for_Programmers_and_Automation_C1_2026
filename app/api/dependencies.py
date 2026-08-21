from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.database import get_database
from app.repositories.faq_repository import FAQRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.ticket_repository import TicketRepository
from app.services.analysis_service import AnalysisService
from app.services.claude_service import ClaudeService
from app.services.faq_service import FAQService
from app.services.response_service import ResponseService
from app.services.ticket_service import TicketService
from app.services.workflow_service import WorkflowService


def get_ticket_repository() -> TicketRepository:
    """Return a ticket repository bound to the connected database."""
    return TicketRepository(get_database())


def get_order_repository() -> OrderRepository:
    """Return an order repository bound to the connected database."""
    return OrderRepository(get_database())


def get_faq_repository() -> FAQRepository:
    """Return a FAQ repository bound to the connected database."""
    return FAQRepository(get_database())


async def get_claude_service() -> AsyncIterator[ClaudeService]:
    """Yield a Claude client and close it when the request finishes."""
    claude_service = ClaudeService()
    try:
        yield claude_service
    finally:
        await claude_service.close()


def get_analysis_service(
    claude_service: Annotated[ClaudeService, Depends(get_claude_service)],
) -> AnalysisService:
    return AnalysisService(claude_service)


def get_ticket_service(
    ticket_repository: Annotated[TicketRepository, Depends(get_ticket_repository)],
) -> TicketService:
    return TicketService(ticket_repository)


def get_faq_service(
    faq_repository: Annotated[FAQRepository, Depends(get_faq_repository)],
    claude_service: Annotated[ClaudeService, Depends(get_claude_service)],
) -> FAQService:
    return FAQService(
        faq_repository=faq_repository,
        claude_service=claude_service,
    )


def get_response_service(
    claude_service: Annotated[ClaudeService, Depends(get_claude_service)],
) -> ResponseService:
    return ResponseService(claude_service)


def get_workflow_service(
    analysis_service: Annotated[AnalysisService, Depends(get_analysis_service)],
    response_service: Annotated[ResponseService, Depends(get_response_service)],
    ticket_service: Annotated[TicketService, Depends(get_ticket_service)],
    order_repository: Annotated[OrderRepository, Depends(get_order_repository)],
    faq_repository: Annotated[FAQRepository, Depends(get_faq_repository)],
) -> WorkflowService:
    """Assemble the workflow orchestrator from already-wired dependencies."""
    return WorkflowService(
        analysis_service=analysis_service,
        response_service=response_service,
        ticket_service=ticket_service,
        order_repository=order_repository,
        faq_repository=faq_repository,
    )


ClaudeServiceDep = Annotated[ClaudeService, Depends(get_claude_service)]
AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]
TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]
FAQServiceDep = Annotated[FAQService, Depends(get_faq_service)]
OrderRepositoryDep = Annotated[OrderRepository, Depends(get_order_repository)]
ResponseServiceDep = Annotated[ResponseService, Depends(get_response_service)]
WorkflowServiceDep = Annotated[WorkflowService, Depends(get_workflow_service)]
