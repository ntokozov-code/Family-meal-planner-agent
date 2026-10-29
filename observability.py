"""
observability.py - Structured JSON logging, PII sanitization, and OpenTelemetry distributed tracing.
"""
import re
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# OpenTelemetry distributed tracing framework integration
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

# Initialize OpenTelemetry Tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("family-meal-concierge-tracer")
trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("MealAgentObservability")

EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_REGEX = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'

def redact_pii(text: str) -> str:
    """Masks personally identifiable information (emails, phone numbers)."""
    if not isinstance(text, str):
        return text
    text = re.sub(EMAIL_REGEX, "[REDACTED_EMAIL]", text)
    text = re.sub(PHONE_REGEX, "[REDACTED_PHONE]", text)
    return text

def start_span(name: str):
    """Starts an OpenTelemetry distributed tracing span."""
    return tracer.start_as_current_span(name)

def log_event(
    event_type: str,
    trace_id: str,
    intent: Optional[str] = None,
    outcome: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Emits structured JSON logs containing trace context, intent, and outcomes."""
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
