# AgentService runs a bounded Claude/tool loop while application code validates and executes each requested action.
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Core helpers provide cross-cutting infrastructure such as IDs, logging, prompt serialization or caching.
from app.core.prompt_data import (
    serialize_prompt_payload,
)
from app.prompts.agent import AGENT_SYSTEM_PROMPT
from app.repositories.faq_repository import FAQRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.agent import (
    AgentSupportRequest,
    ToolExecutionAudit,
)
from app.schemas.common import (
    Priority,
    TicketStatus,
)
from app.schemas.faq import FAQSource
from app.schemas.order import OrderContext
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketResponse,
)
from app.schemas.usage import AIUsage
from app.services.analysis_service import AnalysisService
from app.services.claude_service import (
    ClaudeResponseError,
    ClaudeService,
)
from app.services.ticket_service import TicketService
from app.tools.registry import ToolRegistry


MAX_TOOL_ROUNDS = 3


# A frozen dataclass is a simple immutable result object passed between application layers.
@dataclass(frozen=True)
# `AgentResult` gives this layer one explicit, testable responsibility.
class AgentResult:
    ticket: TicketResponse
    final_response: str
    # Collect an application-visible audit trail of every model-requested tool.
    tool_calls: list[
        ToolExecutionAudit
    ]
    iterations: int
    analysis_usage: AIUsage
    agent_usage: AIUsage


