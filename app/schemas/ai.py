from pydantic import Field, model_validator

from app.schemas.common import StricModel, TicketCategories, Sentiment, Priority

from app.schemas.usage import AIUsage


class SummariseRequest(StricModel):
    text: str = Field(min_length=1, max_length=5000)


class SummariseResponse(StricModel):
    summary: str
    model: str
    input_tokens: int
    output_tokens: int


class AnalyseRequest(StricModel):
    text: str = Field(min_length=5, max_length=5000)


class TicketAnalysis(StricModel):
    summary: str = Field(min_length=5, max_length=5000)

    category: TicketCategories
    sentiment: Sentiment
    priority: Priority

    needs_order_lookup: bool
    needs_faq_lookup: bool
    needs_human_review: bool

    faq_query: str | None = Field(default=None, max_length=500)

    human_review_reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_dependencies(self) -> "TicketAnalysis":
        if self.needs_faq_lookup and not self.faq_query:
            raise ValueError("faq_query must be provided if needs_faq_lookup is True")
        if self.needs_human_review and not self.human_review_reason:
            raise ValueError(
                "human_review_reason must be provided if needs_human_review is True"
            )
        return self


class ResponseContextUsed(StricModel):
    customer_id: str = Field(min_length=1, max_length=100)
    order_id: str = Field(min_length=1, max_length=100)
    draft_response: str | None = None


class GenerateResponseRequest(StricModel):
    customer_message: str = Field(
        min_length=5,
        max_length=5000,
    )
    customer_id: str | None = None
    order_id: str | None = None


class GenerateResponseResponse(StricModel):
    draft_response: str = Field(
        min_length=1,
        max_length=5000,
    )
    context_used: ResponseContextUsed
    usage: AIUsage


class AnalyseResponse(StricModel):
    analysis: TicketAnalysis
    usage: AIUsage
