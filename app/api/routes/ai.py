from fastapi import APIRouter, HTTPException

from app.schemas.ai import (
    AnalyseRequest,
    AnalyseResponse,
    SummariseRequest,
    SummariseResponse,
    TicketAnalysis,
)
from app.schemas.usage import AIUsage
from app.services.claude_service import ClaudeResponseError, ClaudeService

from app.prompts.analyse import ANALYSE_SYSTEM_PROMPT
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


@router.post("/ai/analyse", response_model=AnalyseResponse)
async def analyse(input: AnalyseRequest) -> AnalyseResponse:
    claude_service = ClaudeService()
    try:
        result = await claude_service.generate_structured(
            user_message=input.text,
            schema=TicketAnalysis,
            max_tokens=600,
            system=ANALYSE_SYSTEM_PROMPT,
        )
    except ClaudeResponseError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        await claude_service.close()

    return AnalyseResponse(
        analysis=result.data,
        usage=AIUsage(
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ),
    )
