"""Model constants for the ShopWise assistant — v0.1.

Constants only. No logic, no imports beyond os, nothing that can fail.

Every value is read from the environment with a default, so when Google retires a
model the fix is one line in `.env` rather than an edit in every snapshot:

    SHOPWISE_MODEL=gemini-3.6-flash-lite

These five names are the same in every session from here on. Code refers to
`config.MODEL`, never to a model ID spelled out in place. Session 3 turns this
file into a validated Settings class — these naked constants are here so that
upgrade shows up as a diff.
"""

import os

# The course default: fast, cheap, and on the free tier. Start here always.
MODEL = os.getenv("SHOPWISE_MODEL", "gemini-3.5-flash-lite")

# One tier up. Reach for it only when you can name a task the default fails.
MODEL_STRONG = os.getenv("SHOPWISE_MODEL_STRONG", "gemini-3.8-flash")

# Search-grounded answers. Billed — not used before session 12.
MODEL_SEARCH = os.getenv("SHOPWISE_MODEL_SEARCH", "gemini-3.5-flash-lite")

# The strongest and slowest. Used sparingly, from session 9's evaluation work.
MODEL_PRO = os.getenv("SHOPWISE_MODEL_PRO", "gemini-2.5-pro")

# Embeddings. Not used until session 8 — but the name is fixed now so that
# every snapshot's config.py has the same shape.
EMBED_MODEL = os.getenv("SHOPWISE_EMBED_MODEL", "gemini-embedding-2")
