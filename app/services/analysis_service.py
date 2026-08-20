from app.prompts.ticket_analysis import (
    TICKET_ANALYSIS_SYSTEM_PROMPT,
)
from app.schemas.ai import TicketAnalysis
from app.services.claude_service import (
    ClaudeService,
    ClaudeStructuredResult,
)


class AnalysisService:
    def __init__(
        self,
        claude_service: ClaudeService,
    ) -> None:
        self.claude_service = claude_service

    async def analyse(
        self,
        message: str,
    ) -> ClaudeStructuredResult[TicketAnalysis]:
        user_prompt = (
            "Customer support message:\n"
            + message
        )

        return await self.claude_service.generate_structured(
            user_prompt,
            system=TICKET_ANALYSIS_SYSTEM_PROMPT,
            output_model=TicketAnalysis,
            max_tokens=500,
        )
