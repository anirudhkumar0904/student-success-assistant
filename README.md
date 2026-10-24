# Student Success Assistant

Take-home task (Applied AI Engineer, Round 2). Predict which students are at risk of
dropping out, give at-risk students useful feedback on their own lesson explanations,
and recommend how to run it in production.

## Parts

- **Part 1 — Data science & ML:** explore, clean, build features, train a dropout
  model vs a baseline, evaluate with precision/recall/F1. → `notebooks/part1_ml.ipynb`
- **Part 2 — AI/LLM:** judge each explanation (`understood` / `partial` / `wrong`)
  against the lesson key points, generate short feedback, return structured JSON,
  evaluate on the 60 labelled rows. → `notebooks/part2_llm.ipynb`
- **Part 3 — Research memo:** LLM choice for 50k students/month, and when to use a
  small ML model vs an LLM (with the optional TF-IDF + LogReg bonus).
  → `memo/research_memo.md`, `notebooks/part3_bonus.ipynb`

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # then add ANTHROPIC_API_KEY (Part 2 default) and/or GEMINI_API_KEY
```

Then open the notebooks in `notebooks/` in order.

## Data

Provided dataset in `data/raw/` (synthetic, 500 students, 3 lessons, course ran
Jun–30 Sep 2026). See `data/raw/README.md` for the file/column list. Treated as
read-only.

## Repo layout

| Path | What |
|---|---|
| `notebooks/` | one notebook per part |
| `src/` | small plain functions (loading, cleaning, features) |
| `outputs/charts/`, `outputs/json/` | generated charts and JSON (committed) |
| `outputs/cache/` | cached LLM responses / intermediates (gitignored) |
| `memo/` | Part 3 research memo |
| `CLAUDE.md` | working rules for this repo |

## Key findings / evaluation results

_To be filled in as the work is done._

**Part 2 model choice:** the judge runs on **Claude Haiku 5.5** (`claude-haiku-5-5`). It started on
Gemini Flash and moved twice:
1. `gemini-3.8-flash` (newest) was overloaded on the free tier — most calls returned
   `504 DEADLINE_EXCEEDED`; one run completed a single call in ~4.5 minutes.
2. `gemini-3.6-flash` worked (~12 s/call) but the free tier is capped at 5 requests/minute and
   **20 requests/day per model** — the v1 evaluation alone needs 76 calls.

The cache was cleared and v1 re-run from scratch on Haiku, so every result comes from one model.
Provider and model are one line in `src/llm_judge.py` (`PROVIDER, MODEL = ...`); the Gemini code path
is kept. Production lesson, used in the Part 3 memo: newest ≠ best and a free tier is not a production
plan — pin the model, set timeouts, keep a tested fallback, and check quotas against volume.

**Part 2 prompt v1 → v2:** v2 changes only the grading rubric (v1 is kept and still runs). Two caveats:
- **v2's accuracy is optimistic.** The rubric was tuned on the same 60 labelled rows it is measured on;
  a fresh labelled set is needed to confirm the gain.
- **The labels define `understood` as "core key points correct and specific", not "all 4 key points".**
  This differs slightly from `lessons.md` ("covers the key points correctly"). v2 follows the labels;
  in production the definition should be agreed with the course team.

Results on Claude Haiku 5.5 (`outputs/llm_eval_v1.md`, `outputs/llm_eval_v2.md`):

| | v1 | v2 |
|---|---|---|
| Accuracy, all 60 rows | 80.0% | 90.0% |
| Accuracy, 37 unique texts | 83.8% | 91.9% |
| Prompt-injection rows passed | 3/3 | 3/3 |
| Stability (same verdict on a re-run) | 97.3% | 94.6% |
| Avg tokens per call | 1,477 | 2,210 |

v2 fixes most `understood → partial` errors but turns one vague-but-on-topic `partial` (E0274) into
`wrong`.

## What I'd improve with more time

_To be filled in._

## Note on AI tools

_To be filled in: which tools used and for what._
