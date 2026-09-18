# AI/LLM Application Builder — student workspace

**CSE Industrial Training 2026 · Grow with Data**

Everything you build in this course lives here. One project, **ShopWise** (an e-commerce
customer-support assistant), grown across 20 sessions.

Sessions are published here as they are delivered, so expect this repo to grow week by week.

## Setup (once)

We use [uv](https://docs.astral.sh/uv/) — one command builds the environment for all 20 sessions
from `pyproject.toml` and `uv.lock`, so everyone in the cohort ends up on identical versions.

```bash
git clone git@github.com:Grow-with-Data/CSE-Industrial-Training-26.git
cd CSE-Industrial-Training-26

uv sync                    # creates .venv and installs everything. ~1 minute.
cp .env.example .env       # then paste your Gemini key into .env
uv run jupyter lab         # then pick the .venv kernel — see below
```

Install once, at the repo root. There is no per-session install — week 10's dependencies are already
there, so no session ever opens with a failed `pip install`.

### Pick the right kernel — this is the #1 cause of broken cells

`uv sync` installs into `.venv` at the repo root. Your notebook must run **that** Python, not a
system or Anaconda one. In Jupyter: **Kernel → Change Kernel** and choose the interpreter whose path
ends in `CSE-Industrial-Training-26/.venv/bin/python`. In VS Code: click the kernel name, top right.

If you see `AttributeError: 'Client' object has no attribute 'interactions'`, you are on the wrong
kernel — a different Python with an older `google-genai`. The first cell of every notebook prints
which interpreter it is using, so check that before debugging anything else.

Keys are **yours**, created in your own accounts — we walk through every signup in session. Never
commit `.env`; it's gitignored, keep it that way.

> ⚠️ **Free-tier prompts are used to train Google's models.** Google's pricing page lists "content
> used to improve our products" as **Yes** for the free tier and **No** for paid. Never paste real
> customer data, real names, or anything belonging to an employer into a free-tier notebook. Every
> ticket in `data/tickets.yml` is invented for this reason.

## How to work

Each session folder is self-contained:

```
session-05/
├── session-05.ipynb    # the lesson — follow along in class
├── exercises.ipynb     # do these after class (⭐ warm-up · ⭐⭐ apply · ⭐⭐⭐ stretch)
├── slides/index.html   # the session deck — open it in any browser, works offline
└── project/            # ShopWise as it stands at the end of this session — runnable
```

Worked **solutions are published after the exercise review** at the start of the following session,
so the exercises are worth attempting cold.

`project/` is a **snapshot**, not a shared codebase. `session-06/project/` is `session-05/project/`
plus that session's changes, so you can see exactly what moved:

```bash
diff -r session-05/project session-06/project
```

Missed a session or fell behind? Open the folder for the session you're on — it runs on its own. You
never need `git checkout` to catch up.

Notebooks are committed **with their outputs cleared**, so every cell is yours to run. That is
deliberate: reading an output teaches you much less than watching your own code produce it. If a cell
misbehaves, `Kernel → Restart and Run All` before debugging anything else.

## Session map

Dates will be filled in once the department confirms the start date; the cadence is Friday +
Saturday, 7:30–9:30 PM, ten weeks.


| # | Date | Session | Version | Keys you need |
|---|---|---|---|---|
| S01 | TBD | Hello, AI | — setup | `GEMINI_API_KEY` (free) |
| S02 | TBD | Talking to the machines | v0.1 | `GEMINI_API_KEY` |
| S03 | TBD | From chat to software | v0.2 | `GEMINI_API_KEY` |
| S04 | TBD | One interface to rule them all | v1 | + `LANGSMITH_*` (your own free account) |
| S05 | TBD | Give it hands | v2 | same |
| S06 | TBD | Remember and respond | v3 | same |
| S07 | TBD | Safety rails | v4 | same |
| S08 | TBD | It should know your policies | v5 | same — Qdrant runs **locally, no signup** |
| S09 | TBD | Answer with receipts | v6 | same |
| S10 | TBD | Open the black box | v7 | same |
| S11 | TBD | Pause, resume, remember forever | v8 | same |
| S12 | TBD | A team of specialists | v9 | same |
| S13 | TBD | It needs an API | v10 | same |
| S14 | TBD | From PRD to tasks | v11 | + Claude Code (pre-work; a fallback is provided) |
| S15 | TBD | A face for your assistant | v12 | same |
| S16 | TBD | Ship it | v13 | + deploy account, Qdrant Cloud (free tier) |
| S17 | TBD | Your own model, part 1: decide, build the data, train | v14 | a Google account for Colab (free GPU, no card) |
| S18 | TBD | Your own model, part 2: measure it, serve it, decide | v15 | Ollama on your laptop (installed in S04) |
| S19 | TBD | The AI pair becomes a teammate: skills, subagents, hooks, MCP | v16 | same as S14 |
| S20 | TBD | Demo day | capstone | same |

Cost: the course runs on **Gemini's free tier** throughout, on `gemini-3.1-flash-lite` by default.
Staying inside the notebooks should cost you nothing.

Two capabilities are the exception, and the notebooks say so where they appear: **search grounding**
is free only on `gemini-2.5-flash`/`-flash-lite` (500 requests/day), and **image generation is not
free on any model**. Your instructor demos both from a billed key; those cells are written to explain
themselves rather than crash if you re-run them on a free key.

Google no longer publishes free-tier rate limits — check your own at
[ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits) and in
your AI Studio dashboard. We walk through both in session 1.

## Shared data

`data/` is one copy for the whole course — the ticket set, the customer images the model is shown,
and later the policy documents and order database. Session folders read from it; they never carry
their own copy.

| | What it is | First used |
|---|---|---|
| `data/tickets.yml` | 20 invented support tickets, hand-labelled with a ground-truth `category` | S01 |
| `data/images/` | photos a customer would attach to a ticket — e.g. headphones with a torn earcup pad | S01 §7.3 |
| `data/policies/` | ShopWise's returns, warranty and shipping documents | S08 |
