from app.core.prompt_data import (
    serialize_prompt_payload,
)
from app.prompts.response_generation import (
    RESPONSE_GENERATION_SYSTEM_PROMPT,
)
from app.schemas.order import OrderContext
from app.services.claude_service import (
    ClaudeService,
    ClaudeTextResult,
)


class ResponseService:
    def __init__(
        self,
        claude_service: ClaudeService,
    ) -> None:
        self.claude_service = claude_service

    async def generate_draft(
        self,
        customer_message: str,
        *,
        order_context: OrderContext | None = None,
    ) -> ClaudeTextResult:
        # Keep user input and trusted context as distinct fields.
        payload = {
            "customer_message": customer_message,
            "trusted_order_context": (
                order_context.model_dump(
                    mode="json"
                )
                if order_context
                else None
            ),
        }

        # Serialize the application-created structure before sending it to Claude.
        user_prompt = (
            "Customer request and application "
            "context:\n"
            + serialize_prompt_payload(
                payload
            )
        )

        # Claude drafts text; the application decides what context it receives.
        return await self.claude_service.generate_text(
            user_prompt,
            system=RESPONSE_GENERATION_SYSTEM_PROMPT,
            max_tokens=350,
        )
