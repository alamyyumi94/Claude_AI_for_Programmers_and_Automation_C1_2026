from enum import Enum

from pydantic import Field, model_validator

from app.schemas.common import StrictModel, TicketCategories, Sentiment, Priority

from app.schemas.usage import AIUsage


class SummariseRequest(StrictModel):
    text: str = Field(min_length=1, max_length=5000)


class SummariseResponse(StrictModel):
    summary: str
    model: str
    input_tokens: int
    output_tokens: int


class AnalyseRequest(StrictModel):
    text: str = Field(min_length=5, max_length=5000)


class TicketAnalysis(StrictModel):
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


class AnalyseResponse(StrictModel):
    analysis: TicketAnalysis
    usage: AIUsage


class GenerateResponseRequest(StrictModel):
    # The customer message remains untrusted input
    customer_message: str = Field(
        min_length=5,
        max_length=5000,
    )
    # Customer and Order intentifiers
    customer_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )

    order_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )

    @model_validator(mode="after")
    def validate_order_context(
        self,
    ) -> "GenerateResponseRequest":
        # An order lookup cannot be safely performed without both a customer_id and an order_id. If one is provided, the other must be as well.
        if (
            self.order_id and not self.customer_id
        ):
            raise ValueError(
                "customer_id is required when order_id is provided"
            )

        return self

class ResponseContextUsed(StrictModel):
    # Make trusted context available to the app for logging and debugging purposes. This is not sent to Claude.
    order_id: str | None = None

class GenerateResponseResponse(StrictModel):
    draft_response: str = Field(
        min_length=1,
        max_length=5000,
    )
    context_used: ResponseContextUsed
    usage: AIUsage
