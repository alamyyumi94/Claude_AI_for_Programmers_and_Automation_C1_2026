# dataclass gives us a simple immutable result object for returning generated response data.
from dataclasses import dataclass

# Repository responsible for retrieving order data from the application's data source.
from app.repositories.order_repository import OrderRepository

# Pydantic request model describing the input needed to generate a customer response.
from app.schemas.ai import GenerateResponseRequest

# Service responsible for asking Claude to generate the actual draft response.
from app.services.response_service import ResponseService

# GenerateResponseService now retrieves approved FAQ context as well as orders.
from app.repositories.faq_repository import FAQRepository


@dataclass(frozen=True)
class GenerateResponseResult:
    draft_response: str         # Final draft generated for the customer.
    order_id_used: str | None   # Order ID actually used as context, or None if no order was found/used.
    faq_ids_used: list[str]     # Record which approved FAQ IDs were actually supplied to Claude.
    model: str                  # Claude model that produced the response.
    input_tokens: int           # Number of tokens Claude processed as input.
    output_tokens: int          # Number of tokens Claude generated as output.


class GenerateResponseService:
    # This service coordinates order lookup and AI response generation.
    def __init__(
        self,
        *,
        response_service: ResponseService,
        order_repository: OrderRepository,
        faq_repository: FAQRepository,  # Repository used to resolve caller-supplied FAQ IDs to approved records.
    ) -> None:
        self.response_service = response_service    # Store the AI response-generation dependency.
        self.order_repository = order_repository  # Store the repository used to retrieve trusted order data.
        self.faq_repository = faq_repository      # Save the repository dependency for use during generation.

    async def generate(
        self,
        request: GenerateResponseRequest,
    ) -> GenerateResponseResult:
        order_context = None    # Start with no order context because order information is optional.

        # Only attempt an order lookup when both customer_id and order_id were supplied.
        if request.order_id and request.customer_id:
            # Retrieve the specific order while also ensuring it belongs to the given customer.
            order_context = (
                await self.order_repository
                .get_order_for_customer(
                    request.customer_id,
                    request.order_id,
                )
            )

        faq_context = await self.faq_repository.get_by_ids(
            request.faq_ids
        )

        # Ask the response service to generate the draft using the customer message
        # plus trusted order data retrieved by our application, if available.
        claude_result = (
            await self.response_service
            .generate_draft(
                request.customer_message,
                order_context=order_context,
                faq_context=faq_context,
            )
        )

        # Convert the Claude/service result into the result shape expected by the API layer.
        return GenerateResponseResult(
            draft_response=claude_result.text,  # Generated customer-facing draft.

            # Record which order was actually used, if any.
            order_id_used=(
                order_context.order_id
                if order_context
                else None
            ),
            faq_ids_used=[
                faq.faq_id
                for faq in faq_context
            ],
            model=claude_result.model,                      # Preserve model information for visibility/debugging.
            input_tokens=claude_result.input_tokens,        # Preserve token usage for monitoring and cost awareness.
            output_tokens=claude_result.output_tokens,      # Preserve generated token usage as part of the result metadata.
        )
