from fastapi import APIRouter

from app.database import get_database
from app.repositories.faq_repository import (
    FAQRepository,
)
from app.schemas.faq import (
    FAQAskRequest,
    FAQAskResponse,
)
from app.schemas.usage import AIUsage
from app.services import faq_service
from app.services.claude_service import (
    ClaudeService,
)
from app.services.faq_service import (
    FAQService,
)

router = APIRouter(
    prefix="/faq",
    tags=["faq"],
)

@router.post(
    "/ask",
    response_model=FAQAskResponse,
)
async def ask_faq(
    request: FAQAskRequest,
) -> FAQAskResponse:
    claude_service = ClaudeService()

    # Compose the service from the Claude and MongoDB boundaries
    service = FAQService(
        faq_repository=FAQRepository(
            get_database()
        ),
        claude_service=claude_service,
    )

    try:
        result = await service.ask(
            request.question,
        )
    finally:
        await claude_service.close()

    usage = None

    if result.model is not None:
        usage = AIUsage(
            model=result.model,
            input_tokens=(
                result.input_tokens or 0
            ),
            output_tokens=(
                result.output_tokens or 0
            ),
        )


    return FAQAskResponse(
        answer=result.answer,
        sources=result.sources,
        requires_human_review=result.requires_human_review,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        usage=usage,
    )
