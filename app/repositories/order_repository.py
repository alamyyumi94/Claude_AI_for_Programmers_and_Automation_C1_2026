from typing import Any

from app.schemas.order import OrderContext


# Projection is an allowlist of fields the repository returns to the app.
ORDER_CONTEXT_PROJECTION = {
    "_id": 0,
    "order_id": 1,
    "status": 1,
    "items": 1,
    "estimated_delivery": 1,
    "delivered_at": 1,
}


class OrderRepository:
    def __init__(
        self,
        database: Any,
    ) -> None:
        # Repositories own database access; ClaudeService does not.
        self.collection = database.orders

    async def get_order_for_customer(
        self,
        customer_id: str,
        order_id: str,
    ) -> OrderContext | None:
        return await self.collection.find_one(
            {"customer_id": customer_id, "order_id": order_id},
            projection=ORDER_CONTEXT_PROJECTION,
        )
        raise NotImplementedError
