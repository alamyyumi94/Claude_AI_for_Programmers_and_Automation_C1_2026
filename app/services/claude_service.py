import json
from dataclasses import dataclass
from typing import Generic, TypeVar

from anthropic import AsyncAnthropic

from app.config import get_settings

from pydantic import BaseModel, ValidationError


class ClaudeConfigurationError(RuntimeError):
    pass

class ClaudeResponseError(RuntimeError):
    pass


ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(frozen=True)
class ClaudeTextResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class ClaudeStructuredResult(Generic[ModelT]):
    data: ModelT
    model: str
    input_tokens: int
    output_tokens: int


class ClaudeService:
    def __init__(self) -> None:
        self.settings = get_settings()
        if self.settings.anthropic_api_key is None:
            raise ClaudeConfigurationError("Claude API key is not configured.")
        if self.settings.claude_model is None:
            raise ClaudeConfigurationError("Claude model is not configured.")
        self.model = self.settings.claude_model
        self.client = AsyncAnthropic(
            api_key=self.settings.anthropic_api_key.get_secret_value().strip(),
            timeout=self.settings.claude_timeout_seconds,
            max_retries=self.settings.claude_max_retries,
        )

    async def generate_text(
        self,
        user_message: str,
        *,
        max_tokens: int = 300,
        system: str | None = None,
    ) -> ClaudeTextResult:
        request = {
            "model": self.settings.claude_model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
        }

        if system:
            request["system"] = system

        message = await self.client.messages.create(**request)

        text_parts = [block.text for block in message.content if block.type == "text"]

        text = "\n".join(text_parts).strip()

        return ClaudeTextResult(
            text=text,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )

    async def generate_structured(
        self,
        user_message: str,
        *,
        schema: type[ModelT],
        max_tokens: int = 600,
        system: str | None = None,
    ) -> ClaudeStructuredResult[ModelT]:
        result = await self.generate_text(
            user_message=user_message,
            max_tokens=max_tokens,
            system=system,
        )

        payload = _extract_json_object(result.text)

        try:
            data = schema.model_validate(payload)
        except ValidationError as e:
            raise ClaudeResponseError(
                f"Claude returned JSON that does not match {schema.__name__}: {e}"
            ) from e

        return ClaudeStructuredResult(
            data=data,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )

    async def close(self) -> None:
        await self.client.close()


def _extract_json_object(text: str) -> dict:
    """Parse the first JSON object in a Claude reply, tolerating code fences."""
    candidate = text.strip()

    if candidate.startswith("```"):
        candidate = candidate.split("```")[1]
        if candidate.lstrip().lower().startswith("json"):
            candidate = candidate.lstrip()[4:]
        candidate = candidate.strip()

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ClaudeResponseError("Claude did not return a JSON object.")

    try:
        payload = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError as e:
        raise ClaudeResponseError(f"Claude returned invalid JSON: {e}") from e

    if not isinstance(payload, dict):
        raise ClaudeResponseError("Claude returned JSON that is not an object.")

    return payload
