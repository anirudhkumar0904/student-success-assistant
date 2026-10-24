"""Load and clean the raw dataset. Every cleaning step is logged (see CLAUDE.md rule 4)."""

import pandas as pd

RAW_DIR = "../data/raw/"

# Each cleaning step appends one row here: what changed, how many rows, and why.
CLEANING_LOG = []


def log_step(table, what, rows, why):
    """Record and print one cleaning decision."""
    CLEANING_LOG.append({"table": table, "what": what, "rows": rows, "why": why})
    print(f"[clean] {table}: {what} ({rows} rows) - {why}")


def cleaning_log():
    """Return all logged cleaning steps as a table."""
    return pd.DataFrame(CLEANING_LOG)


def load_raw(raw_dir=RAW_DIR):
    """Read the four CSVs as-is. The raw files are never modified."""
    return {
        "students": pd.read_csv(raw_dir + "students.csv"),
        "quiz": pd.read_csv(raw_dir + "quiz_attempts.csv"),
        "explanations": pd.read_csv(raw_dir + "explanations.csv"),
        "outcome": pd.read_csv(raw_dir + "outcome.csv"),
    }


def clean_students(students):
    students = students.copy()
    students["signup_date"] = pd.to_datetime(students["signup_date"])

    for col in ["age_group", "device"]:
        n_missing = students[col].isna().sum()
        students[col] = students[col].fillna("unknown")
        log_step("students", f"filled missing {col} with 'unknown'", n_missing,
                 "keep these students; missing is its own category rather than a guess")

    # refund_requested stays in the table for exploration only.
    # It is NOT used as a model feature (leaks the outcome) - see features.py.
    return students


def clean_quiz(quiz):
    quiz = quiz.copy()
    quiz["attempted_at"] = pd.to_datetime(quiz["attempted_at"])

    bad_score = (quiz["score"] < 0) | (quiz["score"] > 100)
    log_step("quiz", "dropped scores outside 0-100 (all were 999)", bad_score.sum(),
             "impossible value, looks like a placeholder/error code")
    quiz = quiz[~bad_score]

    # Same student, lesson, score, time and timestamp = the same attempt recorded twice.
    same_attempt = quiz.drop(columns="attempt_id").duplicated(keep="first")
    log_step("quiz", "dropped duplicate attempts (identical except attempt_id)", same_attempt.sum(),
             "double-logged rows would inflate attempt counts")
    quiz = quiz[~same_attempt]

    # Not filled here: a median over all students would leak across CV folds.
    # features.py averages only known times; the model Pipeline imputes what is left.
    n_missing = quiz["time_spent_min"].isna().sum()
    log_step("quiz", "left missing time_spent_min as missing", n_missing,
             "missing at a similar rate for both groups; imputed per CV fold inside the model Pipeline")

    return quiz.reset_index(drop=True)


def clean_outcome(outcome):
    outcome = outcome.copy()
    outcome["dropped_out"] = (outcome["dropped_out"] == "yes").astype(int)
    log_step("outcome", "mapped dropped_out yes/no to 1/0", len(outcome),
             "numeric target for modelling")
    return outcome


def load_clean(raw_dir=RAW_DIR):
    """Load raw data and return cleaned students, quiz and outcome tables."""
    CLEANING_LOG.clear()
    raw = load_raw(raw_dir)
    return {
        "students": clean_students(raw["students"]),
        "quiz": clean_quiz(raw["quiz"]),
        "outcome": clean_outcome(raw["outcome"]),
    }
