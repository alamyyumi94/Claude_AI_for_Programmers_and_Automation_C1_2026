import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from app.repositories.faq_repository import (
    FAQRepository,
)
from app.repositories.order_repository import (
    OrderRepository,
)
from app.schemas.agent import (
    EscalateTicketArgs,
    GetOrderStatusArgs,
    SearchFAQArgs,
    ToolName,
)
from app.schemas.common import TicketStatus
from app.schemas.faq import FAQSource
from app.schemas.order import OrderContext
from app.schemas.ticket import TicketResponse
from app.services.ticket_service import (
    TicketService,
)


@dataclass(frozen=True)
class ToolExecutionResult:
    content: str
    is_error: bool
    summary: str
    order_context: (
        OrderContext | None
    ) = None
    faq_context: (
        list[FAQSource] | None
    ) = None


class ToolRegistry:
    def __init__(
        self,
        *,
        order_repository:
            OrderRepository,
        faq_repository:
            FAQRepository,
        ticket_service:
            TicketService,
        customer_id: str,
        allowed_order_id:
            str | None,
        ticket_id: str,
    ) -> None:
        self.order_repository = (
            order_repository
        )
        self.faq_repository = (
            faq_repository
        )
        self.ticket_service = (
            ticket_service
        )
        self.customer_id = customer_id
        self.allowed_order_id = (
            allowed_order_id
        )
        self.ticket_id = ticket_id

    def definitions(
        self,
    ) -> list[dict[str, Any]]:
        return [
            {
                "name": (
                    ToolName
                    .GET_ORDER_STATUS
                    .value
                ),
                "description": (
                    "Retrieve order status "
                    "for the order supplied "
                    "with the current support "
                    "request."
                ),
                "input_schema": (
                    GetOrderStatusArgs
                    .model_json_schema()
                ),
            },
            {
                "name": (
                    ToolName.SEARCH_FAQ
                    .value
                ),
                "description": (
                    "Search approved FAQ "
                    "knowledge for support "
                    "policy or guidance."
                ),
                "input_schema": (
                    SearchFAQArgs
                    .model_json_schema()
                ),
            },
            {
                "name": (
                    ToolName
                    .ESCALATE_TICKET
                    .value
                ),
                "description": (
                    "Escalate the current "
                    "support ticket for "
                    "human handling."
                ),
                "input_schema": (
                    EscalateTicketArgs
                    .model_json_schema()
                ),
            },
        ]

    async def execute(
        self,
        tool_name: str,
        raw_input: Any,
    ) -> ToolExecutionResult:
        allowed = {
            item.value
            for item in ToolName
        }

        if tool_name not in allowed:
            return ToolExecutionResult(
                content=json.dumps(
                    {
                        "error":
                            "Tool is not "
                            "allowlisted."
                    }
                ),
                is_error=True,
                summary=(
                    "Blocked non-"
                    "allowlisted tool."
                ),
            )

        if (
            tool_name
            == ToolName
            .GET_ORDER_STATUS
            .value
        ):
            return (
                await self
                ._get_order_status(
                    raw_input
                )
            )

        if (
            tool_name
            == ToolName
            .SEARCH_FAQ
            .value
        ):
            return (
                await self._search_faq(
                    raw_input
                )
            )

        return (
            await self._escalate_ticket(
                raw_input
            )
        )

    async def _get_order_status(
        self,
        raw_input: Any,
    ) -> ToolExecutionResult:
        try:
            args = (
                GetOrderStatusArgs
                .model_validate(
                    raw_input
                )
            )
        except ValidationError:
            return (
                self._invalid_arguments(
                    ToolName
                    .GET_ORDER_STATUS
                )
            )

        if self.allowed_order_id is None:
            return ToolExecutionResult(
                content=json.dumps(
                    {
                        "error":
                            "No order ID was "
                            "supplied."
                    }
                ),
                is_error=True,
                summary=(
                    "Order lookup blocked: "
                    "no request order ID."
                ),
            )

        if (
            args.order_id
            != self.allowed_order_id
        ):
            return ToolExecutionResult(
                content=json.dumps(
                    {
                        "error":
                            "Order ID not "
                            "permitted for this "
                            "request."
                    }
                ),
                is_error=True,
                summary=(
                    "Blocked different "
                    "order ID."
                ),
            )

        order = (
            await self.order_repository
            .get_order_for_customer(
                self.customer_id,
                args.order_id,
            )
        )

        if order is None:
            return ToolExecutionResult(
                content=json.dumps(
                    {
                        "found": False,
                    }
                ),
                is_error=False,
                summary=(
                    "No authorized order "
                    "was found."
                ),
            )

        return ToolExecutionResult(
            content=json.dumps(
                {
                    "found": True,
                    "order":
                        order.model_dump(
                            mode="json"
                        ),
                }
            ),
            is_error=False,
            summary=(
                f"Verified order "
                f"{order.order_id} "
                f"with status "
                f"{order.status.value}."
            ),
            order_context=order,
        )

    async def _search_faq(
        self,
        raw_input: Any,
    ) -> ToolExecutionResult:
        try:
            args = (
                SearchFAQArgs
                .model_validate(
                    raw_input
                )
            )
        except ValidationError:
            return (
                self._invalid_arguments(
                    ToolName.SEARCH_FAQ
                )
            )

        results = (
            await self.faq_repository
            .search(
                args.query,
                limit=3,
            )
        )

        return ToolExecutionResult(
            content=json.dumps(
                {
                    "matches": [
                        item.model_dump(
                            mode="json"
                        )
                        for item
                        in results
                    ]
                }
            ),
            is_error=False,
            summary=(
                "FAQ search returned "
                f"{len(results)} "
                "approved record(s)."
            ),
            faq_context=results,
        )

    async def _escalate_ticket(
        self,
        raw_input: Any,
    ) -> ToolExecutionResult:
        try:
            args = (
                EscalateTicketArgs
                .model_validate(
                    raw_input
                )
            )
        except ValidationError:
            return (
                self._invalid_arguments(
                    ToolName
                    .ESCALATE_TICKET
                )
            )

        ticket = (
            await self.ticket_service
            .get(self.ticket_id)
        )

        if ticket is None:
            return ToolExecutionResult(
                content=json.dumps(
                    {
                        "error":
                            "Current ticket "
                            "not found."
                    }
                ),
                is_error=True,
                summary=(
                    "Escalation failed: "
                    "ticket missing."
                ),
            )

        updated = (
            TicketResponse.model_validate(
                {
                    **ticket.model_dump(
                        mode="python"
                    ),
                    "status":
                        TicketStatus
                        .ESCALATED,
                    "escalation_reason":
                        args.reason,
                    "updated_at":
                        datetime.now(
                            timezone.utc
                        ),
                }
            )
        )

        await self.ticket_service.save(
            updated
        )

        return ToolExecutionResult(
            content=json.dumps(
                {
                    "success": True,
                    "ticket_id":
                        ticket.ticket_id,
                    "status":
                        TicketStatus
                        .ESCALATED.value,
                }
            ),
            is_error=False,
            summary=(
                "Current ticket "
                "escalated."
            ),
        )

    @staticmethod
    def _invalid_arguments(
        tool_name: ToolName,
    ) -> ToolExecutionResult:
        return ToolExecutionResult(
            content=json.dumps(
                {
                    "error":
                        "Tool arguments "
                        "failed validation."
                }
            ),
            is_error=True,
            summary=(
                "Invalid arguments "
                f"blocked for "
                f"{tool_name.value}."
            ),
        )
