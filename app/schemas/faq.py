from datetime import datetime

from pydantic import Field

from app.schemas.common import StricModel, TicketCategories


class FaqEntry(StricModel):
    """A single approved FAQ / policy answer the AI is allowed to rely on."""

    faq_id: str = Field(
        min_length=1, max_length=50, description="Unique identifier for the FAQ entry"
    )
    category: TicketCategories = Field(
        description="Ticket category this entry answers, matching TicketAnalysis.category"
    )
    question: str = Field(
        min_length=5, max_length=300, description="Customer-facing question"
    )
    answer: str = Field(
        min_length=5,
        max_length=2000,
        description="Approved answer. Only this text may be quoted back to a customer.",
    )
    keywords: list[str] = Field(
        min_length=1,
        description="Search terms used to match a customer message to this entry",
    )
    active: bool = Field(
        default=True, description="Inactive entries must not be used in responses"
    )
    updated_at: datetime = Field(description="When the entry was last approved")


class FaqSearchRequest(StricModel):
    query: str = Field(min_length=2, max_length=500)
    category: TicketCategories | None = None
    limit: int = Field(default=5, ge=1, le=20)


class FaqListResponse(StricModel):
    items: list[FaqEntry]
    total: int = Field(ge=0)
