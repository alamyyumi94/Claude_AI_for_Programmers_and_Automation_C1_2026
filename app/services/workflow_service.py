from dataclasses import dataclass
from datetime import datetime, timezone

from app.repositories.faq_repository import FAQRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.common import TicketStatus
from app.schemas.faq import FAQSource
from app.schemas.order import OrderContext
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketResponse,
)
from app.schemas.usage import AIUsage
from app.schemas.workflow import (
    ProcessTicketRequest,
    WorkflowStep,
)
from app.services.analysis_service import AnalysisService
from app.services.response_service import ResponseService
from app.services.ticket_service import TicketService


# One result object represents the outcome of the entire workflow.
@dataclass(frozen=True)
class WorkflowProcessResult:
    ticket: TicketResponse
    executed_steps: list[WorkflowStep]
    analysis_usage: AIUsage
    response_usage: AIUsage


# This service does not replace the existing services/repositories.
# It coordinates them in an application-owned sequence.
class WorkflowService:
    def __init__(
        self,
        *,
        analysis_service: AnalysisService,
        response_service: ResponseService,
        ticket_service: TicketService,
        order_repository: OrderRepository,
        faq_repository: FAQRepository,
    ) -> None:
        # Dependencies are injected so this service does not create its own
        # Claude client or MongoDB connection.
        self.analysis_service = analysis_service
        self.response_service = response_service
        self.ticket_service = ticket_service
        self.order_repository = order_repository
        self.faq_repository = faq_repository

    async def process(
        self,
        request: ProcessTicketRequest,
    ) -> WorkflowProcessResult:
        executed_steps: list[WorkflowStep] = []

        # Claude only classifies the message; the application decides what happens next.
        analysis_result = await self.analysis_service.analyse(
            message=request.message,
        )
        analysis = analysis_result.data
        executed_steps.append(WorkflowStep.ANALYSIS)

        order_context: OrderContext | None = None

        # Skip the lookup entirely unless the analysis asked for it and the
        # request carries an order_id to scope the query with.
        if analysis.needs_order_lookup and request.order_id is not None:
            order_context = await self.order_repository.get_order_for_customer(
                customer_id=request.customer_id,
                order_id=request.order_id,
            )
            executed_steps.append(WorkflowStep.ORDER_LOOKUP)

        # A requested order that does not exist for this customer is not something
        # the draft response should guess about, so the ticket is escalated below.
        order_lookup_failed = (
            WorkflowStep.ORDER_LOOKUP in executed_steps
            and order_context is None
        )

        # FAQ retrieval runs before the ticket is stored so the stored record
        # holds every piece of trusted context this workflow gathered.
        faq_context: list[FAQSource] = []
        if analysis.needs_faq_lookup and analysis.faq_query:
            faq_context = await self.faq_repository.search(
                analysis.faq_query,
            )
            executed_steps.append(WorkflowStep.FAQ_LOOKUP)

        ticket = await self.ticket_service.create(
            TicketCreateRequest(
                customer_id=request.customer_id,
                order_id=request.order_id,
                message=request.message,
            ),
            analysis,
        )
        executed_steps.append(WorkflowStep.DATABASE_INSERT)

        # TicketService derives status from the analysis alone; a failed order
        # lookup is workflow state, so this service owns that escalation.
        status = ticket.status
        escalation_reason = (
            analysis.human_review_reason
            if analysis.needs_human_review
            else None
        )
        if order_lookup_failed:
            status = TicketStatus.NEEDS_HUMAN_REVIEW
            escalation_reason = (
                f"Order {request.order_id} was not found for this customer."
            )

        # Claude drafts a reply from the customer message plus the trusted
        # context the application retrieved; it never queries the database.
        draft = await self.response_service.generate_draft(
            request.message,
            order_context=order_context,
            faq_context=faq_context,
        )
        executed_steps.append(WorkflowStep.RESPONSE_GENERATION)

        # A ticket held for a human keeps that status even though a draft exists.
        if status != TicketStatus.NEEDS_HUMAN_REVIEW:
            status = TicketStatus.PROCESSED

        ticket = await self.ticket_service.save(
            ticket.model_copy(
                update={
                    "order_context": order_context,
                    "faq_context": faq_context,
                    "draft_response": draft.text,
                    "status": status,
                    "escalation_reason": escalation_reason,
                    "updated_at": datetime.now(timezone.utc),
                },
            ),
        )
        executed_steps.append(WorkflowStep.DATABASE_UPDATE)

        return WorkflowProcessResult(
            ticket=ticket,
            executed_steps=executed_steps,
            analysis_usage=AIUsage(
                model=analysis_result.model,
                input_tokens=analysis_result.input_tokens,
                output_tokens=analysis_result.output_tokens,
            ),
            response_usage=AIUsage(
                model=draft.model,
                input_tokens=draft.input_tokens,
                output_tokens=draft.output_tokens,
            ),
        )
