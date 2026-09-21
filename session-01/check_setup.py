"""Session 1 setup checker — run this before anything else.

    uv run python check_setup.py

Every check prints PASS or FAIL with the exact thing to do about it. Nothing here
talks to the network or spends any quota, so run it as often as you like.

If you are reading this after the session: work top to bottom. A later check
failing is often a symptom of an earlier one, so fix the first FAIL and re-run
rather than trying to fix them all at once.
"""

import os
import sys
from pathlib import Path

# session-01/check_setup.py  ->  repo root
LABS = Path(__file__).resolve().parent.parent

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

results: list[tuple[str, str, str]] = []


def record(status: str, name: str, detail: str) -> None:
    results.append((status, name, detail))


# --- 1. Python version -------------------------------------------------------
# We need 3.12+. google-genai itself requires 3.10+, and the course uses modern
# type-hint syntax (`list[dict]`, `str | None`) that reads badly on older versions.
version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
if sys.version_info >= (3, 12):
    record(PASS, "Python version", f"{version}")
else:
    record(
        FAIL,
        "Python version",
        f"found {version}, need 3.12+. Install it, then re-run `uv sync` in the repo root.",
    )


# --- 2. Are we inside the labs virtual environment? --------------------------
# The classic first-session failure: packages installed into .venv, but the
# notebook or terminal running the system Python, so imports mysteriously fail.
in_venv = sys.prefix != sys.base_prefix
expected_venv = LABS / ".venv"
running_from = Path(sys.prefix).resolve()

if not in_venv:
    record(
        FAIL,
        "Virtual environment",
        "you are on the system Python. Run this as `uv run python check_setup.py` "
        "from the repo root, or activate .venv first.",
    )
elif running_from == expected_venv.resolve():
    record(PASS, "Virtual environment", f"{running_from}")
else:
    record(
        WARN,
        "Virtual environment",
        f"inside a venv, but not the repo's .venv ({running_from}). Usually harmless; "
        "if imports fail below, this is why.",
    )


# --- 3. The packages this course is built on ---------------------------------
# Import name on the left, install name on the right — they differ often enough
# to be worth showing (`import yaml` comes from the `pyyaml` package).
packages = [
    ("google.genai", "google-genai"),
    ("dotenv", "python-dotenv"),
    ("yaml", "pyyaml"),
    ("pydantic", "pydantic"),
    ("pydantic_settings", "pydantic-settings"),   # typed configuration, from session 3
    ("mermaid", "mermaid-py"),       # notebook diagrams, from session 1
    ("PIL", "pillow"),               # showing the image the model reads/writes
    ("langchain", "langchain"),      # not used until session 4, checked now
    ("langgraph", "langgraph"),      # not used until session 10, checked now
]

from importlib import import_module      # noqa: E402  (kept here, next to its use)
from importlib.metadata import version as pkg_version, PackageNotFoundError  # noqa: E402

missing: list[str] = []
for import_name, install_name in packages:
    try:
        import_module(import_name)
    except ImportError:
        missing.append(install_name)
        continue
    try:
        record(PASS, f"import {import_name}", pkg_version(install_name))
    except PackageNotFoundError:
        record(PASS, f"import {import_name}", "installed")

if missing:
    record(
        FAIL,
        "Missing packages",
        f"{', '.join(missing)} — run `uv sync` in the repo root.",
    )


# --- 4. The .env file and your key ------------------------------------------
# We check that a key EXISTS and looks the right shape. We never print it, and
# we do not call the API here — a bad key surfaces in the notebook instead.
env_path = LABS / ".env"
if not env_path.exists():
    record(
        FAIL,
        ".env file",
        f"not found at {env_path}. Run `cp .env.example .env` in the repo root, then paste your key.",
    )
else:
    record(PASS, ".env file", str(env_path))

    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
    except ImportError:
        pass  # already reported above

    key = os.getenv("GEMINI_API_KEY") or ""
    if not key:
        record(
            FAIL,
            "GEMINI_API_KEY",
            "empty. Get one free at https://aistudio.google.com/apikey and paste it "
            "after the `=` in .env (no quotes, no spaces).",
        )
    elif key.startswith("your") or key.endswith("here"):
        record(FAIL, "GEMINI_API_KEY", "still the placeholder text — paste your real key.")
    elif not key.startswith("AIza"):
        record(
            WARN,
            "GEMINI_API_KEY",
            f"set ({len(key)} chars) but doesn't start with 'AIza', which Google keys "
            "normally do. Check you didn't paste an OpenAI key here.",
        )
    else:
        record(PASS, "GEMINI_API_KEY", f"set, {len(key)} chars, starts with AIza")


# --- 5. The shared data file -------------------------------------------------
# data/ is ONE copy shared by all 20 sessions. Session folders read
# ../data/tickets.yml — they never keep their own copy.
tickets_path = LABS / "data" / "tickets.yml"
if not tickets_path.exists():
    record(
        FAIL,
        "data/tickets.yml",
        f"not found at {tickets_path}. Are you running from inside session-01/?",
    )
else:
    try:
        import yaml

        tickets = yaml.safe_load(tickets_path.read_text(encoding="utf-8"))
        record(PASS, "data/tickets.yml", f"{len(tickets)} tickets loaded")
    except ImportError:
        record(WARN, "data/tickets.yml", "found, but pyyaml is missing so it wasn't parsed")
    except Exception as exc:  # a broken YAML edit should say so, not traceback
        record(FAIL, "data/tickets.yml", f"found but could not be parsed: {exc}")

# The customer photo the notebook hands to the model in §7.3, and that the ⭐⭐⭐
# exercise reuses. Shared like tickets.yml — one copy in data/.
photo_path = LABS / "data" / "images" / "ticket-photo-headphones.jpg"
if photo_path.exists():
    record(PASS, "data/images/", f"{photo_path.name} ({photo_path.stat().st_size // 1024} KB)")
else:
    record(
        FAIL,
        "data/images/",
        f"not found at {photo_path}. Pull the latest — §7.3 of the notebook needs it.",
    )


# --- Report ------------------------------------------------------------------
print()
print("ShopWise — session 1 setup check")
print("=" * 62)

width = max(len(name) for _, name, _ in results)
icons = {PASS: "✓", FAIL: "✗", WARN: "!"}
for status, name, detail in results:
    print(f"  {icons[status]} {status:<4} {name:<{width}}  {detail}")

print("=" * 62)

failures = [r for r in results if r[0] == FAIL]
warnings = [r for r in results if r[0] == WARN]

if failures:
    print(f"\n{len(failures)} check(s) failed. Fix the first one, then run this again.")
    print("Still stuck? Raise your hand — this is what the setup lab is for.\n")
    sys.exit(1)

if warnings:
    print(f"\nAll required checks passed, with {len(warnings)} warning(s) above.\n")
else:
    print("\nEverything green. You're ready for session 2.\n")

sys.exit(0)
