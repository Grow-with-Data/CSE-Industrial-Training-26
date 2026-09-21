"""Python-for-AI warm-up — the file we type together in session 1.

    uv run python warmup.py

This is every Python feature the rest of the course needs, and nothing else:
reading a file, dicts, f-strings, functions with type hints, a small class, and
JSON in and out — no model calls, on purpose. Section 2 of the notebook is the
same material with more explanation; this is it as a script, which is what every
session from S02 on actually ships.

It is also the scaffold for exercise 3 (Ticket loader), so keep it working.
"""

import json
from pathlib import Path

import yaml

# --- 1. Finding a file, the way that doesn't break on someone else's machine --
#
# `Path(__file__)` is THIS file. `.parent` is the folder it sits in. So the path
# below means "the data folder next door to my own folder" — it works no matter
# which directory you launched Python from, which "data/tickets.yml" does not.
#
# session-01/warmup.py  ->  repo root  ->  data/tickets.yml
TICKETS_PATH = Path(__file__).resolve().parent.parent / "data" / "tickets.yml"


# --- 2. A function, with type hints ------------------------------------------
#
# `-> list[dict]` is a promise to the reader (and to your editor) about what
# comes back. Python does not enforce it; humans and tools rely on it. From
# session 3 onward these hints stop being documentation and start being the
# thing that tells the model what shape to answer in — so get used to them now.
def load_tickets(path: Path = TICKETS_PATH) -> list[dict]:
    """Read the shared ticket fixture and return it as a list of dicts."""
    text = path.read_text(encoding="utf-8")   # encoding matters: TCK-004 is Bangla
    return yaml.safe_load(text)


# --- 3. A class, in five minutes ---------------------------------------------
#
# This is all the object-orientation the course uses. A class bundles some data
# with the things you can do to it. `__init__` runs when you create one; `self`
# is the instance being worked on.
class Ticket:
    def __init__(self, id: str, subject: str, body: str, category: str) -> None:
        self.id = id
        self.subject = subject
        self.body = body
        self.category = category

    # A method: a function that lives on the class and can see `self`.
    def is_shouting(self) -> bool:
        """True if the body is mostly capitals — our crude anger detector.

        Session 3 replaces this with the model's own judgement. Keep it in mind:
        this is the kind of rule an LLM makes unnecessary.
        """
        letters = [c for c in self.body if c.isalpha()]
        if not letters:
            return False
        capitals = [c for c in letters if c.isupper()]
        return len(capitals) / len(letters) > 0.7

    # __repr__ controls what you see when you print the object. Without it you
    # get something useless like <Ticket object at 0x104f2a390>.
    def __repr__(self) -> str:
        return f"Ticket({self.id}, {self.category})"


def main() -> None:
    tickets = load_tickets()

    # --- 4. Looping and f-strings --------------------------------------------
    #
    # An f-string lets you drop a value straight into text with {braces}.
    # `t["id"]` is dict access by key — a KeyError if the key is missing, which
    # is why the fixture's fields are documented at the top of tickets.yml.
    print(f"\nShopWise inbox — {len(tickets)} open tickets\n")
    for t in tickets:
        print(f"  [{t['id']}] {t['subject']}")

    # --- 5. Using the class --------------------------------------------------
    #
    # `**t` unpacks a dict into keyword arguments, so {"id": "TCK-001", ...}
    # becomes Ticket(id="TCK-001", ...). It only works because the dict's keys
    # match the parameter names — hence `received` and `from` are dropped here.
    objects = [
        Ticket(id=t["id"], subject=t["subject"], body=t["body"], category=t["category"])
        for t in tickets
    ]

    shouting = [t for t in objects if t.is_shouting()]
    print(f"\nTickets in ALL CAPS: {shouting}")

    # --- 6. JSON out, JSON in ------------------------------------------------
    #
    # Every API in this course speaks JSON. `json.dumps` turns a Python dict
    # into a string to send; `json.loads` turns a string you received back into
    # a dict. That round trip is the whole shape of talking to a model.
    first = tickets[0]
    as_text = json.dumps(first, ensure_ascii=False, indent=2)
    print(f"\nOne ticket, as a JSON string:\n{as_text}")

    back_to_dict = json.loads(as_text)
    print(f"\nParsed back — same subject? {back_to_dict['subject'] == first['subject']}")

    # --- Your turn: exercise 3 (⭐⭐ Ticket loader) ---------------------------
    #
    # A. Count how many tickets are in each category and print a small report.
    #    Start from an empty dict and use `counts.get(key, 0) + 1` — section 2.6.
    #    That exact pattern reappears in session 10 as how a graph updates state.
    #
    # B. Do the same for t["from"]: who writes in most?
    #
    # C. Then generalise A and B into ONE function, and call it from here:
    #
    #        def count_by(tickets: list[dict], field: str) -> dict[str, int]:
    #            ...
    #
    #    count_by(tickets, "category") and count_by(tickets, "from") both work.
    #    Passing the field NAME as an argument instead of hard-coding it is the
    #    difference between a script and a tool — and session 5 is entirely
    #    about writing tools.


# This guard means the file can be imported by the exercises notebook without
# running main(). `__name__` is "__main__" only when the file is run directly.
if __name__ == "__main__":
    main()
