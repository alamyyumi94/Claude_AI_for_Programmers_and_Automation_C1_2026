from typing import Literal

from pydantic import BaseModel


class healthResponse(BaseModel):
    status: Literal["ok"]
