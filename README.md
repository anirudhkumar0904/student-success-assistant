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

cp .env.example .env      # then add your GEMINI_API_KEY (needed for Part 2)
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

## What I'd improve with more time

_To be filled in._

## Note on AI tools

_To be filled in: which tools used and for what._
