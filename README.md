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

| | v1 | final v2 |
|---|---|---|
| Accuracy, all 60 rows | 80.0% | 81.7% |
| Accuracy, 37 unique texts | 83.8% | 86.5% |
| Precision on `wrong` verdicts (no partly correct student told "wrong") | 1.00 | 1.00 |
| Prompt-injection rows passed | 3/3 | 3/3 |
| Stability (same verdict on a re-run) | 97.3% | 94.6% |
| Avg tokens per call | 1,477 | 2,332 |

**v2 is the final prompt.** There will be no more tuning on these 60 rows.
- **Small gain:** v2 beats v1 by only one unique text, which is within noise.
- **What it adds:** per-key-point checks that make every verdict auditable, and an explicit rule that only
  a contradiction makes an answer `wrong`.

**Feedback-wording fix (not grading tuning):** the first v2 run's `missed` field often stated the correct
answer. Only the wording instructions for `got_right` / `missed` / `hint` were changed: `missed` now names
*what* is missing without giving the content, and the hint stays a nudge. The rubric is identical. v2 was
then re-run from an empty cache.
- **The first v2 run scored 90.0%; the re-run 81.7%.** 4 unique texts changed verdict: E0274 went
  `wrong` → `partial` (fixed); E0040, E0545 and E0720 went `understood` → `partial`.
- **On 60 rows, a few points of accuracy is noise.** Verdicts on borderline answers move with any prompt
  edit and with re-runs.
- The old-wording results are kept in `outputs/cache/` as `v2-oldwording`.

### Known errors (Part 2, final prompt v2)

- **Vague but on-topic `partial` → `wrong` (E0274) is the most harmful error type.** Telling a partly
  correct student they're wrong discourages exactly the at-risk students we want to keep. So precision on
  `wrong` verdicts matters more than headline accuracy.
  - The first v2 run made this error (precision on `wrong` 0.91).
  - The final run doesn't (1.00), but the boundary is fragile.
- **Proposed v3 rule, not implemented:** `wrong` requires a misconception or no correct claim at all;
  vague but on-topic = `partial`. Needs a fresh labelled set to validate.
- **Most common error: `understood` graded `partial`** (E0720, E0040, E0250, E0157, E0545; 11 of 20
  `understood` rows). Each answer misses one point the labels treat as minor.
- **Borderline answers are unstable between runs:** E0432 (v1); E0720 and E0080 (first v2 run); E0108
  and E0333 (final v2).
  - Production fix: majority vote over 2–3 runs.
  - When the runs disagree, send the answer to a teacher.

**At-risk feedback:** final v2 graded all 358 explanations written by the 215 at-risk students who
submitted one (Part 1 threshold 0.368) → `outputs/at_risk_feedback.json`.
- Only 9 new API calls were needed: the 358 explanations are 47 unique texts, and 38 were already graded
  during evaluation.
- Verdicts: 90 understood, 195 partial, 73 wrong.

## What I'd improve with more time

- **Reply in the student's language.** Feedback is always in simple English, even when the student wrote
  in Hinglish. Students writing in Hindi, Tamil or Kannada should get feedback in that language, checked
  by native speakers.
- **A fresh, larger labelled set** (a few hundred real answers, labelled independently) to measure prompts
  honestly, then test the proposed v3 rule for `wrong`.
- **Majority vote over 2–3 runs**, and send to a teacher when they disagree, for borderline answers.
- **Agree the definition of `understood` with the course team** (core points vs all 4 key points).
- **Batch API for nightly grading** (half the cost); feedback doesn't need to be instant.

## Note on AI tools

_To be filled in: which tools used and for what._
