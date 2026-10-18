"""Prespecified development-only baselines; no tuning or holdout evaluation."""
import hashlib
import json
import platform
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, brier_score_loss, confusion_matrix, roc_auc_score,
)
from sklearn.pipeline import Pipeline

from day03_preprocessing import COLUMNS, DOMAINS, FEATURES, NUMERIC, make_preprocessor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/day04"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_development():
    source = ROOT / "data/raw/processed.cleveland.data"
    split_path = ROOT / "reports/day01/cleveland_split.csv"
    manifest = json.loads((ROOT / "reports/day01/manifest.json").read_text(encoding="utf-8"))
    if sha256(source) != manifest["source_manifest"][source.name]["sha256"]:
        raise ValueError("Source hash changed; stop for review.")
    canonical = split_path.read_bytes().replace(b"\r\n", b"\n")
    blob = hashlib.sha1(f"blob {len(canonical)}\0".encode() + canonical).hexdigest()
    if blob != "37417c4d1976cbae3b00492ad014ab13c1f826a5":
        raise ValueError("Frozen split changed; stop for review.")
    split = pd.read_csv(split_path)
    if split.record_id.isna().any() or split.record_id.duplicated().any():
        raise ValueError("Invalid split IDs.")
    if split.partition.value_counts().to_dict() != {"development": 242, "locked_test": 61}:
        raise ValueError("Unexpected partition sizes.")
    raw = pd.read_csv(source, header=None, names=COLUMNS, na_values="?")
    raw.index = [f"cleveland:{i:04d}" for i in range(len(raw))]
    if set(raw.index) != set(split.record_id):
        raise ValueError("Source and split IDs differ.")
    ids = split.loc[split.partition.eq("development"), "record_id"]
    dev = raw.loc[ids, FEATURES + ["num"]].copy()
    if not dev.num.isin([0, 1, 2, 3, 4]).all():
        raise ValueError("Invalid development labels.")
    X, y = dev[FEATURES], dev.num.gt(0).astype(int)
    if y.value_counts().to_dict() != {0: 131, 1: 111}:
        raise ValueError("Unexpected development outcome counts.")
    for feature, allowed in DOMAINS.items():
        if not X[feature].dropna().isin(allowed).all():
            raise ValueError(f"Invalid category: {feature}")
    values = X.to_numpy(dtype=float)
    if not np.isfinite(values[~np.isnan(values)]).all():
        raise ValueError("Nonfinite input.")
    if X[["age", "trestbps", "chol", "thalach"]].le(0).any().any() or X.oldpeak.lt(0).any():
        raise ValueError("Invalid physiology requires review.")
    folds_path = ROOT / "reports/day03/development_folds.csv"
    canonical = folds_path.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(canonical).hexdigest() != FOLDS_SHA256:
        raise ValueError("Day 3 fold assignments changed; use the committed version.")
    folds = pd.read_csv(folds_path)
    if folds.record_id.isna().any() or folds.record_id.duplicated().any():
        raise ValueError("Invalid fold IDs.")
    if set(folds.record_id) != set(X.index) or set(folds.validation_fold) != set(range(1, 6)):
        raise ValueError("Fold assignments differ from development cohort.")
    assignment = folds.set_index("record_id").loc[X.index, "validation_fold"]
    groups = pd.util.hash_pandas_object(X, index=False)
    if pd.DataFrame({"group": groups, "fold": assignment}).groupby("group").fold.nunique().max() != 1:
        raise ValueError("Identical predictor rows cross folds.")
    return X, y, assignment


def make_model(name):
    if name == "dummy_prior":
        classifier = DummyClassifier(strategy="prior")
    else:
        classifier = LogisticRegression(
            C=1.0, solver="lbfgs", max_iter=5000,
            class_weight="balanced" if name == "logistic_balanced" else None,
            random_state=42,
        )
    return Pipeline([("preprocess", make_preprocessor()), ("classifier", classifier)])


def metrics(y, probability):
    prediction = np.asarray(probability) >= 0.5
    tn, fp, fn, tp = confusion_matrix(y, prediction, labels=[0, 1]).ravel()
    return dict(n=len(y), roc_auc=roc_auc_score(y, probability),
                average_precision=average_precision_score(y, probability),
                brier=brier_score_loss(y, probability),
                sensitivity=tp / (tp + fn), specificity=tn / (tn + fp),
                tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp))


