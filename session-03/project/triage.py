"""ShopWise support assistant — project version v0.2.

    uv run python triage.py --limit 3            # three tickets, printed
    uv run python triage.py --csv triage.csv     # the whole inbox, plus a spreadsheet

v0.1 wrote prose. v0.2 first turns each ticket into data the code can use, then
writes the reply:

    ticket -> triage()  -> TriageResult   what kind of ticket, how urgent, needs a person?
           -> extract() -> TicketFacts    order numbers, product, days since delivery
           -> return_window(facts)        decided in code, not by the model
           -> draft_reply()               the reply, steered by the triage

v0.1 streamed each reply so a customer could watch it arrive. v0.2 is a batch job
over the inbox, so it waits for whole replies; streaming comes back in session 6,
where somebody is watching.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

import yaml
from google.genai import errors, types
from pydantic import ValidationError

from config import settings
from policy import return_window
from schemas import Ticket, TicketFacts, TriageResult
from utils import ModelReturnedNothing, ask_json, build_client, load_inbox

HERE = Path(__file__).resolve().parent
PROMPTS = yaml.safe_load((HERE / "prompts.yml").read_text(encoding="utf-8"))


def triage_system(with_examples: bool | None = None) -> str:
    """The triage prompt, plus the few-shot examples when they are switched on."""
    if with_examples is None:
        with_examples = settings.USE_FEW_SHOT
    prompt = PROMPTS["triage_prompt"]
    if with_examples:
        prompt += "\nExamples of how ShopWise labels the awkward cases:\n"
        for ex in PROMPTS["few_shot_examples"]:
            prompt += (f"\n<ticket>\nSubject: {ex['subject']}\n{ex['body']}\n</ticket>\n"
                       f"category: {ex['category']}\n")
    return prompt


def triage(client, ticket: Ticket):
    """Decide what the ticket is. Returns (TriageResult, usage)."""
    return ask_json(client, TriageResult, ticket.as_block(), triage_system())


def extract(client, ticket: Ticket):
    """Copy the facts out of the ticket. Returns (TicketFacts, usage).

    The ticket text goes in as validation context, so every order number the model
    returns is checked against what the customer actually wrote.
    """
    return ask_json(client, TicketFacts, ticket.as_block(), PROMPTS["facts_prompt"],
                    context={"ticket": f"{ticket.subject}\n{ticket.body}"})


def reply_system(today: date) -> str:
    """v0.1's system slot, unchanged: today's date first, then the rules, then examples."""
    examples = ""
    for ex in PROMPTS["examples"]:
        examples += (f"<example>\n<ticket>\n{ex['ticket'].strip()}\n</ticket>\n"
                     f"<reply>\n{ex['reply'].strip()}\n</reply>\n</example>\n")
    return (f"Today's date is {today.isoformat()}.\n\n"
            f"{PROMPTS['system_prompt'].strip()}\n\n## Examples\n{examples}")


def draft_reply(client, ticket: Ticket, result: TriageResult) -> str:
    """Write the reply, now that triage has decided what kind of ticket this is."""
    steer = (f"\nThis ticket was triaged as {result.category}, urgency {result.urgency}; "
             f"the customer sounds {result.sentiment}.")
    if result.needs_human:
        steer += ("\nA colleague must make the actual decision. Don't state or hint at an "
                  "outcome: say who will follow up and what happens next.")

    user_turn = PROMPTS["ticket_template"].format(
        id=ticket.id, subject=ticket.subject, body=ticket.body)
    response = client.models.generate_content(
        model=settings.MODEL,
        contents=user_turn,
        config=types.GenerateContentConfig(
            system_instruction=reply_system(date.today()) + steer,
            stop_sequences=["</reply>"],
            max_output_tokens=settings.MAX_OUTPUT_TOKENS,
        ),
    )
    return (response.text or "").split("<reply>", 1)[-1].strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage and answer the ShopWise inbox.")
    parser.add_argument("--limit", type=int, help="only the first N tickets")
    parser.add_argument("--csv", type=Path, help="also write one row per ticket to this file")
    parser.add_argument("--no-reply", action="store_true", help="skip drafting replies")
    args = parser.parse_args()

    if not settings.has_key:
        print("No GEMINI_API_KEY found. Put it in .env and try again.")
        return 1

    client = build_client()
    tickets = load_inbox()[: args.limit]
    rows = []

    print(f"{settings.APP_NAME} v{settings.VERSION} · {settings.MODEL} · {len(tickets)} ticket(s)\n")
    for ticket in tickets:
        try:
            result, _ = triage(client, ticket)
            facts, _ = extract(client, ticket)
            reply = "" if args.no_reply else draft_reply(client, ticket, result)
        except errors.ClientError as err:      # 4xx: our request is wrong; retrying won't help
            print(f"! {ticket.id}: client error {err.code} {err.status}\n")
            continue
        except errors.ServerError as err:      # 5xx, still failing after the SDK's retries
            print(f"! {ticket.id}: server error {err.code}, try this ticket again later\n")
            continue
        except (ModelReturnedNothing, ValidationError) as err:   # 200 OK, nothing usable
            print(f"! {ticket.id}: no usable answer ({str(err).splitlines()[0]})\n")
            continue

        window = return_window(facts)
        print("=" * 76)
        print(f"{ticket.id}  {result.category} | {result.urgency} | {result.sentiment}"
              f" | needs_human={result.needs_human}")
        print(f"  {result.summary}")
        print(f"  orders={facts.order_ids or '-'}  days={facts.days_since_delivery}"
              f"  return window: {window}")
        if reply:
            print("-" * 76)
            print(reply)
        print()

        rows.append({"id": ticket.id, **result.model_dump(),
                     "order_ids": " ".join(facts.order_ids),
                     "days_since_delivery": facts.days_since_delivery,
                     "return_window": window})

    if args.csv and rows:
        with args.csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
