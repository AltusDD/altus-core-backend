from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class OutboxMessage:
    topic: str
    aggregate_type: str
    aggregate_id: str
    payload: Mapping[str, Any]
    dedupe_key: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"
    attempt_count: int = 0
    last_error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def create_outbox_message(
    *,
    topic: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: Mapping[str, Any],
    dedupe_key: str,
) -> OutboxMessage:
    return OutboxMessage(
        topic=topic,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
        dedupe_key=dedupe_key,
    )


def build_outbox_record(message: OutboxMessage) -> dict[str, Any]:
    return {
        "message_id": message.message_id,
        "topic": message.topic,
        "aggregate_type": message.aggregate_type,
        "aggregate_id": message.aggregate_id,
        "payload_json": json.dumps(message.payload, sort_keys=True, separators=(",", ":")),
        "dedupe_key": message.dedupe_key,
        "status": message.status,
        "attempt_count": message.attempt_count,
        "last_error": message.last_error,
        "created_at": message.created_at,
    }
