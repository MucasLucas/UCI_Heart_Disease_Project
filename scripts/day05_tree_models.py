"""Nested development CV for bounded Random Forest and XGBoost searches."""
import json
import platform
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from day03_preprocessing import make_preprocessor
from day04_baselines import load_development, make_model, metrics, sha256

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/day05"
GRIDS = {
    "random_forest_nested": {
        "classifier__max_depth": [3, None],
        "classifier__min_samples_leaf": [3, 8],
    },
    "xgboost_nested": {
        "classifier__max_depth": [1, 2],
        "classifier__n_estimators": [100, 250],
    },
}


def make_tree(name):
    if name == "random_forest_nested":
        classifier = RandomForestClassifier(
            n_estimators=200, max_features="sqrt", class_weight=None,
            random_state=42, n_jobs=1,
        )
    elif name == "xgboost_nested":
        classifier = XGBClassifier(
            objective="binary:logistic", eval_metric="logloss", tree_method="hist",
            learning_rate=0.03, min_child_weight=5, reg_lambda=5.0,
            subsample=1.0, colsample_bytree=1.0, scale_pos_weight=1.0,
            enable_categorical=False,
            random_state=42, n_jobs=1, verbosity=0,
        )
    else:
        raise ValueError(f"Unknown model: {name}")
    return Pipeline([("preprocess", make_preprocessor()), ("classifier", classifier)])


def checked_inner_splits(X, y, outer_fold):
    groups = pd.util.hash_pandas_object(X, index=False)
    cv = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=100 + outer_fold)
    splits = list(cv.split(X, y, groups))
    seen = np.zeros(len(X), dtype=int)
    rows = []
    for inner_fold, (train, valid) in enumerate(splits, 1):
        if set(groups.iloc[train]) & set(groups.iloc[valid]):
            raise ValueError("Identical predictors crossed inner folds.")
        if set(y.iloc[train]) != {0, 1} or set(y.iloc[valid]) != {0, 1}:
            raise ValueError("Inner split lacks a class.")
        seen[valid] += 1
        rows.extend(dict(outer_fold=outer_fold, record_id=X.index[i],
                         inner_validation_fold=inner_fold) for i in valid)
    if not np.all(seen == 1):
        raise ValueError("Inner validation coverage is incomplete.")
    return splits, rows


