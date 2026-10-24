# Research notes (working numbers for the Part 3 memo)

Raw numbers and assumptions behind `research_memo.md`. Measured values come from this repo's runs;
everything else is marked as an assumption or as not confirmed.

## Measured: Claude Haiku 5.5 on the Part 2 judge

From `outputs/cache/usage_log.jsonl`, summarised in `outputs/llm_eval_v1.md` / `llm_eval_v2.md`
(76 calls per prompt: 37 unique labelled texts, 2 injection rows, 37 stability re-runs).

| Prompt | Avg input tokens | Avg output tokens (incl. thinking) | Avg total | Accuracy (60 rows / unique) |
|---|---|---|---|---|
| v1 | **1,217** | **260** | 1,477 | 80.0% / 83.8% |
| v2 | 1,787 | 423 | 2,210 | 90.0% / 91.9% (optimistic: rubric tuned on these rows) |

v2 costs ~50% more tokens per call (longer rubric + a status for each key point before the verdict).
Latency: not measured systematically; the one timed smoke-test call took ~13 s end to end (incl. client
setup). Needs a proper measurement before the memo quotes a number.

## Cost table: 50,000 students / month

**Assumptions**
- Prices: Claude API list prices per 1M tokens (input / output) — Haiku 5.5 $0.10 / $0.50,
  Sonnet 5.5 $2 / $10, Opus 5.5 $4 / $20 (as listed in Anthropic's API reference, Oct 2026; re-check
  before quoting).
- Tokens per call: the **measured Haiku v1 numbers (1,217 in / 260 out)** for every model. Other models
  were not run, so their real token counts (especially thinking) may differ — treat those rows as rough.
- Volume: *base* = 1.45 explanations per student per month (724 explanations / 500 students in our data)
  → 72,400 calls; *high* = 3 per student (one per lesson) → 150,000 calls.
- No de-duplication cache savings: our synthetic data has heavy duplication (724 rows → 48 unique texts),
  real student writing would not.

| Model | Cost per 1,000 explanations | Base: 72,400 / month | High: 150,000 / month |
|---|---|---|---|
| Claude Haiku 5.5 (v1 tokens) | $0.25 | **$18** | **$38** |
| Claude Haiku 5.5 (v2 tokens: 1,787 / 423) | $0.39 | $28 | $59 |
| Claude Sonnet 5.5 (v1 tokens) | $5.03 | $364 | $755 |
| Claude Opus 5.5 (v1 tokens) | $10.07 | $729 | $1,510 |
| TF-IDF + LR (Part 3 bonus) | ≈ $0 (CPU, ~0.05 s per 1k) | ≈ $0 | ≈ $0 |

Levers not included above: the Batch API (asynchronous, 50% off — fits if feedback can arrive within
hours) and prompt caching of the fixed system prompt (only if it reaches the model's minimum cacheable
length).

## Gemini: could not be evaluated on our task

- `gemini-3.8-flash` (newest Flash): free tier overloaded — most calls returned `504 DEADLINE_EXCEEDED`;
  one run completed a single graded call in ~4.5 minutes.
- `gemini-3.6-flash`: worked (~12 s/call) but the free tier is capped at ~5 requests/minute and
  **20 requests/day per model** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`). One evaluation
  run needs 76 calls, so it could not be completed; only 17 texts were graded before the cap, and those
  results were discarded so every reported number comes from one model.
- So there are **no Gemini accuracy or token numbers** to compare. Gemini paid-tier prices were not
  confirmed here (third-party sources disagree); look them up on Google's pricing page before the memo.
- At 20 requests/day the free tier would cover ~600 explanations a month — far below 72,400.

## Not confirmed / still to check

- Data privacy terms for student data (retention, training use) for each provider.
- Indian-language support (Hindi, Tamil, Kannada) — only Hinglish was tested here: one labelled
  `understood` text (E0720), graded `understood` by v2 in the main run but `partial` in the stability
  re-run. One text is not evidence either way.
- Token counts for Sonnet / Opus on this task (not run).
