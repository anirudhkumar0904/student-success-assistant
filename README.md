# Student Success Assistant

Take-home task (Applied AI Engineer, Round 2). Predict which students are at risk of dropping out, give
at-risk students useful feedback on their own lesson explanations, and recommend how to run it in
production.

- **Part 1 — Data science & ML:** explore, clean, build features, train a dropout model vs baselines,
  evaluate with precision / recall / F1. → `notebooks/part1_ml.ipynb`
- **Part 2 — AI / LLM:** judge each explanation (`understood` / `partial` / `wrong`) against the lesson
  key points, write short feedback, return structured JSON, evaluate on the 60 labelled rows, and run it
  for the at-risk students from Part 1. → `notebooks/part2_llm.ipynb`
- **Part 3 — Research memo:** which LLM for 50k students/month, and when a small ML model beats an LLM
  (with the TF-IDF + LogReg bonus). → **`memo/research_memo.md`** (2-page PDF: `memo/research_memo.pdf`),
  `notebooks/part3_bonus.ipynb`

## How to run

Tested with Python 3.12 on Windows, from a fresh clone.

> **Windows:** clone into a short path, for example `C:\code\student-success`. Jupyter installs some very
> long file paths, and in a deeply nested folder `pip install` fails with `WinError 206`. The alternative
> is to enable Windows long paths.

```bash
git clone <repo-url> && cd student-success
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # Windows: copy .env.example .env
# optional: put your key in .env:  ANTHROPIC_API_KEY=...   (only needed for REFRESH = True, see below)
```

