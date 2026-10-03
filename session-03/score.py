"""Score the assistant against what we know is true.

    uv run python score.py                 # triage + extraction, shipped configuration
    uv run python score.py --compare       # three triage prompts, three runs each
    uv run python score.py --schemas       # a reasoning field first vs last (appendix C)

Two different kinds of number come out of this:

  triage accuracy   compared with the hand labels in tickets.yml. Some labels are
                    arguable, so this measures agreement with OUR convention.
  extraction        order numbers compared with a regex over the ticket text.
                    No judgment involved: an ID is in the text or it isn't.

It lives beside the notebook, not in project/: it measures the assistant, it is
not part of it.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pydantic import BaseModel, Field

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "project"))        # reuse the snapshot's code

import triage as project                                          # noqa: E402
from schemas import BANGLA_DIGITS, TicketCategory, TriageResult   # noqa: E402
from utils import ask_json, build_client, load_inbox              # noqa: E402

BARE = "You classify ShopWise customer support tickets."


def score_triage(client, tickets, system, schema=TriageResult):
    """Category accuracy against the hand labels. Returns (hits, misses, output tokens)."""
    hits, misses, out_tokens = 0, [], 0
    for ticket in tickets:
        try:
            result, usage = ask_json(client, schema, ticket.as_block(), system)
        except Exception as err:
            misses.append((ticket.id, ticket.category, f"FAILED {type(err).__name__}"))
            continue
        out_tokens += usage.candidates_token_count or 0
        if result.category == ticket.category:
            hits += 1
        else:
            misses.append((ticket.id, ticket.category, result.category))
    return hits, misses, out_tokens


def true_order_ids(ticket) -> set[str]:
    """Ground truth: every ORD-number written in the ticket, found by a regex."""
    text = f"{ticket.subject} {ticket.body}".translate(BANGLA_DIGITS)
    return {f"ORD-{n}" for n in re.findall(r"ORD-?(\d+)", text, re.I)}


def score_extraction(client, tickets):
    """Order-number extraction. Returns (found, missed, invented, rejected)."""
    found = missed = invented = rejected = 0
    for ticket in tickets:
        truth = true_order_ids(ticket)
        try:
            facts, _ = project.extract(client, ticket)
        except Exception:
            rejected += 1          # the validator refused it, even after one repair
            missed += len(truth)
            continue
        got = set(facts.order_ids)
        found += len(got & truth)
        missed += len(truth - got)
        invented += len(got - truth)
    return found, missed, invented, rejected


class ReasoningFirst(BaseModel):
    """Folklore: let the model reason before it decides."""
    reasoning: str = Field(description="Which two categories could fit, and which ShopWise "
                                       "convention settles it? Two sentences.")
    category: TicketCategory


class ReasoningLast(BaseModel):
    """The control: same field, declared after the decision, so it can't influence it."""
    category: TicketCategory
    reasoning: str = Field(description="Which two categories could fit, and which ShopWise "
                                       "convention settles it? Two sentences.")


class CategoryOnly(BaseModel):
    category: TicketCategory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--compare", action="store_true", help="three prompts, three runs each")
    parser.add_argument("--runs", type=int, default=3, help="runs per prompt for --compare")
    parser.add_argument("--schemas", action="store_true", help="reasoning first vs last")
    args = parser.parse_args()

    client = build_client()
    tickets = load_inbox()
    n = len(tickets)

    if args.compare:
        arms = [("bare instruction", BARE),
                ("conventions as rules", project.triage_system(with_examples=False)),
                ("rules + 3 examples", project.triage_system(with_examples=True))]
        for label, system in arms:
            scores, tokens = [], 0
            for _ in range(args.runs):
                hits, _, out_tokens = score_triage(client, tickets, system)
                scores.append(hits)
                tokens += out_tokens
            print(f"{label:22} {scores} out of {n}   (avg {tokens // args.runs} output tokens)")
        return 0

    if args.schemas:
        for label, schema in [("category only", CategoryOnly),
                              ("reasoning FIRST", ReasoningFirst),
                              ("reasoning LAST", ReasoningLast)]:
            hits, _, out_tokens = score_triage(client, tickets, BARE + "\n\n"
                                               + project.triage_system(False), schema)
            print(f"{label:16} {hits}/{n} correct · {out_tokens} output tokens")
        return 0

    hits, misses, out_tokens = score_triage(client, tickets, project.triage_system())
    print(f"triage: {hits}/{n} correct · {out_tokens} output tokens")
    for tid, truth, said in misses:
        print(f"  {tid}  labelled {truth:<17} model said {said}")

    found, missed, invented, rejected = score_extraction(client, tickets)
    print(f"\norder numbers: {found} found · {missed} missed · {invented} invented"
          f" · {rejected} ticket(s) rejected by the validator")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