def main():
    warnings.filterwarnings("error", category=ConvergenceWarning)
    X, y, outer = load_development()
    names = ["dummy_prior", "logistic_unweighted", "logistic_balanced"] + list(GRIDS)
    oof = {name: np.full(len(X), np.nan) for name in names}
    coverage = {name: np.zeros(len(X), dtype=int) for name in names}
    fold_rows, tuning_rows, selected_rows, inner_rows = [], [], [], []
    for fold in range(1, 6):
        train = np.flatnonzero(outer.to_numpy() != fold)
        valid = np.flatnonzero(outer.to_numpy() == fold)
        X_train, y_train = X.iloc[train], y.iloc[train]
        X_valid, y_valid = X.iloc[valid], y.iloc[valid]
        if set(y_train) != {0, 1} or set(y_valid) != {0, 1}:
            raise ValueError("Outer fold lacks a class.")
        inner, memberships = checked_inner_splits(X_train, y_train, fold)
        if {r["record_id"] for r in memberships} & set(X_valid.index):
            raise ValueError("Outer validation entered tuning.")
        inner_rows.extend(memberships)
        print(f"Outer fold {fold}/5: train={len(train)}, validation={len(valid)}", flush=True)
        for name in names:
            if name in GRIDS:
                search = GridSearchCV(
                    make_tree(name), GRIDS[name], scoring="roc_auc", cv=inner,
                    refit=True, n_jobs=1, error_score="raise", return_train_score=False,
                )
                # GridSearchCV clones the complete pipeline for every inner fit.
                # No outer validation data or eval_set is supplied to fitting.
                search.fit(X_train, y_train)
                model = search.best_estimator_
                result = search.cv_results_
                for i, params in enumerate(result["params"]):
                    tuning_rows.append(dict(
                        model=name, outer_fold=fold, candidate=i + 1,
                        parameters=json.dumps(params, sort_keys=True),
                        mean_inner_roc_auc=float(result["mean_test_score"][i]),
                        sd_inner_roc_auc=float(result["std_test_score"][i]),
                        rank=int(result["rank_test_score"][i]),
                        **{f"inner_{k+1}_roc_auc": float(result[f"split{k}_test_score"][i])
                           for k in range(3)},
                    ))
                if not np.isfinite(result["mean_test_score"]).all():
                    raise ValueError("Nonfinite tuning scores.")
                selected_rows.append(dict(
                    model=name, outer_fold=fold,
                    parameters=json.dumps(search.best_params_, sort_keys=True),
                    best_mean_inner_roc_auc=float(search.best_score_),
                ))
            else:
                model = make_model(name).fit(X_train, y_train)
            p = np.asarray(model.predict_proba(X_valid)[:, 1], dtype=np.float64)
            if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
                raise ValueError("Invalid outer validation probabilities.")
            oof[name][valid] = p
            coverage[name][valid] += 1
            fold_rows.append(dict(model=name, fold=fold, **metrics(y_valid, p)))
    summaries, predictions = [], []
    for name in names:
        if not np.all(coverage[name] == 1) or not np.isfinite(oof[name]).all():
            raise ValueError("Each record must have exactly one outer validation prediction.")
        summaries.append(dict(model=name, threshold=0.5, **metrics(y, oof[name])))
        predictions.extend(dict(model=name, record_id=X.index[i], fold=int(outer.iloc[i]),
                                target=int(y.iloc[i]), probability=float(oof[name][i]))
                           for i in range(len(X)))
    if len(tuning_rows) != 40 or len(selected_rows) != 10:
        raise ValueError("Unexpected bounded search size.")
    OUT.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(summaries)
    tables = {"oof_metrics.csv": summary, "fold_metrics.csv": pd.DataFrame(fold_rows),
              "oof_predictions.csv": pd.DataFrame(predictions),
              "inner_search_results.csv": pd.DataFrame(tuning_rows),
              "selected_parameters.csv": pd.DataFrame(selected_rows),
              "inner_fold_assignments.csv": pd.DataFrame(inner_rows)}
    for filename, table in tables.items():
        table.to_csv(OUT / filename, index=False)
    inputs = ["scripts/day03_preprocessing.py", "scripts/day04_baselines.py",
              "scripts/day05_tree_models.py", "data/raw/processed.cleveland.data",
              "reports/day01/cleveland_split.csv", "reports/day03/development_folds.csv"]
    manifest = dict(
        development_n=len(X), locked_test_n=61, holdout_analyzed=False,
        outer_folds=5, inner_folds=3, inner_selection_metric="mean ROC-AUC",
        tie_rule="first candidate in deterministic ParameterGrid order",
        search_grids=GRIDS, candidate_fits=120, outer_tree_refits=10,
        fixed_baseline_fits=15, threshold=0.5, threshold_selected=False,
        calibrated=False, early_stopping=False, final_model_selected=False,
        random_forest_fixed=make_tree("random_forest_nested").named_steps["classifier"].get_params(),
        xgboost_fixed=make_tree("xgboost_nested").named_steps["classifier"].get_params(),
        python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
        scikit_learn=sklearn.__version__, xgboost=xgboost.__version__,
        hashes={p: sha256(ROOT / p) for p in inputs},
    )
    # Encode XGBoost's NaN sentinel as text to keep the manifest strict JSON.
    manifest["xgboost_fixed"]["missing"] = "NaN (missing-value sentinel)"
    (OUT / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(summary.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print("PASS: 242 development records; five outer folds; three inner folds.")
    print("Tree tuning stayed inside each outer training fold. Locked test not analyzed.")
    print("Threshold fixed at 0.5. No calibration or final model selection.")
    print(f"Outputs saved to: {OUT}")
    print("Day 5 remains open pending local output review, interpretation, and commit.")


if __name__ == "__main__":
    main()
