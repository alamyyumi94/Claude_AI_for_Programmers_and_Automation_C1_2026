from fastapi import APIRouter, HTTPException

from app.api.dependencies import FAQServiceDep
from app.schemas.faq import (
    FAQAskRequest,
    FAQAskResponse,
)
from app.schemas.usage import AIUsage
from app.services.claude_service import ClaudeResponseError

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
    faq_service: FAQServiceDep,
) -> FAQAskResponse:
    try:
        result = await faq_service.ask(request.question)
    except ClaudeResponseError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    # If no Claude answer call happened, usage remains None.
    usage = None

    if result.model is not None:
        usage = AIUsage(
            model=result.model,
            input_tokens=result.input_tokens or 0,
            output_tokens=result.output_tokens or 0,
        )

    return FAQAskResponse(
        answer=result.answer,
        sources=result.sources,
        requires_human_review=result.requires_human_review,
        usage=usage,
    )
