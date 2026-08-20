from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.database import get_database
from app.repositories.faq_repository import FaqRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.ticket_repository import TicketRepository
from app.services.analysis_service import AnalysisService
from app.services.claude_service import ClaudeService
from app.services.faq_service import FaqService
from app.services.ticket_service import TicketService


def get_ticket_repository() -> TicketRepository:
    """Return a ticket repository bound to the connected database."""
    return TicketRepository(database=get_database())


def get_order_repository() -> OrderRepository:
    """Return an order repository bound to the connected database."""
    return OrderRepository(database=get_database())


def get_faq_repository() -> FaqRepository:
    """Return a FAQ repository bound to the connected database."""
    return FaqRepository(database=get_database())


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
    return AnalysisService(claude_service=claude_service)


def get_ticket_service(
    ticket_repository: Annotated[TicketRepository, Depends(get_ticket_repository)],
    analysis_service: Annotated[AnalysisService, Depends(get_analysis_service)],
    order_repository: Annotated[OrderRepository, Depends(get_order_repository)],
    faq_repository: Annotated[FaqRepository, Depends(get_faq_repository)],
) -> TicketService:
    return TicketService(
        ticket_repository=ticket_repository,
        analysis_service=analysis_service,
        order_repository=order_repository,
        faq_repository=faq_repository,
    )


def get_faq_service(
    faq_repository: Annotated[FaqRepository, Depends(get_faq_repository)],
) -> FaqService:
    return FaqService(faq_repository=faq_repository)


TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]
FaqServiceDep = Annotated[FaqService, Depends(get_faq_service)]
