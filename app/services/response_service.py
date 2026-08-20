from app.prompts.response_generation import (
    RESPONSE_GENERATION_SYSTEM_PROMPT,
)
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

    async def generate(
        self,
        customer_message: str,
    ) -> ClaudeTextResult:
        return await self.claude_service.generate_text(
            customer_message,
            system=RESPONSE_GENERATION_SYSTEM_PROMPT,
            max_tokens=300,
        )
