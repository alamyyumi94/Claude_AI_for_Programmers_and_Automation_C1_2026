# FastAPI's APIRouter lets us group related API endpoints together.
from fastapi import APIRouter, HTTPException

# System prompt used specifically for the summarisation endpoint.
from app.prompts.summarise import (
    SUMMARISE_SYSTEM_PROMPT,
)

# Pydantic request/response models used by the AI endpoints.
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

# Shared usage schema used to expose Claude model/token information in responses.
from app.schemas.usage import AIUsage

# Database dependency used to obtain the application's MongoDB/database connection.
from app.database import get_database

# Repository responsible for retrieving trusted order data from the database.
from app.repositories.order_repository import (
    OrderRepository,
)

# Application service responsible for analysing customer-support tickets.
from app.services.analysis_service import (
    AnalysisService,
)

# Low-level Claude integration service responsible for communicating with Anthropic.
from app.services.claude_service import (
    ClaudeResponseError,
    ClaudeService,
)

# Service responsible for generating a customer-facing response using Claude.
from app.services.response_service import (
    ResponseService,
)

# Workflow service that coordinates order retrieval and AI response generation.
from app.services.generate_response_service import (
    GenerateResponseService,
)


# Create a router for AI-related endpoints.
# The "ai" tag groups these endpoints together in FastAPI's /docs interface.
router = APIRouter(tags=["ai"])


# ------------------------------------------------------------
# SUMMARISE ENDPOINT
# ------------------------------------------------------------

# Register a POST /summarise endpoint and declare the expected response shape.
@router.post(
    "/summarise",
    response_model=SummariseResponse,
)
async def summarise_text(
    # FastAPI/Pydantic validates the incoming JSON as a SummariseRequest.
    request: SummariseRequest,
) -> SummariseResponse:
    # Create a Claude client/service for this request.
    claude_service = ClaudeService()
    try:
        # Send the user's text to Claude using the summarisation system prompt.
        result = await claude_service.generate_text(
            user_message=request.text,
            # Budget covers claude-sonnet-5's thinking tokens plus the summary.
            max_tokens=1000,
            system=SUMMARISE_SYSTEM_PROMPT,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        # Always close the Claude client, even if the API call fails.
        await claude_service.close()

    # Convert the internal ClaudeTextResult into the API response model.
    return SummariseResponse(
        summary=result.text,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )


# ------------------------------------------------------------
# ANALYSE ENDPOINT
# ------------------------------------------------------------

# Register a POST /analyse endpoint for structured ticket analysis.
@router.post(
    "/analyse",
    response_model=AnalyseResponse,
)
async def analyse_ticket(
    # Validate the incoming request using the AnalyseRequest schema.
    request: AnalyseRequest,
) -> AnalyseResponse:
    # Create the reusable Claude integration service.
    claude_service = ClaudeService()

    # Create the ticket-analysis business service and inject ClaudeService into it.
    analyse_service = AnalysisService(
        claude_service
    )

    try:
        # Analyse the customer-support message and return structured output.
        result = await analyse_service.analyse(
            request.text
        )
    except ClaudeResponseError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        # Ensure network resources held by the Claude client are released.
        await claude_service.close()

    # Build the public API response from the structured analysis and usage metadata.
    return AnalyseResponse(
        # result.data is the validated structured TicketAnalysis object.
        analysis=result.data,

        # Expose model and token usage separately from the analysis itself.
        usage=AIUsage(
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ),
    )


# ------------------------------------------------------------
# GENERATE RESPONSE ENDPOINT
# ------------------------------------------------------------

# Register a POST /generate-response endpoint.
@router.post(
    "/generate-response",
    response_model=GenerateResponseResponse,
)
async def generate_response(
    # Validate the incoming customer message and optional order identifiers.
    request: GenerateResponseRequest,
) -> GenerateResponseResponse:
    # Obtain the application's database connection/dependency.
    # The route does not perform MongoDB queries directly.
    database = get_database()

    # Create the low-level Claude integration service.
    claude_service = ClaudeService()

    # Build the application workflow and inject all of its dependencies.
    service = GenerateResponseService(

        # ResponseService knows how to ask Claude to draft a customer response.
        response_service=ResponseService(
            claude_service
        ),

        # OrderRepository knows how to retrieve trusted order information.
        order_repository=OrderRepository(
            database
        ),
    )

    try:
        # Coordinate optional order lookup plus AI response generation.
        result = await service.generate(
            request
        )
    finally:
        # Close the per-request Claude client even when generation raises an error.
        await claude_service.close()

    # Convert the workflow result into the API's public response shape.
    return GenerateResponseResponse(

        # Customer-facing draft generated by Claude.
        draft_response=result.draft_response,

        # Tell the caller which trusted order record was actually used, if any.
        context_used=ResponseContextUsed(
            order_id=result.order_id_used,
        ),

        # Include Claude model and token usage for visibility and monitoring.
        usage=AIUsage(
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ),
    )
