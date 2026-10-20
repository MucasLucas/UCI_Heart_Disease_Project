"""Nested development selection of model, sigmoid calibration, and threshold."""
import json
import math
import platform
import warnings
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from day03_preprocessing import FEATURES, make_preprocessor
from day04_baselines import load_development, make_model, sha256

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/day06"
TARGET = 0.90
# Fixed before the Day 6 run: no grid expansion from outer scores.
SPECS = [dict(family="logistic", max_depth=None, min_samples_leaf=None)] + [
    dict(family="random_forest", max_depth=depth, min_samples_leaf=leaf)
    for depth in [3, None] for leaf in [3, 8]
]
CANDIDATES = [dict(candidate=f"c{i*2+j:02d}", **spec, calibration=cal)
              for i, spec in enumerate(SPECS) for j, cal in enumerate(["none", "sigmoid"])]
MEMBERSHIPS = []


def splits(X, y, seed, stage):
    groups = pd.util.hash_pandas_object(X, index=False)
    result = list(StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=seed).split(X, y, groups))
    seen = np.zeros(len(X), dtype=int)
    for fold, (train, valid) in enumerate(result, 1):
        if set(groups.iloc[train]) & set(groups.iloc[valid]):
            raise ValueError("Predictor groups crossed a fold boundary.")
        if set(y.iloc[train]) != {0, 1} or set(y.iloc[valid]) != {0, 1}:
            raise ValueError("A training/validation fold lacks an outcome class.")
        seen[valid] += 1
        MEMBERSHIPS.extend(dict(stage=stage, fold=fold, record_id=X.index[i]) for i in valid)
    if not np.all(seen == 1):
        raise ValueError("Incomplete cross-fitting coverage.")
    return result


def base_model(spec):
    if spec["family"] == "logistic":
        return make_model("logistic_unweighted")
    classifier = RandomForestClassifier(
        n_estimators=200, max_features="sqrt", max_depth=spec["max_depth"],
        min_samples_leaf=spec["min_samples_leaf"], class_weight=None,
        random_state=42, n_jobs=1,
    )
    return Pipeline([("preprocess", make_preprocessor()), ("classifier", classifier)])


def fitted(spec, X, y, seed, stage):
    estimator = base_model(spec)
    if spec["calibration"] == "sigmoid":
        # Each calibration OOF score excludes its own label from preprocessing
        # and base fitting. ensemble=False then refits one base pipeline on X.
        cv = splits(X, y, seed, stage + "/calibration")
        estimator = CalibratedClassifierCV(estimator=estimator, method="sigmoid",
                                          cv=cv, ensemble=False, n_jobs=1)
    return estimator.fit(X, y)


def predict(estimator, X):
    p = np.asarray(estimator.predict_proba(X)[:, 1], dtype=np.float64)
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Invalid probabilities.")
    return p


def measures(y, p, threshold):
    labels = np.asarray(p) >= np.asarray(threshold)
    tn, fp, fn, tp = confusion_matrix(y, labels, labels=[0, 1]).ravel()
    return dict(n=len(y), roc_auc=float(roc_auc_score(y, p)),
                average_precision=float(average_precision_score(y, p)),
                brier=float(brier_score_loss(y, p)),
                sensitivity=float(tp / (tp + fn)), specificity=float(tn / (tn + fp)),
                tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp))


def tradeoff(y, p):
    # >= rule and all unique observed score cutoffs, including classify-all-positive.
    p, y = np.asarray(p), np.asarray(y)
    thresholds = np.unique(np.r_[0.0, p, np.nextafter(1.0, 2.0)])
    labels = p[:, None] >= thresholds[None, :]
    tp = labels[y == 1].sum(axis=0)
    fp = labels[y == 0].sum(axis=0)
    fn, tn = (y == 1).sum() - tp, (y == 0).sum() - fp
    return pd.DataFrame(dict(threshold=thresholds, n=len(y),
        sensitivity=tp / (tp + fn), specificity=tn / (tn + fp),
        tp=tp, fp=fp, fn=fn, tn=tn))


def choose(y, predictions):
    records, curves = [], []
    required_tp = math.ceil(TARGET * int(np.asarray(y).sum()) - 1e-12)
    for spec in CANDIDATES:
        key = spec["candidate"]
        curve = tradeoff(y, predictions[key])
        feasible = curve.loc[curve.tp.ge(required_tp)]
        if feasible.empty:
            raise ValueError("No threshold reaches target; review scores and rule.")
        best = feasible.sort_values(["specificity", "threshold"], ascending=[False, False]).iloc[0]
        records.append(dict(candidate=key, threshold=float(best.threshold),
                            **measures(y, predictions[key], float(best.threshold))))
        curves.append(curve.assign(candidate=key))
    table = pd.DataFrame(records)
    # Prefer specificity subject to sensitivity; probability quality breaks ties.
    winner = table.sort_values(["specificity", "brier", "candidate"],
                               ascending=[False, True, True]).iloc[0]
    return winner, table, pd.concat(curves, ignore_index=True)


