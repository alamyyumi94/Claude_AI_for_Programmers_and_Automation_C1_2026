from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TicketCategories(str, Enum):
    DELIVERY = "delivery"
    RETURN = "return"
    REFUND = "refund"
    BILLING = "billing"
    PRODUCT = "product"
    ACCOUNT = "account"
    GENERAL = "general"
    OTHER = "other"

class TicketStatus(str, Enum):
    NEW = "new"
    ANALYSED = "analysed"
    PROCESSED = "processed"
    ESCALATED = "escalated"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    PROCESSING_FAILED = "processing_failed"
    CLOSED = "closed"

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Priority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TicketStatus(str, Enum):
    NEW = "new"
    ANALYZED = "analyzed"
    PROCESSED = "processed"
    ESCALATED = "escalated"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    PROCESSING = "processing"
    CLOSED = "closed"


class healthResponse(BaseModel):
    status: Literal["ok"]
