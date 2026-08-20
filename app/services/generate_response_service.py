# dataclass gives us a simple immutable result object for returning generated response data.
from dataclasses import dataclass

# Repository responsible for retrieving order data from the application's data source.
from app.repositories.order_repository import (
    OrderRepository,
)

# Pydantic request model describing the input needed to generate a customer response.
from app.schemas.ai import GenerateResponseRequest

# Service responsible for asking Claude to generate the actual draft response.
from app.services.response_service import (
    ResponseService,
)


@dataclass(frozen=True)
class GenerateResponseResult:
    # Final draft generated for the customer.
    draft_response: str

    # Order ID actually used as context, or None if no order was found/used.
    order_id_used: str | None

    # Claude model that produced the response.
    model: str

    # Number of tokens Claude processed as input.
    input_tokens: int

    # Number of tokens Claude generated as output.
    output_tokens: int


class GenerateResponseService:
    # This service coordinates order lookup and AI response generation.
    def __init__(
        self,
        *,
        response_service: ResponseService,
        order_repository: OrderRepository,
    ) -> None:
        # Store the AI response-generation dependency.
        self.response_service = response_service

        # Store the repository used to retrieve trusted order data.
        self.order_repository = order_repository

    async def generate(
        self,
        request: GenerateResponseRequest,
    ) -> GenerateResponseResult:
        # Start with no order context because order information is optional.
        order_context = None

        # Only attempt an order lookup when both customer_id and order_id were supplied.
        if (
            request.order_id
            and request.customer_id
        ):
            # Retrieve the specific order while also ensuring it belongs to the given customer.
            order_context = (
                await self.order_repository
                .get_order_for_customer(
                    request.customer_id,
                    request.order_id,
                )
            )

        # Ask the response service to generate the draft using the customer message
        # plus trusted order data retrieved by our application, if available.
        claude_result = (
            await self.response_service
            .generate_draft(
                request.customer_message,
                order_context=order_context,
            )
        )

        # Convert the Claude/service result into the result shape expected by the API layer.
        return GenerateResponseResult(
            # Generated customer-facing draft.
            draft_response=claude_result.text,

            # Record which order was actually used, if any.
            order_id_used=(
                order_context.order_id
                if order_context
                else None
            ),

            # Preserve model information for visibility/debugging.
            model=claude_result.model,

            # Preserve token usage for monitoring and cost awareness.
            input_tokens=(
                claude_result.input_tokens
            ),

            # Preserve generated token usage as part of the result metadata.
            output_tokens=(
                claude_result.output_tokens
            ),
        )
