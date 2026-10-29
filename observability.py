"""
observability.py - Structured logging, distributed tracing, and PII redaction.
"""
import re
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("MealAgentObservability")

EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_REGEX = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'

def redact_pii(text: str) -> str:
    """Masks personally identifiable information (PII) like emails and phone numbers."""
    if not isinstance(text, str):
        return text
    text = re.sub(EMAIL_REGEX, "[REDACTED_EMAIL]", text)
    text = re.sub(PHONE_REGEX, "[REDACTED_PHONE]", text)
    return text

def create_trace_id() -> str:
    """Generates a distributed trace identifier for request tracing."""
    return str(uuid.uuid4())

def log_event(
    event_type: str,
    trace_id: str,
    intent: Optional[str] = None,
    outcome: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Emits structured JSON logs containing trace context, intent, and outcomes with PII protection."""
    clean_meta = {}
    if metadata:
        for k, v in metadata.items():
            clean_meta[k] = redact_pii(str(v)) if isinstance(v, str) else v

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "event_type": event_type,
        "intent": redact_pii(intent) if intent else "unknown",
        "outcome": redact_pii(outcome) if outcome else "in_progress",
        "metadata": clean_meta
    }
    logger.info(json.dumps(record))
