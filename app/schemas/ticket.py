from datetime import datetime
from pydantic import Field

from app.schemas.common import StricModel, TicketStatus

from app.schemas.ai import TicketAnalysis

from app.schemas.order import OrderContext

from app.schemas.faq import FaqEntry


class TicketCreateRequest(StricModel):
    customer_id: str
    order_id: str | None = None
    message: str


class TicketResponse(StricModel):
    ticket_id: str
    customer_id: str
    order_id: str | None = None
    message: str

    analysis: TicketAnalysis

    order_context: OrderContext | None = None
    # What we searched the FAQ store for, and what came back.
    faq_query: list[str] = []
    faq_context: list[FaqEntry] = []

    status: TicketStatus
    escalation_reason: str | None = None
    processing_error: str | None = None
    created_at: datetime
    updated_at: datetime


class TicketListResponse(StricModel):
    items: list[TicketResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    skip: int
