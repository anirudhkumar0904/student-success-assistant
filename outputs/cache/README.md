# Cached LLM judgements (committed)

Results of the final committed Part 2 run (Claude Haiku 5.5), so the notebooks run with no API key.

- `judgements_v1.json`, `judgements_v2.json`: one grading per unique (prompt, model, lesson, normalized text).
- `*_repeat.json`: the second, independent run used for the stability check.
- `judgements_v2-oldwording*.json`: v2 before the feedback-wording fix (kept for comparison only).
- `usage_log.jsonl`: token usage of every real API call (used for the cost estimates).

`REFRESH = False` in `src/llm_judge.py` reads only these files. `REFRESH = True` calls the API again and
overwrites them; a cold re-run gives slightly different numbers (see the README's run-to-run spread).