# AgentService controls the bounded reasoning/tool loop rather than giving Claude an unbounded autonomous process.
class AgentService:
    # Store injected dependencies so this object does not create hidden Claude/MongoDB collaborators.
    def __init__(
        self,
        *,
        claude_service: ClaudeService,
        analysis_service:
            AnalysisService,
        ticket_service:
            TicketService,
        order_repository:
            OrderRepository,
        faq_repository:
            FAQRepository,
    ) -> None:
        self.claude_service = (
            claude_service
        )
        self.analysis_service = (
            analysis_service
        )
        self.ticket_service = (
            ticket_service
        )
        self.order_repository = (
            order_repository
        )
        self.faq_repository = (
            faq_repository
        )

    # Keep `support()` focused on this layer's responsibility instead of mixing unrelated concerns.
    async def support(
        self,
        request: AgentSupportRequest,
    ) -> AgentResult:
        analysis_result = (
            await self.analysis_service
            .analyse(request.message)
        )

        ticket = (
            await self.ticket_service
            .create(
                TicketCreateRequest(
                    customer_id=(
                        request.customer_id
                    ),
                    order_id=(
                        request.order_id
                    ),
                    message=(
                        request.message
                    ),
                ),
                analysis_result.data,
            )
        )

        registry = ToolRegistry(
            order_repository=(
                self.order_repository
            ),
            faq_repository=(
                self.faq_repository
            ),
            ticket_service=(
                self.ticket_service
            ),
            customer_id=(
                request.customer_id
            ),
            allowed_order_id=(
                request.order_id
            ),
            ticket_id=ticket.ticket_id,
        )

        # Maintain the bounded conversation state sent back to Claude after each tool result.
        messages: list[
            dict[str, Any]
        ] = [
            {
                "role": "user",
                "content":
                    serialize_prompt_payload(
                        {
                            "order_id":
                                request.order_id,
                            "analysis":
                                analysis_result
                                .data
                                .model_dump(
                                    mode="json"
                                ),
                            "customer_message":
                                request.message,
                        }
                    ),
            }
        ]

        # Collect an application-visible audit trail of every model-requested tool.
        tool_calls: list[
            ToolExecutionAudit
        ] = []
        order_context: (
            OrderContext | None
        ) = None
        faq_by_id: dict[
            str,
            FAQSource,
        ] = {}

        total_input_tokens = 0
        total_output_tokens = 0
        model_name = (
            self.claude_service.model
        )
        iterations = 0
        final_response: str | None = None

        for _ in range(
            MAX_TOOL_ROUNDS
        ):
            response = (
                await self.claude_service
                .create_message(
                    # Maintain the bounded conversation state sent back to Claude after each tool result.
                    messages,
                    system=(
                        AGENT_SYSTEM_PROMPT
                    ),
                    tools=(
                        registry.definitions()
                    ),
                    max_tokens=600,
                )
            )

            iterations += 1
            model_name = response.model
            total_input_tokens += (
                response.usage.input_tokens
            )
            total_output_tokens += (
                response.usage.output_tokens
            )

            assistant_content = (
                self._assistant_content(
                    response.content
                )
            )

            # Maintain the bounded conversation state sent back to Claude after each tool result.
            messages.append(
                {
                    "role": "assistant",
                    "content":
                        assistant_content,
                }
            )

            tool_blocks = [
                block
                for block
                in response.content
                if block.type
                == "tool_use"
            ]

            if not tool_blocks:
                final_response = (
                    self._extract_text(
                        response.content
                    )
                )
                break

            tool_results = []

            for block in tool_blocks:
                execution = (
                    await registry.execute(
                        block.name,
                        block.input,
                    )
                )

                arguments = (
                    dict(block.input)
                    if isinstance(
                        block.input,
                        dict,
                    )
                    else {
                        "raw":
                            str(block.input)
                    }
                )

                # Collect an application-visible audit trail of every model-requested tool.
                tool_calls.append(
                    ToolExecutionAudit(
                        tool_name=(
                            block.name
                        ),
                        arguments=arguments,
                        success=(
                            not execution.is_error
                        ),
                        result_summary=(
                            execution.summary
                        ),
                    )
                )

                if (
                    execution.order_context
                    is not None
                ):
                    order_context = (
                        execution.order_context
                    )

                if (
                    execution.faq_context
                    is not None
                ):
                    for faq in (
                        execution.faq_context
                    ):
                        faq_by_id[
                            faq.faq_id
                        ] = faq

                tool_results.append(
                    {
                        "type":
                            "tool_result",
                        "tool_use_id":
                            block.id,
                        "content":
                            execution
                            .content,
                        "is_error":
                            execution
                            .is_error,
                    }
                )

            # Maintain the bounded conversation state sent back to Claude after each tool result.
            messages.append(
                {
                    "role": "user",
                    "content":
                        tool_results,
                }
            )

        if final_response is None:
            response = (
                await self.claude_service
                .create_message(
                    # Maintain the bounded conversation state sent back to Claude after each tool result.
                    messages,
                    system=(
                        AGENT_SYSTEM_PROMPT
                    ),
                    max_tokens=600,
                )
            )
            iterations += 1
            model_name = response.model
            total_input_tokens += (
                response.usage.input_tokens
            )
            total_output_tokens += (
                response.usage.output_tokens
            )
            final_response = (
                self._extract_text(
                    response.content
                )
            )

        if not final_response:
            # Fail explicitly rather than allowing an invalid/unauthorized state to continue silently.
            raise ClaudeResponseError(
                "Agent returned no "
                "customer-facing response."
            )

        current_ticket = (
            await self.ticket_service.get(ticket.ticket_id)
        )

        if current_ticket is None:
            # Fail explicitly rather than allowing an invalid/unauthorized state to continue silently.
            raise RuntimeError(
                "Agent ticket missing."
            )

        faq_context = list(
            faq_by_id.values()
        )[:3]

        if (
            current_ticket.status
            == TicketStatus.ESCALATED
        ):
            # Translate accumulated review requirements into an application-owned final ticket status.
            final_status = (
                TicketStatus.ESCALATED
            )
        else:
            needs_review = (
                current_ticket.analysis.needs_human_review or 
                current_ticket.analysis.priority == Priority.URGENT
            )

            if (
                current_ticket.analysis.needs_order_lookup
                and order_context is None
            ):
                needs_review = True

            if (
                current_ticket.analysis.needs_faq_lookup
                and not faq_context
            ):
                needs_review = True

            # Translate accumulated review requirements into an application-owned final ticket status.
            final_status = (
                TicketStatus.NEEDS_HUMAN_REVIEW
                if needs_review
                else TicketStatus.PROCESSED
            )

        updated_ticket = (
            TicketResponse.model_validate(
                {
                    **current_ticket
                    .model_dump(
                        mode="python"
                    ),
                    "order_context":
                        order_context,
                    "faq_context":
                        faq_context,
                    "draft_response":
                        final_response,
                    "status":
                        final_status,
                    "updated_at":
                        datetime.now(
                            timezone.utc
                        ),
                }
            )
        )

        updated_ticket = (
            await self.ticket_service.save(updated_ticket)
        )

        return AgentResult(
            ticket=updated_ticket,
            final_response=final_response,
            # Collect an application-visible audit trail of every model-requested tool.
            tool_calls=tool_calls,
            iterations=iterations,
            analysis_usage=AIUsage(
                model=(
                    analysis_result.model
                ),
                input_tokens=(
                    analysis_result
                    .input_tokens
                ),
                output_tokens=(
                    analysis_result
                    .output_tokens
                ),
            ),
            agent_usage=AIUsage(
                model=model_name,
                input_tokens=(
                    total_input_tokens
                ),
                output_tokens=(
                    total_output_tokens
                ),
            ),
        )

    # This decorator attaches framework/metadata behaviour without changing the responsibility of the function/class below.
    @staticmethod
    # Keep `_extract_text()` focused on this layer's responsibility instead of mixing unrelated concerns.
    def _extract_text(
        blocks: list[Any],
    ) -> str:
        return "\n".join(
            block.text
            for block in blocks
            if block.type == "text"
        ).strip()

    # This decorator attaches framework/metadata behaviour without changing the responsibility of the function/class below.
    @staticmethod
    # Keep `_assistant_content()` focused on this layer's responsibility instead of mixing unrelated concerns.
    def _assistant_content(
        blocks: list[Any],
    ) -> list[dict[str, Any]]:
        content: list[
            dict[str, Any]
        ] = []

        for block in blocks:
            if block.type == "text":
                content.append(
                    {
                        "type": "text",
                        "text": block.text,
                    }
                )
            elif (
                block.type
                == "tool_use"
            ):
                content.append(
                    {
                        "type":
                            "tool_use",
                        "id": block.id,
                        "name":
                            block.name,
                        "input":
                            block.input,
                    }
                )

        return content
