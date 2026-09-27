"""ShopWise support replier — project version v0.1.

    uv run python reply.py                  # every ticket, streamed as it is written
    uv run python reply.py --limit 3        # just the first three
    uv run python reply.py --no-stream      # whole replies at once (for logs and CI)

What v0.1 is: a two-slot prompt read from prompts.yml, sent through one config
object, streamed back, with a hand-written retry for rate limits. That is the
whole assistant. Every later session adds a capability to this shape.

What v0.1 is NOT, named honestly so later sessions have something to fix:
  - free text only, so nothing downstream can sort or count it        -> S03
  - one provider, one SDK, spelled out on every line                  -> S04
  - facts only as good as the text pasted into the prompt             -> S08
  - guardrails are instructions, which is a soft boundary             -> S07

Importing this module does nothing. The client is created inside main(), so a
missing key is an error when you RUN it, not when something imports it.
"""

from __future__ import annotations

import argparse
import os
import time
from datetime import date
from pathlib import Path

import yaml
from dotenv import load_dotenv

import config

HERE = Path(__file__).resolve().parent
# session-02/project/ -> repo root . The fixture and the key live at the tree
# root: snapshots never keep their own copy of the data (ADR-0001).
LABS = HERE.parent.parent
TICKETS_PATH = LABS / "data" / "tickets.yml"
PROMPTS_PATH = HERE / "prompts.yml"

RETRY_WAITS = (2, 4, 8, 16)   # seconds; doubling, then give up


def load_prompts() -> dict:
    """Read prompts.yml: system_prompt, examples and ticket_template."""
    return yaml.safe_load(PROMPTS_PATH.read_text(encoding="utf-8"))


def load_tickets() -> list[dict]:
    """Read the shared support inbox."""
    return yaml.safe_load(TICKETS_PATH.read_text(encoding="utf-8"))


def build_system(prompts: dict, today: date) -> str:
    """Assemble the system slot: today's date, then the rules, then the examples.

    The date is written in by CODE. The model has no clock, so this is the only
    way it can know whether a 30-day window has passed. It goes FIRST: in the
    session 2 notebook (section 7.5) the same sentence was used 5/5 times at the
    start and only 3/5 at the end. It changes once a day, so it costs one prompt
    cache miss a day; everything after it is identical on every call.
    """
    examples = "\n".join(
        f"<example>\n<ticket>\n{ex['ticket'].strip()}\n</ticket>\n"
        f"<reply>\n{ex['reply'].strip()}\n</reply>\n</example>"
        for ex in prompts["examples"]
    )
    return (f"Today's date is {today.isoformat()}.\n\n"
            f"{prompts['system_prompt'].strip()}\n\n## Examples\n{examples}")


def build_user_turn(prompts: dict, ticket: dict) -> str:
    """Fill the user-turn template: the ticket as delimited data, the task last."""
    return prompts["ticket_template"].format(
        id=ticket["id"], subject=ticket["subject"], body=ticket["body"].strip())


def with_retry(call):
    """Run `call()`, waiting and retrying when the API says 429 (rate limit).

    Written by hand on purpose: session 3 replaces this with the SDK's
    HttpRetryOptions, and session 4's framework does it for you. You only know
    what they are hiding if you wrote it once.
    """
    from google.genai import errors

    for wait in (*RETRY_WAITS, None):
        try:
            return call()
        except errors.ClientError as err:
            if err.code != 429 or wait is None:
                raise
            print(f"  (rate limited — waiting {wait}s)", flush=True)
            time.sleep(wait)


def clean(text: str) -> str:
    """Drop the <reply> tag. The stop sequence already cut everything after it."""
    return text.split("<reply>", 1)[-1].strip()


def answer(client, system: str, user_turn: str, stream: bool) -> tuple[str, object]:
    """Send one ticket; return (reply text, usage_metadata)."""
    from google.genai import types

    cfg = types.GenerateContentConfig(
        system_instruction=system,
        stop_sequences=["</reply>"],       # nothing after the reply survives
        max_output_tokens=1024,            # a runaway reply is cut, not billed forever
    )
    history = [types.Content(role="user", parts=[types.Part(text=user_turn)])]

    if not stream:
        resp = with_retry(lambda: client.models.generate_content(
            model=config.MODEL, contents=history, config=cfg))
        return clean(resp.text or ""), resp.usage_metadata

    chunks = with_retry(lambda: client.models.generate_content_stream(
        model=config.MODEL, contents=history, config=cfg))
    text, printed, usage = "", 0, None
    for chunk in chunks:
        text += chunk.text or ""
        usage = chunk.usage_metadata or usage   # the full count arrives on the LAST chunk
        # The opening tag can arrive split across two chunks ("<re" + "ply>"), so
        # hold output back until it has fully arrived, then print what follows it.
        if "<reply>" in text:
            body = text.split("<reply>", 1)[1].lstrip("\n")
            print(body[printed:], end="", flush=True)
            printed = len(body)
    if printed == 0:          # the model skipped the tag: show the whole reply
        print(clean(text), end="")
    print()
    return clean(text), usage


def main() -> int:
    parser = argparse.ArgumentParser(description="Reply to the ShopWise inbox.")
    parser.add_argument("--limit", type=int, default=None,
                        help="only handle the first N tickets")
    parser.add_argument("--no-stream", action="store_true",
                        help="print each reply whole instead of streaming it")
    args = parser.parse_args()

    load_dotenv(LABS / ".env")
    if not os.getenv("GEMINI_API_KEY"):
        print("No GEMINI_API_KEY found. Put it in .env and try again.")
        return 1

    from google import genai

    client = genai.Client()
    prompts = load_prompts()
    system = build_system(prompts, date.today())
    tickets = load_tickets()[: args.limit] if args.limit else load_tickets()

    print(f"ShopWise assistant v0.1 — {len(tickets)} ticket(s) on {config.MODEL}\n")
    for ticket in tickets:
        print("=" * 72)
        print(f"{ticket['id']}  [{ticket['category']}]  {ticket['subject']}")
        print("-" * 72)
        try:
            reply, usage = answer(client, system, build_user_turn(prompts, ticket),
                                  stream=not args.no_stream)
            if args.no_stream:
                print(reply)
            print(f"\n  [in {usage.prompt_token_count} · out {usage.candidates_token_count}"
                  f" · total {usage.total_token_count} tokens]")
        except Exception as err:  # one bad ticket shouldn't lose the whole run
            print(f"  ! could not answer {ticket['id']}: {str(err)[:160]}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