def coefficient_contrasts(model, model_name):
    """Interpret full one-hot encoding via category coefficient differences."""
    prep = model.named_steps["preprocess"]
    beta = model.named_steps["classifier"].coef_[0]
    rows = []
    scales = prep.named_transformers_["numeric"].named_steps["scale"].scale_
    for feature, coefficient, scale in zip(NUMERIC, beta[:len(NUMERIC)], scales):
        rows.append(dict(model=model_name, feature=feature,
                         comparison="increase by one development SD", raw_units=float(scale),
                         log_odds_contrast=float(coefficient), odds_ratio=float(np.exp(coefficient))))
    offset = len(NUMERIC)
    encoder = prep.named_transformers_["categorical"].named_steps["encode"]
    for feature, categories in zip(DOMAINS, encoder.categories_):
        coefficients = beta[offset:offset + len(categories)]
        for i in range(1, len(categories)):
            contrast = coefficients[i] - coefficients[0]
            rows.append(dict(model=model_name, feature=feature,
                             comparison=f"category {categories[i]:g} vs {categories[0]:g}",
                             raw_units=None, log_odds_contrast=float(contrast),
                             odds_ratio=float(np.exp(contrast))))
        offset += len(categories)
    return rows


def main():
    warnings.filterwarnings("error", category=ConvergenceWarning)
    X, y, assignment = load_development()
    names = ["dummy_prior", "logistic_unweighted", "logistic_balanced"]
    predictions, fold_metrics, pooled_metrics, coefficients = [], [], [], []
    for name in names:
        oof = np.full(len(X), np.nan)
        for fold in range(1, 6):
            train = np.flatnonzero(assignment.to_numpy() != fold)
            valid = np.flatnonzero(assignment.to_numpy() == fold)
            if set(y.iloc[train]) != {0, 1} or set(y.iloc[valid]) != {0, 1}:
                raise ValueError("Both outcome classes required in each fold.")
            model = make_model(name)
            model.fit(X.iloc[train], y.iloc[train])
            p = model.predict_proba(X.iloc[valid])[:, 1]
            if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
                raise ValueError("Invalid predicted probabilities.")
            oof[valid] = p
            fold_metrics.append(dict(model=name, fold=fold, **metrics(y.iloc[valid], p)))
        if not np.isfinite(oof).all():
            raise ValueError("Missing out-of-fold predictions.")
        pooled_metrics.append(dict(model=name, threshold=0.5, **metrics(y, oof)))
        predictions.extend(dict(model=name, record_id=X.index[i], fold=int(assignment.iloc[i]),
                                target=int(y.iloc[i]), probability=float(oof[i])) for i in range(len(X)))
        if name != "dummy_prior":
            # Descriptive coefficient fit only; not used to estimate performance.
            descriptive = make_model(name).fit(X, y)
            coefficients.extend(coefficient_contrasts(descriptive, name))
    OUT.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(pooled_metrics)
    summary.to_csv(OUT / "oof_metrics.csv", index=False)
    pd.DataFrame(fold_metrics).to_csv(OUT / "fold_metrics.csv", index=False)
    pd.DataFrame(predictions).to_csv(OUT / "oof_predictions.csv", index=False)
    pd.DataFrame(coefficients).to_csv(OUT / "coefficient_contrasts.csv", index=False)
    inputs = ["scripts/day04_baselines.py", "scripts/day03_preprocessing.py",
              "data/raw/processed.cleveland.data", "reports/day01/cleveland_split.csv",
              "reports/day03/development_folds.csv"]
    (OUT / "run_manifest.json").write_text(json.dumps(dict(
        development_n=len(X), locked_test_n=61, holdout_analyzed=False,
        threshold=0.5, threshold_selected=False, hyperparameters_tuned=False,
        logistic_C=1.0, logistic_penalty="l2", folds=5,
        coefficient_fit="full development only; descriptive; no performance estimate",
        python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
        scikit_learn=sklearn.__version__, hashes={p: sha256(ROOT / p) for p in inputs},
    ), indent=2) + "\n", encoding="utf-8")
    print("Development records: 242; CAD positive: 111; CAD negative: 131")
    print(summary.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print("PASS: predictions generated only in held-out development folds.")
    print("Threshold fixed at 0.5; no tuning/calibration; locked test not analyzed.")
    print(f"Outputs saved to: {OUT}")
    print("Day 4 remains open pending local output review, interpretation, and commit.")


FOLDS_SHA256 = "23ebf0bacc878bcca51b2156a6785aa156fa09ff20f22dc271fdde2b6d78bb2d"

if __name__ == "__main__":
    main()
