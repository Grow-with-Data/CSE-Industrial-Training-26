# Git & GitHub — pre-work

You will use Git every session: your ShopWise build is committed as it grows, and your session-20
capstone lives in your own GitHub afterwards. Work through these before session 2 if Git is new to
you, or skim them if it isn't.

| | What it covers |
|---|---|
| [Lesson 1 — Setup](lesson-1-setup.md) · [PDF](lesson-1-setup.pdf) | Installing Git, creating a GitHub account, making a repository, and setting up **SSH keys** so you never type a password again |
| [Lesson 2 — Learning Git](lesson-2-learning-git.md) · [PDF](lesson-2-learning-git.pdf) | The everyday commands: `init` · `clone` · `status` · `add` · `commit` · `push` · `pull` · `branch` · `merge` · `log` · `stash` |
| [Lesson 3 — Practical scenario](lesson-3-practical-scenario.md) · [PDF](lesson-3-practical-scenario.pdf) | A three-person team working the same repo — branches, pull requests, and resolving a merge conflict |
| [গিট ও গিটহাব — এক পলকে](git-and-github-at-a-glance.pdf) | A full Bangla reference book on Git & GitHub, for anyone who prefers reading it in Bangla |

The `.md` and `.pdf` versions of lessons 1–3 are the same content — read whichever you prefer.

> **One rule that matters more than any command:** never commit a `.env` file or an API key. A key in
> a commit is a key on the internet, even if you delete it in the next commit — the old commit still
> has it. If it happens, revoke the key immediately in AI Studio rather than trying to rewrite
> history.

The examples in lessons 2 and 3 use an *expense tracker* project rather than ShopWise. The commands
are identical; only the filenames differ.
