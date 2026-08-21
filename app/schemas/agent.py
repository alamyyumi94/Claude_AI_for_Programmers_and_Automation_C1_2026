# These Pydantic models define the validated contract for agent requests, tool arguments and execution traces.
from enum import Enum
from typing import Any

# Pydantic validates untrusted/model-generated data before application code relies on it.
from pydantic import Field

# Schemas define validated request, response and internal contracts shared across layers.
from app.schemas.common import StrictModel
from app.schemas.ticket import TicketResponse
from app.schemas.usage import AIUsage


# `ToolName` gives this layer one explicit, testable responsibility.
class ToolName(str, Enum):
    GET_ORDER_STATUS = "get_order_status"
    SEARCH_FAQ = "search_faq"
    ESCALATE_TICKET = "escalate_ticket"


# `GetOrderStatusArgs` gives this layer one explicit, testable responsibility.
class GetOrderStatusArgs(StrictModel):
    order_id: str = Field(
        min_length=3,
        max_length=50,
    )


# `SearchFAQArgs` gives this layer one explicit, testable responsibility.
class SearchFAQArgs(StrictModel):
    query: str = Field(
        min_length=3,
        max_length=200,
    )


# `EscalateTicketArgs` gives this layer one explicit, testable responsibility.
class EscalateTicketArgs(StrictModel):
    reason: str = Field(
        min_length=5,
        max_length=300,
    )


# `AgentSupportRequest` gives this layer one explicit, testable responsibility.
class AgentSupportRequest(StrictModel):
    customer_id: str = Field(
        min_length=3,
        max_length=50,
    )
    order_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )
    message: str = Field(
        min_length=5,
        max_length=5000,
    )


# `ToolExecutionAudit` gives this layer one explicit, testable responsibility.
class ToolExecutionAudit(StrictModel):
    tool_name: str
    arguments: dict[
        str,
        Any,
    ] = Field(default_factory=dict)
    success: bool
    result_summary: str = Field(
        min_length=1,
        max_length=500,
    )


# `AgentSupportResponse` gives this layer one explicit, testable responsibility.
class AgentSupportResponse(StrictModel):
    ticket: TicketResponse
    final_response: str = Field(
        min_length=1,
        max_length=5000,
    )
    # Collect an application-visible audit trail of every model-requested tool.
    tool_calls: list[
        ToolExecutionAudit
    ] = Field(default_factory=list)
    iterations: int = Field(
        ge=1,
        le=4,
    )
    analysis_usage: AIUsage
    agent_usage: AIUsage
