from pydantic import Field

from app.schemas.common import StricModel


class AIUsage(StricModel):
    model: str = Field(min_length=1, max_length=100)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
