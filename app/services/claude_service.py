from dataclasses import dataclass
from functools import lru_cache

from anthropic import AsyncAnthropic

from app.config import get_settings


class ClaudeConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ClaudeTextResult:
    text: str
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
            max_tokens: max_tokens,
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

        text_parts = [block.text for block in message.context if block.type == "text"]

        text = "\n".join(text_parts).strip()

        return ClaudeTextResult(
            text=text,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )

    async def close(self) -> None:
        await self.client.close()
