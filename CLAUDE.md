# Student Success Assistant — Working Rules

Take-home for Applied AI Engineer (Round 2). Three parts: Part 1 Data science & ML
(predict dropout), Part 2 AI/LLM (judge student explanations + feedback), Part 3
Research memo. I have to **demo this live and edit it in the interview**, so these
rules are not optional.

## Rules

1. **Keep code simple and readable.** I must be able to explain and edit every line
   live in an interview. Prefer small plain functions in `src/` over clever
   abstractions. No code I can't explain.

2. **No API keys in code.** Load `GEMINI_API_KEY` from the environment (`.env` via
   `python-dotenv`). `.env` is gitignored; `.env.example` shows the shape. Never
   hardcode or commit a key.

3. **Fixed random seeds.** Set a seed (e.g. `SEED = 42`) for every split, shuffle,
   and model so results reproduce run to run.

4. **Log every cleaning decision.** Each data-cleaning step gets a short logged note
   (what changed, how many rows, and why). Cleaning must be transparent, not silent.

5. **Do not use `refund_requested` as a feature.** It leaks outcome / is not an
   honest early-warning signal. Exclude it from Part 1 modeling.

## Layout

- `notebooks/` — one notebook per part.
- `src/`       — small, reusable plain functions (loading, cleaning, features).
- `outputs/`   — `charts/` and `json/` are committed; `cache/` (LLM responses,
                 intermediates) is gitignored.
- `memo/`      — Part 3 research memo.
- `data/raw/`  — provided dataset (read-only; never edit in place).
