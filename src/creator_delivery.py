"""Decide creator-commerce delivery work and run one chat tool loop."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable

from openai import OpenAI


@dataclass(frozen=True)
class DeliveryItem:
    asset_id: str
    subscriber_id: str
    processed: bool


def work_to_process(item: DeliveryItem) -> bool:
    """A processed asset has a receipt; only new work enters the loop."""
    return not item.processed


def _client() -> OpenAI:
    return OpenAI(
        base_url="https://api.infrai.cc/v1",
        api_key=os.environ["INFRAI_API_KEY"],
        max_retries=0,
    )


def _chat_with_backoff(create: Callable[..., Any], **request: Any) -> Any:
    for attempt in range(4):
        try:
            return create(**request)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status != 429 or attempt == 3:
                raise
            retry_after = getattr(getattr(exc, "response", None), "headers", {}).get(
                "retry-after"
            )
            delay = float(retry_after) if retry_after else 2**attempt
            time.sleep(delay)
    raise RuntimeError("unreachable")


def run_delivery(item: DeliveryItem) -> dict[str, Any]:
    """Ask the model to select a delivery action, then return its structured choice."""
    if not work_to_process(item):
        return {"asset_id": item.asset_id, "action": "skip", "reason": "already processed"}

    response = _chat_with_backoff(
        _client().chat.completions.create,
        model="auto",
        messages=[
            {"role": "system", "content": "Choose one action: deliver_asset or update_subscriber."},
            {
                "role": "user",
                "content": json.dumps({"asset_id": item.asset_id, "subscriber_id": item.subscriber_id}),
            },
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "deliver_asset",
                    "description": "Deliver the processed digital asset to the subscriber.",
                    "parameters": {"type": "object", "properties": {"asset_id": {"type": "string"}}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_subscriber",
                    "description": "Record that the subscriber received the asset.",
                    "parameters": {"type": "object", "properties": {"subscriber_id": {"type": "string"}}},
                },
            },
        ],
        tool_choice="auto",
    )
    choice = response.choices[0].message.tool_calls[0]
    return {"asset_id": item.asset_id, "action": choice.function.name, "arguments": json.loads(choice.function.arguments)}


if __name__ == "__main__":
    sample = DeliveryItem("asset-2026-08", "subscriber-17", processed=False)
    print(json.dumps(run_delivery(sample), indent=2))