def inner_predictions(X, y, seed, stage):
    result = {s["candidate"]: np.full(len(X), np.nan) for s in CANDIDATES}
    cv = splits(X, y, seed, stage + "/selection")
    for fold, (train, valid) in enumerate(cv, 1):
        for spec in CANDIDATES:
            est = fitted(spec, X.iloc[train], y.iloc[train], seed + 100 + fold,
                         stage + f"/inner{fold}/{spec['candidate']}")
            result[spec["candidate"]][valid] = predict(est, X.iloc[valid])
    if any(not np.isfinite(p).all() for p in result.values()):
        raise ValueError("Incomplete inner out-of-fold predictions.")
    return result


def calibration_bins(y, p, candidate):
    bins = np.minimum((np.asarray(p) * 5).astype(int), 4)
    rows = []
    for b in range(5):
        mask = bins == b
        rows.append(dict(candidate=candidate, bin=b, n=int(mask.sum()),
                         mean_probability=float(np.mean(p[mask])) if mask.any() else None,
                         observed_fraction=float(np.mean(np.asarray(y)[mask])) if mask.any() else None))
    return rows


def main():
    warnings.filterwarnings("error", category=ConvergenceWarning)
    X, y, outer = load_development()
    predictions = {s["candidate"]: np.full(len(X), np.nan) for s in CANDIDATES}
    policy_p, policy_t = np.full(len(X), np.nan), np.full(len(X), np.nan)
    policy_choices, selected_folds, inner_tables, inner_prediction_rows = [], [], [], []
    for fold in range(1, 6):
        train = np.flatnonzero(outer.to_numpy() != fold)
        valid = np.flatnonzero(outer.to_numpy() == fold)
        print(f"Outer fold {fold}/5: selecting on {len(train)} training records only...", flush=True)
        stage = f"outer{fold}"
        inner = inner_predictions(X.iloc[train], y.iloc[train], 1000 + fold, stage)
        winner, table, _ = choose(y.iloc[train], inner)
        inner_tables.append(table.assign(outer_fold=fold))
        for key, p in inner.items():
            inner_prediction_rows.extend(dict(outer_fold=fold, candidate=key,
                record_id=X.index[train[i]], target=int(y.iloc[train[i]]), probability=float(p[i]))
                for i in range(len(train)))
        policy_choices.append(dict(outer_fold=fold, candidate=winner.candidate,
                                  threshold=float(winner.threshold),
                                  selection_sensitivity=float(winner.sensitivity),
                                  selection_specificity=float(winner.specificity)))
        for spec in CANDIDATES:
            est = fitted(spec, X.iloc[train], y.iloc[train], 2000 + fold,
                         stage + f"/refit/{spec['candidate']}")
            p = predict(est, X.iloc[valid])
            predictions[spec["candidate"]][valid] = p
            if spec["candidate"] == winner.candidate:
                policy_p[valid], policy_t[valid] = p, float(winner.threshold)
                selected_folds.append(dict(outer_fold=fold, candidate=winner.candidate,
                    threshold=float(winner.threshold), **measures(y.iloc[valid], p, float(winner.threshold))))
    if any(not np.isfinite(p).all() for p in list(predictions.values()) + [policy_p, policy_t]):
        raise ValueError("Incomplete outer predictions.")
    # Only after all outer assessment: choose a deployable candidate and cutoff
    # using cross-fitted full-development scores. These selection scores are not
    # a fresh performance estimate of the selected winner.
    winner, selection, curves = choose(y, predictions)
    final_spec = next(s for s in CANDIDATES if s["candidate"] == winner.candidate)
    print(f"Fitting review candidate {winner.candidate} on all 242 development records...", flush=True)
    final_model = fitted(final_spec, X, y, 3000, "final")
    OUT.mkdir(parents=True, exist_ok=True)
    models = ROOT / "models"
    models.mkdir(parents=True, exist_ok=True)
    model_path = models / "day06_candidate.joblib"
    joblib.dump(dict(model=final_model, threshold=float(winner.threshold),
                    features=FEATURES, specification=final_spec), model_path)
    row_predictions, bins = [], []
    for key, p in predictions.items():
        row_predictions.extend(dict(candidate=key, record_id=X.index[i], outer_fold=int(outer.iloc[i]),
                                    target=int(y.iloc[i]), probability=float(p[i])) for i in range(len(X)))
        bins.extend(calibration_bins(y, p, key))
    policy = pd.DataFrame(dict(record_id=X.index, outer_fold=outer.to_numpy(),
                              target=y.to_numpy(), probability=policy_p, threshold=policy_t))
    metrics = pd.DataFrame([dict(analysis="nested_selection_policy", **measures(y, policy_p, policy_t))])
    diagnostics = pd.DataFrame([dict(candidate=k, threshold=0.5, **measures(y, p, 0.5))
                                for k, p in predictions.items()])
    tables = {"candidate_specifications.csv": pd.DataFrame(CANDIDATES),
              "candidate_oof_predictions.csv": pd.DataFrame(row_predictions),
              "candidate_oof_metrics_at_05.csv": diagnostics,
              "inner_oof_predictions.csv": pd.DataFrame(inner_prediction_rows),
              "inner_selection_metrics.csv": pd.concat(inner_tables, ignore_index=True),
              "outer_selection.csv": pd.DataFrame(policy_choices),
              "policy_oof_predictions.csv": policy, "policy_oof_metrics.csv": metrics,
              "policy_fold_metrics.csv": pd.DataFrame(selected_folds),
              "final_selection_metrics.csv": selection, "threshold_tradeoff.csv": curves,
              "calibration_bins.csv": pd.DataFrame(bins),
              "validation_membership.csv": pd.DataFrame(MEMBERSHIPS)}
    for name, table in tables.items():
        table.to_csv(OUT / name, index=False)
    spec = dict(status="candidate_pending_local_review_not_accepted_freeze",
                selected=final_spec, threshold=float(winner.threshold), decision_rule="probability >= threshold",
                selection_sensitivity=float(winner.sensitivity), selection_specificity=float(winner.specificity),
                selection_scores_are_not_independent_performance=True, sensitivity_target=TARGET,
                selection_rule="sensitivity >= 0.90, maximize specificity, tie: lower Brier then candidate ID",
                within_candidate_threshold_tie="highest threshold at maximum feasible specificity",
                features=FEATURES, development_n=242, locked_test_n=61, holdout_analyzed=False,
                model_path="models/day06_candidate.joblib", model_sha256=sha256(model_path))
    (OUT / "candidate_freeze.json").write_text(json.dumps(spec, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    inputs = ["scripts/day03_preprocessing.py", "scripts/day04_baselines.py", "scripts/day06_calibration.py",
              "reports/day01/cleveland_split.csv", "reports/day03/development_folds.csv",
              "data/raw/processed.cleveland.data"]
    manifest = dict(python=platform.python_version(), scikit_learn=sklearn.__version__,
        pandas=pd.__version__, numpy=np.__version__, joblib=joblib.__version__,
        candidates=CANDIDATES, outer_folds=5, selection_folds=3, calibration_folds=3,
        calibration_method="sigmoid; ensemble=False; complete pipeline inside each calibration fit",
        calibration_score="estimator decision_function when available, otherwise predict_proba",
        holdout_analyzed=False, cross_site_evaluated=False,
        hashes={p:sha256(ROOT / p) for p in inputs},
        limitations="Day 5 informed shortlist; reused development folds are not fresh confirmation.")
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    b = pd.DataFrame(bins)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    # Four curves: logistic pair and the final selected base model's pair.
    pair_index = int(winner.candidate[1:]) // 2
    keys = sorted(set(["c00", "c01", f"c{pair_index*2:02d}", f"c{pair_index*2+1:02d}"]))
    for key in keys:
        part = b.loc[b.candidate.eq(key) & b.n.gt(0)]
        axes[0].plot(part.mean_probability, part.observed_fraction, marker="o", label=key)
    axes[0].plot([0,1],[0,1],"k--",linewidth=1)
    axes[0].set(xlabel="Mean predicted probability", ylabel="Observed CAD fraction",
                title="Development outer-validation calibration", xlim=(0,1), ylim=(0,1))
    axes[0].legend()
    curve = curves.loc[curves.candidate.eq(winner.candidate) & curves.threshold.le(1)].sort_values("threshold")
    axes[1].plot(curve.threshold, curve.sensitivity, label="Sensitivity")
    axes[1].plot(curve.threshold, curve.specificity, label="Specificity")
    axes[1].axhline(TARGET, color="k", linestyle="--", linewidth=1)
    axes[1].axvline(winner.threshold, color="grey", linestyle=":")
    axes[1].set(xlabel="Threshold", ylabel="Fraction", title="Final candidate selection tradeoff", ylim=(0,1))
    axes[1].legend()
    fig.tight_layout(); fig.savefig(OUT/"calibration_threshold.png", dpi=160); plt.close(fig)
    print("Nested selection-policy outer-validation metrics:")
    print(metrics.to_string(index=False, float_format=lambda v:f"{v:.4f}"))
    print("Final review candidate (selection scores, not independent performance):")
    print(json.dumps(spec, indent=2))
    print("PASS: calibration and threshold selection stayed inside outer training partitions.")
    print("Locked test not analyzed. Keep candidate bundle locally; do not evaluate test yet.")
    print("Day 6 remains open pending local review and accepted freeze documentation.")


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
