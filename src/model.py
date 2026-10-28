"""
Modeling: can state-level, modifiable and structural factors predict
early-onset (ages 20-49) colorectal cancer incidence?

The model is deliberately transparent:
  * outcome = state-year CRC crude rate among adults aged 20-49
  * validation = (a) GroupKFold by state (generalize to unseen states) and
                 (b) temporal holdout (2017-2019 and 2020)
  * algorithms = Ridge, Random Forest, Histogram Gradient Boosting
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "outputs" / "cleaned"

NUMERIC = [
    "year",
    "crc_early_rate_baseline",
    "red_meat_lb_pc",
    "poultry_lb_pc",
    "smoking_pct",
    "obesity_pct",
    "uninsured_pct",
    "log_population",
]
CATEGORICAL = ["region"]
TARGET = "crc_early_rate"


def load_data() -> pd.DataFrame:
    panel = pd.read_csv(CLEAN / "analysis_panel_1999_2020.csv")
    panel = panel.dropna(subset=[TARGET]).copy()
    panel["region"] = panel["region"].fillna("Unknown")
    return panel


def make_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), NUMERIC),
            ("cat", OneHotEncoder(drop="first", sparse_output=False), CATEGORICAL),
        ],
        remainder="drop",
    )


def models() -> dict:
    return {
        "Ridge regression": Pipeline(
            [("prep", make_preprocessor()), ("model", RidgeCV(alphas=np.logspace(-2, 3, 30)))]
        ),
        "Random forest": Pipeline(
            [
                ("prep", make_preprocessor()),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=500, min_samples_leaf=5, random_state=42, n_jobs=-1
                    ),
                ),
            ]
        ),
        "Histogram gradient boosting": Pipeline(
            [
                ("prep", make_preprocessor()),
                (
                    "model",
                    HistGradientBoostingRegressor(
                        max_iter=300,
                        learning_rate=0.05,
                        max_depth=3,
                        min_samples_leaf=20,
                        random_state=42,
                    ),
                ),
            ]
        ),
    }


def group_cv_predictions(model, X, y, groups) -> np.ndarray:
    preds = np.full(len(y), np.nan)
    for train_idx, test_idx in GroupKFold(n_splits=5).split(X, y, groups):
        m = model
        m.fit(X.iloc[train_idx], y.iloc[train_idx])
        preds[test_idx] = m.predict(X.iloc[test_idx])
    return preds


def evaluate() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = load_data()
    X = df[NUMERIC + CATEGORICAL]
    y = df[TARGET]
    groups = df.state_abbr

    rows = []
    all_preds = []
    fitted = {}

    for name, model in models().items():
        pred = group_cv_predictions(model, X, y, groups)
        rows.append(
            {
                "model": name,
                "validation": "5-fold GroupKFold (by state)",
                "r2": r2_score(y, pred),
                "mae": mean_absolute_error(y, pred),
                "n": len(y),
            }
        )
        all_preds.append(
            df[["state_abbr", "year", TARGET]].assign(model=name, prediction=pred)
        )

        # Temporal holdouts
        for label, train_mask, test_mask in [
            ("Temporal holdout 2017-2019", df.year <= 2016, df.year.between(2017, 2019)),
            ("Temporal holdout 2020", df.year <= 2019, df.year == 2020),
        ]:
            model.fit(X[train_mask], y[train_mask])
            test_pred = model.predict(X[test_mask])
            rows.append(
                {
                    "model": name,
                    "validation": label,
                    "r2": r2_score(y[test_mask], test_pred),
                    "mae": mean_absolute_error(y[test_mask], test_pred),
                    "n": int(test_mask.sum()),
                }
            )
        fitted[name] = model

    metrics = pd.DataFrame(rows).round(3)

    # Final model: HGB trained through 2016, evaluated on 2017-2020.
    final = models()["Histogram gradient boosting"]
    train_mask = df.year <= 2016
    test_mask = df.year >= 2017
    final.fit(X[train_mask], y[train_mask])
    test_pred = final.predict(X[test_mask])
    preds = df.loc[test_mask, ["state_abbr", "year", TARGET]].copy()
    preds["prediction"] = test_pred
    preds["residual"] = preds[TARGET] - preds["prediction"]

    # Permutation importance on the temporal holdout (honest, out-of-sample).
    perm = permutation_importance(
        final, X[test_mask], y[test_mask], n_repeats=30, random_state=42, n_jobs=-1
    )
    importance = (
        pd.DataFrame(
            {
                "feature": X.columns,
                "importance_mean": perm.importances_mean,
                "importance_std": perm.importances_std,
            }
        )
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )

    # A second importance view: final model fit on all years.  This is the
    # version used in the report because year cannot extrapolate in the
    # holdout-trained model and would otherwise be forced to zero.
    full_model = models()["Histogram gradient boosting"].fit(X, y)
    perm_full = permutation_importance(
        full_model, X, y, n_repeats=20, random_state=42, n_jobs=-1
    )
    importance_full = (
        pd.DataFrame(
            {
                "feature": X.columns,
                "importance_mean": perm_full.importances_mean,
                "importance_std": perm_full.importances_std,
            }
        )
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )

    return metrics, preds, importance, importance_full, df


def main() -> None:
    metrics, preds, importance, importance_full, df = evaluate()
    metrics.to_csv(CLEAN / "model_metrics.csv", index=False)
    preds.to_csv(CLEAN / "model_test_predictions.csv", index=False)
    importance.to_csv(CLEAN / "model_permutation_importance.csv", index=False)
    importance_full.to_csv(CLEAN / "model_permutation_importance_full.csv", index=False)
    print(metrics.to_string(index=False))
    print("\nPermutation importance (all years, final model):")
    print(importance_full.head(12).round(3).to_string(index=False))
    print(f"\nOutcome rows: {len(df):,}; states: {df.state_abbr.nunique()}")


if __name__ == "__main__":
    main()
