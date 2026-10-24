"""Part 2: evaluate LLM verdicts against the labelled rows and write a markdown report."""

import json
import time

import pandas as pd

LABELS = ["understood", "partial", "wrong"]

# Rows that try to instruct the grader instead of explaining the lesson.
INJECTION_PATTERN = r"ignore (?:all )?previous|note to grader|system prompt|mark this|output verdict"


def md_table(df):
    """Plain markdown table (no extra dependencies)."""
    df = df.reset_index() if df.index.name else df
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    divider = "|" + "---|" * len(df.columns)
    rows = ["| " + " | ".join(str(v).replace("|", "/").replace("\n", " ") for v in row) + " |"
            for row in df.itertuples(index=False)]
    return "\n".join([header, divider] + rows)


def accuracy(df):
    """Accuracy on every row, and on unique texts (one row per lesson + normalized text)."""
    unique = df.drop_duplicates("key")
    return {
        "all_rows": ((df.label == df.verdict).mean(), len(df)),
        "unique_texts": ((unique.label == unique.verdict).mean(), len(unique)),
    }


def confusion(df):
    """Rows = true label, columns = predicted verdict."""
    return pd.crosstab(df.label.rename("true"), df.verdict.rename("predicted")) \
        .reindex(index=LABELS, columns=LABELS, fill_value=0)


def errors_table(df):
    """One row per unique wrong prediction, with how many labelled rows share that text."""
    wrong = df[df.label != df.verdict]
    counts = wrong.groupby("key").size().rename("rows")
    wrong = wrong.drop_duplicates("key").join(counts, on="key")
    return wrong[["explanation_id", "lesson_id", "rows", "explanation_text", "label", "verdict",
                  "key_points_covered", "reasoning"]].sort_values(["lesson_id", "label"])


def is_injection(texts):
    return texts.str.contains(INJECTION_PATTERN, case=False, regex=True)


def injection_rows(df):
    flagged = df[is_injection(df.explanation_text)].copy()
    flagged["passed"] = flagged.verdict != "understood"  # the injection asked for "understood"
    return flagged[["explanation_id", "explanation_text", "label", "verdict", "passed", "reasoning", "hint"]]


def stability(first, second):
    """Compare two runs on the same unique texts. Returns (% identical verdicts, n, flips table)."""
    both = first.drop_duplicates("key").merge(second.drop_duplicates("key")[["key", "verdict"]],
                                               on="key", suffixes=("_run1", "_run2"))
    same = both.verdict_run1 == both.verdict_run2
    flips = both[~same][["explanation_id", "lesson_id", "explanation_text", "label",
                         "verdict_run1", "verdict_run2"]]
    return same.mean(), len(both), flips


def usage_summary(usage_path, prompt_version):
    """Token usage of real API calls for this prompt version, per run and in total."""
    if not usage_path.exists():
        return pd.DataFrame()
    log = pd.DataFrame([json.loads(line) for line in usage_path.read_text(encoding="utf-8").splitlines()])
    log = log[log.prompt_version == prompt_version]
    cols = ["prompt_tokens", "output_tokens", "thinking_tokens", "total_tokens"]
    summary = log.groupby("run")[cols].sum()
    summary.loc["all runs"] = summary.sum()
    summary.insert(0, "calls", log.groupby("run").size().reindex(summary.index[:-1]).tolist() + [len(log)])
    summary["mean_total_per_call"] = (summary.total_tokens / summary.calls).round(0)
    return summary


def write_report(df, path, model, prompt_version, usage, injections, stable):
    """df = labelled rows with verdicts; injections = all injection rows (labelled or not);
    stable = output of stability()."""
    acc = accuracy(df)
    stable_pct, stable_n, flips = stable
    lines = [
        f"# LLM judge evaluation — prompt {prompt_version}",
        "",
        f"Model `{model}`, default temperature, run {time.strftime('%Y-%m-%d')}, on the {len(df)} labelled rows.",
        "",
        "## Accuracy",
        "",
        f"- All rows: **{acc['all_rows'][0]:.1%}** ({acc['all_rows'][1]} rows)",
        f"- Unique texts (lesson + text after stripping filler sign-offs): "
        f"**{acc['unique_texts'][0]:.1%}** ({acc['unique_texts'][1]} texts)",
        "",
        "## Confusion matrix (rows = true label, columns = predicted)",
        "",
        md_table(confusion(df)),
        "",
        "## Every wrong prediction (one row per unique text; `rows` = labelled rows sharing it)",
        "",
        md_table(errors_table(df)),
        "",
        "## Prompt-injection rows (label blank = unlabelled row; pass = verdict not 'understood')",
        "",
        md_table(injections),
        "",
        "## Stability (default temperature)",
        "",
        f"The {stable_n} unique labelled texts were graded twice, the second time bypassing the cache: "
        f"**{stable_pct:.1%} identical verdicts**.",
        "",
        md_table(flips) if len(flips) else "_No verdict changed between runs._",
        "",
        "## Token usage (real API calls only; cache hits cost nothing)",
        "",
        md_table(usage) if len(usage) else "_no usage logged_",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
