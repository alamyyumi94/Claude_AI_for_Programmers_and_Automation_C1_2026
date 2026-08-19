from fastapi import APIRouter, HTTPException

from app.schemas.ai import SummariseResponse, SummariseRequest
from app.services.claude_service import ClaudeService

from app.prompts.summarise import SUMMARISE_SYSTEM_PROMPT


router = APIRouter(tags=["summarise"])


@router.post("/ai/summarise", response_model=SummariseResponse)
async def summarise(input: SummariseRequest) -> SummariseResponse:
    claude_service = ClaudeService()
    try:
        result = await claude_service.generate_text(
            user_message=input.text,
            max_tokens=300,
            system=SUMMARISE_SYSTEM_PROMPT,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        await claude_service.close()
    return SummariseResponse(
        summary=result.text,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
