"""Model pipelines, baselines and cross-validation helpers for Part 1."""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, make_scorer, precision_score
from sklearn.model_selection import cross_validate
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.features import CATEGORICAL, NUMERIC

# zero_division=0: a model that never predicts dropout gets precision 0, not a warning.
SCORING = {
    "accuracy": "accuracy",
    "precision": make_scorer(precision_score, zero_division=0),
    "recall": "recall",
    "f1": "f1",
    "auc": "roc_auc",
}


def make_preprocessor():
    """Impute + scale numbers, one-hot categories. Fitted on each training fold only."""
    numeric = make_pipeline(SimpleImputer(strategy="median"), StandardScaler())
    categorical = OneHotEncoder(handle_unknown="ignore")
    return ColumnTransformer([("num", numeric, NUMERIC), ("cat", categorical, CATEGORICAL)])


def make_logreg(seed):
    return make_pipeline(make_preprocessor(),
                         LogisticRegression(class_weight="balanced", max_iter=1000, random_state=seed))


def make_forest(seed):
    return make_pipeline(make_preprocessor(),
                         RandomForestClassifier(n_estimators=300, min_samples_leaf=5,
                                                class_weight="balanced", random_state=seed))


def make_always_no():
    """Baseline A: always predict 'no dropout'."""
    return DummyClassifier(strategy="constant", constant=0)


class ThresholdRule(ClassifierMixin, BaseEstimator):
    """Baseline B: a one-line rule, predict dropout if X[column] <= N (or >= N).

    N is chosen on the training data (the value with the best F1), so in CV it
    never sees the test fold. Missing values (no attempts) are never flagged.
    """

    def __init__(self, column="mean_score", direction="<="):
        self.column = column
        self.direction = direction

    def _flag(self, values, n):
        return values <= n if self.direction == "<=" else values >= n

    def fit(self, X, y):
        values = X[self.column]
        candidates = sorted(values.dropna().unique())
        self.n_ = max(candidates, key=lambda n: f1_score(y, self._flag(values, n)))
        self.classes_ = np.array([0, 1])
        return self

    def predict(self, X):
        return self._flag(X[self.column], self.n_).astype(int).to_numpy()

    def predict_proba(self, X):
        flagged = self.predict(X)
        return np.column_stack([1 - flagged, flagged])


def cv_summary(model, X, y, cv):
    """Cross-validate and return {metric: (mean, std)} across folds."""
    scores = cross_validate(model, X, y, cv=cv, scoring=SCORING)
    return {m: (scores[f"test_{m}"].mean(), scores[f"test_{m}"].std()) for m in SCORING}


def format_mean_std(summary_rows):
    """Turn {name: {metric: (mean, std)}} into a readable 'mean ± std' table."""
    table = {name: {m: f"{mean:.3f} ± {std:.3f}" for m, (mean, std) in row.items()}
             for name, row in summary_rows.items()}
    return pd.DataFrame(table).T
