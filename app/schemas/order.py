from datetime import datetime
from enum import Enum
from unittest import case

from pydantic import Field
from app.schemas.common import StricModel

# Restrict order status to only the allowed values


class OrderStatus(str, Enum):
    DELAYED = "delayed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class OrderItem(StricModel):
    sku: str = Field(
        min_length=1, max_length=50, description="Stock Keeping Unit of the item"
    )
    name: str = Field(min_length=1, max_length=100, description="Name of the item")
    quantity: int = Field(ge=1, description="Quantity of the item ordered")


class OrderContext(StricModel):
    order_id: str = Field(
        min_length=1, max_length=50, description="Unique identifier for the order"
    )
    status: OrderStatus = Field(description="Current status of the order")
    items: list[OrderItem] = Field(
        min_items=1, description="List of items in the order"
    )
    estimated_delivery: datetime | None = None
    delivered_at: datetime | None = None
