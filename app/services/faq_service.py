from dataclasses import dataclass

from app.core.prompt_data import serialize_prompt_payload
from app.prompts.faq_answer import FAQ_ANSWER_SYSTEM_PROMPT
from app.repositories.faq_repository import FAQRepository
from app.services.claude_service import ClaudeService
from app.schemas.faq import (
    FAQAnswerDecision,
    FAQSource,
)

# Application-owned fallback used when approved evidence is unavailable.
NO_APPROVED_FAQ_ANSWER = (
    "I couldn't find approved FAQ "
    "information that answers this "
    "question. Please refer this "
    "request for human review."
)

@dataclass(frozen=True)
class FAQAnswerResult:
    answer: str
    sources: list[FAQSource]
    requires_human_review: bool
    model: str | None
    input_tokens: int | None
    output_tokens: int | None


class FAQService:
    def __init__(
        self,
        *,
        faq_repository: FAQRepository,
        claude_service: ClaudeService,
    ) -> None:
        self.faq_repository = faq_repository
        self.claude_service = claude_service

    async def ask(
        self,
        question: str,
    ) -> FAQAnswerResult:
        # Retrieve approved FAQ sources first.
        sources = await self.faq_repository.search(
            question,
            limit=3,
        )

        # No approved evidence -> application fallback, no Claude answer call.
        if not sources:
            return FAQAnswerResult(
                answer=NO_APPROVED_FAQ_ANSWER,
                sources=[],
                requires_human_review=True,
                model=None,
                input_tokens=None,
                output_tokens=None,
            )

        payload = {
            "customer_question": question,
            "approved_faq_sources": [
                source.model_dump(mode="json")
                for source in sources
            ],
        }

        result = await self.claude_service.generate_structured(
            serialize_prompt_payload(payload),
            system=FAQ_ANSWER_SYSTEM_PROMPT,
            output_model=FAQAnswerDecision,
            max_tokens=300,
        )

        return FAQAnswerResult(
            answer=result.data.answer,
            sources=sources,
            requires_human_review=(
                not result.data.supported_by_sources
            ),
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )
