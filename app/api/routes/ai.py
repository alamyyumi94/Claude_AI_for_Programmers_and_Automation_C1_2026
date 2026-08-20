from fastapi import APIRouter, HTTPException

from app.repositories.order_repository import OrderRepository
from app.schemas.ai import (
    AnalyseRequest,
    AnalyseResponse,
    GenerateResponseRequest,
    GenerateResponseResponse,
    ResponseContextUsed,
    SummariseRequest,
    SummariseResponse,
    TicketAnalysis,
)
from app.schemas.order import OrderContext
from app.schemas.usage import AIUsage
from app.services.response_service import ResponseService
from app.services.claude_service import ClaudeResponseError, ClaudeService

from app.database import connect_to_database, get_database

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


@router.post("/ai/order")
async def order(order_id: str, customer_id: str):
    await connect_to_database()
    database = get_database()
    order_repository = OrderRepository(database=database)
    try:
        result = await order_repository.get_order_for_customer(
            order_id=order_id,
            customer_id=customer_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return result


@router.post("/ai/processOrder", response_model=GenerateResponseResponse)
async def process_order(input: GenerateResponseRequest) -> GenerateResponseResponse:
    await connect_to_database()
    database = get_database()
    order_repository = OrderRepository(database=database)

    document = await order_repository.get_order_for_customer(
        order_id=input.order_id,
        customer_id=input.customer_id,
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Order not found for customer.")

    claude_service = ClaudeService()
    response_service = ResponseService(claude_service=claude_service)
    try:
        result = await response_service.generate(
            customer_message=(
                f"{input.customer_message}\n\nOrder context (JSON):{document}"
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        await claude_service.close()

    return GenerateResponseResponse(
        draft_response=result.text,
        context_used=ResponseContextUsed(
            customer_id=input.customer_id,
            order_id=input.order_id,
            draft_response=result.text,
        ),
        usage=AIUsage(
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ),
    )
