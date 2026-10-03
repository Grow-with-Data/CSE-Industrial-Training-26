"""Plumbing every LLM program needs — project version v0.2.

Nothing in here knows about triage: a configured client, one function for a
structured call you can trust, and the inbox loader.
"""

from __future__ import annotations

import yaml
from google import genai
from google.genai import types
from pydantic import TypeAdapter, ValidationError

from config import settings
from schemas import Ticket


class ModelReturnedNothing(RuntimeError):
    """The call came back 200 OK with no usable text (cut off, blocked, ...)."""


def build_client() -> genai.Client:
    """One client for the program, with a timeout and the SDK's own retries.

    v0.1 retried 429s with a loop we wrote by hand. HttpRetryOptions does the same
    job (backoff, jitter, give up after N attempts) for every call, so that loop
    is gone. Only transient errors are retried: a 400 means our request is wrong,
    and sending it again won't fix it.
    """
    return genai.Client(
        http_options=types.HttpOptions(
            timeout=int(settings.REQUEST_TIMEOUT_S * 1000),       # milliseconds
            retry_options=types.HttpRetryOptions(
                attempts=settings.MAX_RETRIES,
                http_status_codes=[408, 429, 500, 502, 503, 504],
            ),
        ),
    )


def ask_json(client, schema, contents, system: str, context: dict | None = None):
    """One structured call. Returns (validated object, usage_metadata).

    Two things this does that `response.parsed` doesn't:
      - it validates the text ourselves, so `context` reaches the validators
        (TicketFacts needs the ticket text to check order numbers against);
      - when validation fails it asks once more, showing the model its answer
        and exactly what was wrong with it. Then it gives up and raises.
    """
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        response_schema=schema,
        max_output_tokens=settings.MAX_OUTPUT_TOKENS,
    )
    prompt = contents
    for attempt in (1, 2):
        response = client.models.generate_content(
            model=settings.MODEL, contents=prompt, config=config)
        if not response.text:
            reason = response.candidates[0].finish_reason if response.candidates else "unknown"
            raise ModelReturnedNothing(f"no text (finish_reason={reason})")
        try:
            return schema.model_validate_json(response.text, context=context), response.usage_metadata
        except ValidationError as err:
            if attempt == 2:
                raise
            problems = "; ".join(e["msg"] for e in err.errors())
            prompt = (f"{contents}\n\nYour previous answer was:\n{response.text}\n"
                      f"It was rejected because: {problems}\nReturn a corrected answer.")


def load_inbox() -> list[Ticket]:
    """Read tickets.yml and validate every ticket in one go."""
    raw = yaml.safe_load((settings.DATA_DIR / "tickets.yml").read_text(encoding="utf-8"))
    return TypeAdapter(list[Ticket]).validate_python(raw)