Run the notebooks **in this order** (open them in Jupyter, or run headless from the repo root):

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/part1_ml.ipynb     # no key needed
jupyter nbconvert --to notebook --execute --inplace notebooks/part2_llm.ipynb    # no key needed (cache)
jupyter nbconvert --to notebook --execute --inplace notebooks/part3_bonus.ipynb  # no key needed
```

1. **Part 1** writes `outputs/risk_scores.csv` (risk score + at-risk flag per student), which Part 2
   uses, plus charts and JSON in `outputs/`. It is deterministic (seed 42).
2. **Part 2** uses Claude Haiku 5.5. The LLM judgements from the final run are **committed** in
   `outputs/cache/`, so there are two modes, set by one flag at the top of `src/llm_judge.py`:
   - **`REFRESH = False` (default):** everything runs from the committed cache. **No API key, no API
     calls, and exactly the committed results.** A text that isn't in the cache raises a clear error.
   - **`REFRESH = True`:** every unique text is graded again by the API and the cache is overwritten.
     Needs `ANTHROPIC_API_KEY` in `.env`. Measured from a fresh clone: **161 API calls, about 10 minutes,
     under $0.10.**
   - **A cold re-run gives slightly different numbers**, because the LLM is not deterministic. See the
     run-to-run spread under Part 2 below.
   - **Provider:** one line in `src/llm_judge.py`: `PROVIDER, MODEL = "anthropic", "claude-haiku-5-5"`. The
     Gemini path also works, with `GEMINI_API_KEY`.
3. **Part 3 bonus** trains TF-IDF + LR on the 60 labelled rows. No key needed.

Keys are only read from `.env` (gitignored), never from code. `.env.example` shows the shape.

## Key findings

### Part 1: dropout prediction

**Data checks (all logged in `src/data.py`):**
- 3 quiz scores of `999` were dropped.
- 18 duplicate attempts were dropped.
- 95 missing `time_spent_min` values are imputed inside the model Pipeline, per CV fold.
- 21 missing `age_group` and 16 missing `device` values become `"unknown"`.
- 25% of the 500 students dropped out.

**Leaks found and excluded:**
- **`refund_requested`:** 91% of students who asked for a refund dropped out, against 5% of the rest.
  A refund is part of leaving, not an early sign of it.
- **Full-history activity:** it scores AUC 0.90, but only because every dropout has already stopped by
  then.
- The model therefore only sees each student's **first 14 days**. That's the longest window in which most
  dropouts (58%) are still active.

**Surprise:** in the first 14 days, dropouts are *ahead*, not behind. They start sooner, reach more lessons
and score lower: "rushing". The number of lessons reached is the strongest feature.

5-fold stratified CV (seed 42), mean ± std across folds, default 0.5 threshold:

| Model | Precision | Recall | F1 | AUC |
|---|---|---|---|---|
| A: always "no dropout" (accuracy 75%!) | 0.00 | 0.00 | 0.00 | 0.50 |
| B1: `n_lessons >= N` (one-line rule) | 0.27 | 0.95 | 0.42 | 0.55 |
| B2: `mean_score <= N` (one-line rule) | 0.35 | 0.70 | 0.46 ± 0.06 | 0.64 ± 0.06 |
| **Logistic regression (final)** | 0.46 | 0.68 | **0.54 ± 0.06** | **0.77 ± 0.04** |
| Random forest (not better, dropped) | 0.46 | 0.62 | 0.52 ± 0.06 | 0.75 ± 0.05 |

**Threshold:** recall matters more than precision here. Missing an at-risk student costs more than an
unneeded nudge. The threshold is the highest one with recall ≥ 0.8 on out-of-fold predictions:
- **Threshold 0.368: recall 0.80, precision 0.39.** 257 of 500 students are flagged, 1.6× better than
  random flagging.
- Choosing the threshold on the same out-of-fold predictions makes these numbers slightly optimistic.

### Part 2: LLM judge and feedback

**Model: Claude Haiku 5.5.** Gemini was tried first, but its free tier couldn't run the evaluation:
- `gemini-3.8-flash` mostly returned `504` timeouts.
- `gemini-3.6-flash` is capped at **20 requests/day per model**, and one evaluation needs 76 calls.

The cache was cleared and everything was re-run on Haiku, so every result comes from one model.
Production lesson for Part 3: newest ≠ best, and a free tier is not a production plan.

**Prompt v1 → final v2:** v2 changes only the grading rubric. It checks each key point (clear / vague /
missing / contradicted) *before* choosing a verdict. Results on the 60 labelled rows
(`outputs/llm_eval_v1.md`, `outputs/llm_eval_v2.md`):

Ranges cover two complete cold runs from an empty cache (the committed run and the fresh-clone test);
the committed reports and cache are from the first.

| | v1 | final v2 |
|---|---|---|
| Accuracy, all 60 rows | 80.0% (both runs) | **78.3%–81.7%** |
| Accuracy, 37 unique texts | 83.8% (both runs) | **81.1%–86.5%** |
| Precision on `wrong` verdicts (no partly correct student told "wrong") | 1.00 | 1.00 |
| Prompt-injection attempts resisted | 3/3 | 3/3 |
| Stability (same verdict on a re-run) | 89.2%–97.3% | 94.6%–97.3% |
| Avg tokens per call | 1,477 | 2,332 |

**Run-to-run spread.** Repeating the whole evaluation from an empty cache moves v2 by about 5 points on
unique texts. **Neither prompt is reliably better on these 37 texts.**

**Why v2 is final:** accuracy is tied with v1 within noise on 37 texts. But v2 has the fixed "missed"
wording, and per-key-point checks that make each verdict auditable. The cost is ~58% more tokens and
slightly lower stability in the committed run (not in the re-run): still about $35/month at 50,000
students.

**Feedback-wording fix (not grading tuning):** the first v2 run's `missed` field often stated the
correct answer. Only the wording instructions for `got_right` / `missed` / `hint` were changed: `missed`
now names *what* is missing without giving the content, and the hint stays a nudge. The rubric is
identical. That first run scored 90.0%; the re-run from an empty cache scored 81.7%:
- **4 unique texts changed verdict.** E0274 went `wrong` → `partial` (fixed); E0040, E0545 and E0720 went
  `understood` → `partial`.
- **So on 60 rows, a few points of accuracy is noise.**

**At-risk feedback:** all 358 explanations from the 215 at-risk students who wrote one →
`outputs/at_risk_feedback.json`. Verdicts: 90 understood, 195 partial, 73 wrong.
- **Only 9 new API calls were needed:** after stripping filler sign-offs, the 358 explanations are 47
  unique texts, and 38 were already graded during evaluation.

### Part 3 bonus: TF-IDF + logistic regression

- **73% accuracy on a random split, 19% when whole answer templates are held out.** On the grouped
  folds, always guessing the most common label gets 12%. The model memorises templates; it doesn't
  learn to grade.
- It's nearly free and fast (~50 ms per 1,000 texts), but useless on unseen wording at this data size.

**The Part 3 memo is `memo/research_memo.md`** (also as a 2-page PDF, `memo/research_memo.pdf`): which LLM
for 50k students/month (cost, speed, quality, privacy, Indian languages, recommendation, risks) and when a
small ML model beats an LLM. The working notes and sources behind it are in `memo/research_notes_A_sources.md`
and `memo/research_notes_B.md`.

## Assumptions

- The data is synthetic (500 students, 3 lessons, June–30 Sep 2026). It's treated as read-only and
  checked before use.
- **Early warning = first 14 days after signup** (`WINDOW_DAYS` in `src/features.py`). Later activity is
  not used.
- **At-risk threshold = recall ≥ 0.8**, because a missed at-risk student is worse than an extra nudge.
- **`understood` means the core key points are correct and specific**, as in the labels. That's not "all
  4 key points": it differs slightly from `lessons.md` and should be agreed with the course team.
- Filler sign-offs ("i think", "hope this is right!", "(sorry for typos)", "not sure tho") carry no
  content. They're stripped before grading and caching.
- Cost estimates use 85,000 LLM calls a month (50,000 students × 1.7 explanations each). They assume no
  cache savings, since real students don't repeat templates.

## Known errors

**Part 2 (final prompt v2):**
- **Vague but on-topic `partial` → `wrong` (E0274) is the most harmful error type.** Telling a partly
  correct student they're wrong discourages exactly the at-risk students we want to keep. So precision
  on `wrong` verdicts matters more than headline accuracy.
  - The first v2 run made this error (precision on `wrong` 0.91).
  - The final run doesn't (1.00), but the boundary is fragile.
  - **Proposed v3 rule, not implemented:** `wrong` requires a misconception or no correct claim at all;
    vague but on-topic = `partial`. Needs a fresh labelled set to validate.
- **Most common error: `understood` graded `partial`** (E0720, E0040, E0250, E0157, E0545; 11 of 20
  `understood` rows). Each answer misses one point the labels treat as minor.
- **Borderline answers flip between runs:** E0432 (v1); E0720 and E0080 (first v2 run); E0108 and E0333
  (final v2).
  - Production fix: majority vote over 2–3 runs.
  - When the runs disagree, send the answer to a teacher.
- **The accuracy numbers are optimistic.** The v2 rubric was tuned on the same 60 rows it's measured on,
  and a fresh labelled set is needed to confirm it.

**Part 1:**
- With 125 dropouts, the fold-to-fold spread (AUC ± 0.04) is as large as the gap between neighbouring
  time windows.
- 42% of dropouts have already stopped by day 14, so the model is early for most students, not all.

## What I'd improve with more time

- **Reply in the student's language.** Feedback is always in simple English, even when the student wrote
  in Hinglish. Students writing in Hindi, Tamil or Kannada should get feedback in that language, checked
  by native speakers.
- **A fresh, larger labelled set** (a few hundred real answers, labelled independently) to measure prompts
  honestly, then test the proposed v3 rule for `wrong`.
- **Majority vote over 2–3 runs** for borderline answers, and send to a teacher when they disagree.
- **Agree the definition of `understood` with the course team** (core points vs all 4 key points).
- **Batch API for nightly grading** (half the cost); feedback doesn't need to be instant.
- **Choose the Part 1 threshold inside each training fold** (nested CV), so its precision/recall isn't
  optimistic.
- **Validate the dropout model on a later cohort** before using it on real students.

## AI tools used

I used AI tools throughout this task, as the brief allows. This is what I used and for what:

- **Claude Code (in VS Code)** wrote most of the code: data loading and cleaning, features, the model and evaluation, the LLM judge, notebooks and this README. I gave it one step at a time, read the output of each step, and asked for changes before committing.
- **Claude (chat)** acted as a reviewer and planner. It helped me break the task into steps, check the data for problems (the 999 scores, duplicates, the refund leak, prompt injections), check the agent's results, research Part 3 (pricing, privacy, Indian-language support, examples) and draft the research memo, which I then edited.
- **Claude Haiku 5.5** is the LLM that grades explanations in Part 2. I first tried Gemini 3.8 Flash and 3.6 Flash, but the free tier timed out and then hit a 20-requests-a-day cap.

**Decisions I made or approved after checking them against the data:**
- excluding `refund_requested` (leaks the outcome)
- using only the first 14 days of activity (full history leaks the outcome)
- prioritising recall and choosing the threshold
- dropping the random forest
- the v2 rubric, and stopping tuning to avoid overfitting the 60 rows
- treating a few points' difference between prompts as noise
- the model recommendation in the memo

Several of these were first suggested by the AI. I accepted them only after looking at the numbers.

All results in this repo were produced by running the code. No numbers were written by hand.

## Repo layout

| Path | What |
|---|---|
| `notebooks/` | one notebook per part |
| `src/` | small plain functions: `data.py` (load + logged cleaning), `features.py` (14-day features), `model.py` (Pipelines, baselines, CV), `llm_judge.py` (prompts, LLM calls, cache), `llm_eval.py` (accuracy, reports) |
| `outputs/charts/`, `outputs/json/` | charts and JSON results (committed) |
| `outputs/risk_scores.csv`, `outputs/at_risk_feedback.json`, `outputs/llm_eval_*.md` | Part 1 / Part 2 results (committed) |
| `outputs/cache/` | LLM judgements from the final run + token usage log (committed; `REFRESH = False` runs from it) |
| `memo/` | Part 3 research memo and notes |
| `data/raw/` | provided dataset (read-only) |
| `CLAUDE.md` | working rules for this repo |
