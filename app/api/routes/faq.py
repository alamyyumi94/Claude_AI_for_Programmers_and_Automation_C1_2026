from fastapi import APIRouter

from app.api.dependencies import FAQServiceDep
from app.schemas.faq import (
    FAQAskRequest,
    FAQAskResponse,
)
from app.schemas.usage import AIUsage

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
    result = await faq_service.ask(request.question)

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

    # Model/token details are exposed through `usage`; FAQAskResponse forbids extras.
    return FAQAskResponse(
        answer=result.answer,
        sources=result.sources,
        requires_human_review=result.requires_human_review,
        usage=usage,
    )
