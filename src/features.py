"""Build one row of features per student from their early activity only.

No fitted statistics here (no medians, no scaling, no one-hot): those happen inside the
model Pipeline (src/model.py) so they are fitted on training folds only.
"""

import pandas as pd

# Only use quiz activity from the first WINDOW_DAYS after each student's signup.
# Later activity would tell the model whether the student already stopped (a leak).
WINDOW_DAYS = 14

# Used to cap "days to first attempt" when looking at full history (Jun 1 - Sep 30).
COURSE_DAYS = 122

NUMERIC = ["n_attempts", "n_lessons", "mean_score", "min_score", "mean_time_min",
           "active_days", "days_to_first_attempt", "no_attempts_in_window"]
CATEGORICAL = ["age_group", "device", "country"]

# Not used as features:
# - refund_requested: 106 of 117 refund requesters dropped out; it leaks the outcome.
# - signup_date: a calendar date, not a behaviour; would not generalise to a new cohort.


def days_since_signup(students, quiz):
    """Add days_since_signup (fractional days) to each quiz attempt."""
    quiz = quiz.merge(students[["student_id", "signup_date"]], on="student_id")
    quiz["days_since_signup"] = (quiz["attempted_at"] - quiz["signup_date"]).dt.total_seconds() / 86400
    return quiz


def build_features(students, quiz, window_days=WINDOW_DAYS):
    """One row per student. window_days=None means use full history."""
    quiz = days_since_signup(students, quiz)
    if window_days is not None:
        quiz = quiz[quiz["days_since_signup"] < window_days]
    cap = window_days if window_days is not None else COURSE_DAYS

    per_student = quiz.groupby("student_id").agg(
        n_attempts=("attempt_id", "size"),
        n_lessons=("lesson_id", "nunique"),
        mean_score=("score", "mean"),
        min_score=("score", "min"),
        mean_time_min=("time_spent_min", "mean"),  # mean of known times only
        active_days=("attempted_at", lambda t: t.dt.date.nunique()),
        days_to_first_attempt=("days_since_signup", "min"),
    )

    features = students[["student_id"] + CATEGORICAL].merge(per_student, on="student_id", how="left")

    # Students with no attempts in the window. Counts are truly zero and first attempt is
    # "not before the window ended". Scores and time are left missing (NaN) and imputed
    # in the Pipeline; the flag tells the model these values were imputed.
    features["no_attempts_in_window"] = features["n_attempts"].isna().astype(int)
    count_cols = ["n_attempts", "n_lessons", "active_days"]
    features[count_cols] = features[count_cols].fillna(0)
    features["days_to_first_attempt"] = features["days_to_first_attempt"].fillna(cap)

    return features.set_index("student_id")[NUMERIC + CATEGORICAL]


def last_attempt_day(students, quiz):
    """Days from signup to each student's last attempt (0 if they never attempted)."""
    quiz = days_since_signup(students, quiz)
    last = quiz.groupby("student_id")["days_since_signup"].max()
    return students.set_index("student_id").index.to_series().map(last).fillna(0)
