from fastapi import APIRouter

from app.services.claude_service import ClaudeService
from app.services.claude_service import ClaudeTextResult

router = APIRouter(tags=["summarise"])


@router.post("/summarise", response_model=ClaudeTextResult)
async def summarise(input: str) -> ClaudeTextResult:

    claude_service = ClaudeService()
    result = await claude_service.generate_text(
        user_message=input,
        max_tokens=300,
        system="You are a helpful assistant that summarises text.",
    )
    return result
