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


def format_checks(checks):
    """[{'point': 1, 'status': 'covered_clearly'}, ...] -> '1 clear, 2 vague, 3 missing'."""
    short = {"covered_clearly": "clear", "covered_vaguely": "vague", "missing": "missing",
             "contradicted": "CONTRADICTED"}
    return ", ".join(f"{c['point']} {short[c['status']]}" for c in checks)


def errors_table(df):
    """One row per unique wrong prediction, with how many labelled rows share that text."""
    wrong = df[df.label != df.verdict].copy()
    counts = wrong.groupby("key").size().rename("rows")
    wrong = wrong.drop_duplicates("key").join(counts, on="key")
    cols = ["explanation_id", "lesson_id", "rows", "explanation_text", "label", "verdict", "key_points_covered"]
    if "key_point_checks" in wrong:  # prompt v2 checks every key point before the verdict
        wrong["key_point_checks"] = wrong.key_point_checks.map(format_checks)
        cols.append("key_point_checks")
    return wrong[cols + ["reasoning"]].sort_values(["lesson_id", "label"])


def per_class(df):
    """Recall (share of each true label found) and precision (share of each predicted label that is right)."""
    rows = {}
    for label in LABELS:
        is_true, is_pred = df.label == label, df.verdict == label
        rows[label] = {
            "recall": (is_true & is_pred).sum() / is_true.sum(),
            "precision": (is_true & is_pred).sum() / is_pred.sum() if is_pred.any() else float("nan"),
        }
    return pd.DataFrame(rows).T.round(2)


def compare_versions(runs):
    """runs = {version: {"df": ..., "stable": stability(...), "usage": usage_summary(...)}}.
    Returns one column per prompt version."""
    table = {}
    for version, r in runs.items():
        acc, classes, usage = accuracy(r["df"]), per_class(r["df"]), r["usage"].loc["all runs"]
        column = {
            "accuracy, all 60 rows": f"{acc['all_rows'][0]:.1%}",
            "accuracy, unique texts": f"{acc['unique_texts'][0]:.1%} ({acc['unique_texts'][1]})",
        }
        for label in LABELS:
            column[f"{label}: recall / precision"] = f"{classes.loc[label, 'recall']:.2f} / {classes.loc[label, 'precision']:.2f}"
        column["stability (identical verdicts)"] = f"{r['stable'][0]:.1%} ({r['stable'][1]} texts)"
        column["avg tokens per call (in + out)"] = (f"{usage.total_tokens / usage.calls:,.0f} "
                                                    f"({usage.prompt_tokens / usage.calls:,.0f} + "
                                                    f"{usage.output_tokens / usage.calls:,.0f})")
        table[version] = column
    out = pd.DataFrame(table)
    out.index.name = "metric"
    return out


def verdict_changes(old, new, watch_ids=()):
    """Unique texts whose verdict differs between two prompt versions, plus any watched ids."""
    both = old.drop_duplicates("key").merge(new.drop_duplicates("key")[["key", "verdict"]],
                                            on="key", suffixes=("_old", "_new"))
    watched = both.key.isin(old[old.explanation_id.isin(watch_ids)].key)
    changed = both.verdict_old != both.verdict_new
    out = both[changed | watched].copy()
    out["changed"] = out.verdict_old != out.verdict_new
    out["now_correct"] = out.verdict_new == out.label
    return out[["explanation_id", "lesson_id", "explanation_text", "label", "verdict_old", "verdict_new",
                "changed", "now_correct"]].sort_values(["changed", "lesson_id"], ascending=[False, True])


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


def usage_summary(usage_path, model, prompt_version, keys=None):
    """Token usage of real API calls for this model + prompt version, per run and in total.
    keys: only count calls for these cache keys (e.g. the evaluation texts), if given."""
    if not usage_path.exists():
        return pd.DataFrame()
    log = pd.DataFrame([json.loads(line) for line in usage_path.read_text(encoding="utf-8").splitlines()])
    log = log[(log.model == model) & (log.prompt_version == prompt_version)]
    if keys is not None:
        log = log[log.key.isin(keys)]
    cols = ["prompt_tokens", "output_tokens", "thinking_tokens", "total_tokens"]
    summary = log.groupby("run")[cols].sum()
    summary.loc["all runs"] = summary.sum()
    summary.insert(0, "calls", log.groupby("run").size().reindex(summary.index[:-1]).tolist() + [len(log)])
    summary["mean_total_per_call"] = (summary.total_tokens / summary.calls).round(0)
    return summary


def write_report(df, path, model, prompt_version, usage, injections, stable, extra_lines=()):
    """df = labelled rows with verdicts; injections = all injection rows (labelled or not);
    stable = output of stability(); extra_lines = more markdown appended at the end."""
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
        "## Per-class results (recall = share of each true label found; precision = share of each verdict that is right)",
        "",
        md_table(per_class(df).rename_axis("label")),
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
    ]
    if len(usage):
        total = usage.loc["all runs"]
        lines += [
            f"**Average per call: {total.total_tokens / total.calls:,.0f} tokens** "
            f"({total.prompt_tokens / total.calls:,.0f} input + {total.output_tokens / total.calls:,.0f} output) "
            f"over {total.calls:.0f} calls; {total.total_tokens:,.0f} tokens in total.",
            "",
            md_table(usage),
            "",
            "_For Claude, output tokens include the model's thinking (not reported separately)._",
            "",
        ]
    else:
        lines += ["_no usage logged_", ""]
    lines += list(extra_lines)
    path.write_text("\n".join(lines), encoding="utf-8")
