import json
from typing import Any


def serialize_prompt_payload(
    payload: dict[str, Any],
) -> str:
    """
    This is a small support utility;
    This helper is for turning application data into a clean JSON string before inserting it into a prompt

    Args:
        payload: The prompt data to serialize.

    Returns:
        A JSON string representing the serialized prompt data.

    """
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )
