from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from app.repositories.order_repository import OrderRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.common import TicketStatus
from app.schemas.order import OrderContext
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketListResponse,
    TicketResponse,
)
from app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class TicketService:
    """Orchestrates the ticket pipeline: analyse, enrich, store.

    Services own the flow; repositories own storage and database access.

    Attributes:
        ticket_repository: Repository for ticket persistence operations.
        analysis_service: Service for AI-powered ticket analysis.
        order_repository: Optional repository for order lookups.
    """

    def __init__(
        self,
        ticket_repository: TicketRepository,
        analysis_service: AnalysisService,
        order_repository: OrderRepository | None = None,
    ) -> None:
        self._ticket_repository = ticket_repository
        self._analysis_service = analysis_service
        self._order_repository = order_repository

    async def create_ticket(self, request: TicketCreateRequest) -> TicketResponse:
        """Analyse an incoming message, store the ticket, then enrich it.

        Args:
            request: The ticket creation request containing customer and message data.

        Returns:
            The created and enriched ticket response.

        Raises:
            ClaudeResponseError: If the AI analysis fails.
        """
        # Analysis runs first because TicketResponse.analysis is required.
        # A failure here raises (ClaudeResponseError) and no ticket is stored.
        analysis = (await self._analysis_service.analyse(request.message)).data

        faq_query = [analysis.faq_query] if analysis.needs_faq_lookup and analysis.faq_query else []

        ticket = self._ticket_repository.create(
            {
                "customer_id": request.customer_id,
                "order_id": request.order_id,
                "message": request.message,
                "analysis": analysis,
                "faq_query": faq_query,
                "status": TicketStatus.ANALYZED,
            }
        )

        logger.info("Created ticket %s for customer %s", ticket.ticket_id, request.customer_id)
        return await self._enrich(ticket)

    def get_ticket(self, ticket_id: str) -> TicketResponse | None:
        """Retrieve a ticket by its ID.

        Args:
            ticket_id: The unique identifier of the ticket.

        Returns:
            The ticket if found, None otherwise.
        """
        return self._ticket_repository.get_by_id(ticket_id)

    def list_tickets(self, *, skip: int = 0, limit: int = 50) -> TicketListResponse:
        """List tickets with pagination.

        Args:
            skip: Number of tickets to skip (for pagination).
            limit: Maximum number of tickets to return.

        Returns:
            Paginated list of tickets with total count.
        """
        return TicketListResponse(
            items=self._ticket_repository.get_all(skip=skip, limit=limit),
            total=self._ticket_repository.count(),
            limit=limit,
            skip=skip,
        )

    def close_ticket(self, ticket_id: str) -> TicketResponse | None:
        """Close a ticket by setting its status to CLOSED.

        Args:
            ticket_id: The unique identifier of the ticket to close.

        Returns:
            The updated ticket if found, None otherwise.
        """
        ticket = self._ticket_repository.update(ticket_id, {"status": TicketStatus.CLOSED})
        if ticket:
            logger.info("Closed ticket %s", ticket_id)
        return ticket

    async def _enrich(self, ticket: TicketResponse) -> TicketResponse:
        """Attach order context if the analysis asked for it, then set status.

        Args:
            ticket: The ticket to enrich with additional context.

        Returns:
            The enriched ticket with updated status.
        """
        updates: dict[str, Any] = {}

        if ticket.analysis.needs_order_lookup:
            order_context = await self._safe_lookup_order(ticket)
            if order_context is None:
                # _safe_lookup_order returns None on failure and handles escalation internally
                # but we need to check if it was a "not found" vs "error" case
                return await self._handle_order_lookup(ticket)
            updates["order_context"] = order_context

        if ticket.analysis.needs_human_review:
            return self._escalate_to_human(
                ticket,
                escalation_reason=ticket.analysis.human_review_reason,
                additional_updates=updates,
            )

        updates["status"] = TicketStatus.PROCESSED
        logger.debug("Ticket %s processed successfully", ticket.ticket_id)
        return self._ticket_repository.update(ticket.ticket_id, updates)

    async def _handle_order_lookup(self, ticket: TicketResponse) -> TicketResponse:
        """Handle order lookup with proper error handling and escalation.

        Args:
            ticket: The ticket requiring order lookup.

        Returns:
            The updated ticket, potentially escalated to human review.
        """
        try:
            order_context = await self._lookup_order(
                customer_id=ticket.customer_id,
                order_id=ticket.order_id,
            )
        except (RuntimeError, ValidationError) as exc:
            logger.warning(
                "Order lookup failed for ticket %s: %s",
                ticket.ticket_id,
                exc,
            )
            return self._escalate_to_human(
                ticket,
                processing_error=f"Order lookup failed: {exc}",
            )

        if order_context is None:
            return self._escalate_to_human(
                ticket,
                escalation_reason="Order lookup required but no matching order found.",
            )

        return order_context

    async def _safe_lookup_order(self, ticket: TicketResponse) -> OrderContext | None:
        """Attempt order lookup, returning None on any failure.

        This is a convenience wrapper that suppresses exceptions for cases
        where we want to handle failures gracefully.

        Args:
            ticket: The ticket containing customer and order information.

        Returns:
            The order context if found, None otherwise.
        """
        try:
            return await self._lookup_order(
                customer_id=ticket.customer_id,
                order_id=ticket.order_id,
            )
        except (RuntimeError, ValidationError):
            return None

    async def _lookup_order(
        self,
        customer_id: str,
        order_id: str | None,
    ) -> OrderContext | None:
        """Look up order context for a customer.

        Args:
            customer_id: The customer's unique identifier.
            order_id: The order's unique identifier, if provided.

        Returns:
            The order context if found, None if order_id is None or order not found.

        Raises:
            RuntimeError: If order repository is not configured or document validation fails.
        """
        if order_id is None:
            return None

        if self._order_repository is None:
            raise RuntimeError("Order lookup requested but no order repository configured.")

        document = await self._order_repository.get_order_for_customer(
            customer_id=customer_id,
            order_id=order_id,
        )
        if document is None:
            return None

        # The repository returns a raw Mongo document, so validate it here.
        # Let ValidationError propagate - caller should handle it appropriately.
        return OrderContext.model_validate(document)

    def _escalate_to_human(
        self,
        ticket: TicketResponse,
        *,
        escalation_reason: str | None = None,
        processing_error: str | None = None,
        additional_updates: dict[str, Any] | None = None,
    ) -> TicketResponse:
        """Escalate a ticket to human review.

        Args:
            ticket: The ticket to escalate.
            escalation_reason: Business reason for escalation (e.g., policy decision).
            processing_error: Technical error that caused escalation.
            additional_updates: Any other fields to update on the ticket.

        Returns:
            The updated ticket with NEEDS_HUMAN_REVIEW status.
        """
        updates: dict[str, Any] = {**(additional_updates or {})}
        updates["status"] = TicketStatus.NEEDS_HUMAN_REVIEW

        if escalation_reason is not None:
            updates["escalation_reason"] = escalation_reason
        if processing_error is not None:
            updates["processing_error"] = processing_error

        logger.info(
            "Escalating ticket %s to human review: reason=%s, error=%s",
            ticket.ticket_id,
            escalation_reason,
            processing_error,
        )
        return self._ticket_repository.update(ticket.ticket_id, updates)
