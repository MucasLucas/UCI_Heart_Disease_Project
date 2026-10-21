"""Read-only explanation of the frozen forest and development-policy subgroup audit."""
import hashlib
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
import shap
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.metrics import brier_score_loss, confusion_matrix, roc_auc_score
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from day03_preprocessing import CATEGORICAL, FEATURES, NUMERIC
from day04_baselines import load_development, sha256

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/day07"
EXPECTED_MODEL_SHA256 = "948f8939076cdc1e001a74d7bb414b28c88e21b7de32b0a2172fdc4a805ce1ae"
EXPECTED_POLICY_SHA256_LF = "459a4318694c7c6f6c6ec259e5e4126f501a823757138aa692eb008e7e652718"
FROZEN_THRESHOLD = 0.3528716233973672


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def wilson(successes, total):
    """Descriptive Wilson 95% limits; undefined when the denominator is zero."""
    if total == 0:
        return float("nan"), float("nan")
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total)) / denominator
    radius = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / denominator
    lower = 0.0 if successes == 0 else max(0.0, center-radius)
    upper = 1.0 if successes == total else min(1.0, center+radius)
    return lower, upper


def verified_policy(X, y, outer):
    path = ROOT / "reports/day06/policy_oof_predictions.csv"
    canonical = path.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(canonical).hexdigest() != EXPECTED_POLICY_SHA256_LF:
        raise ValueError("Day 6 policy predictions differ from the reviewed version.")
    p = pd.read_csv(path)
    if p.record_id.duplicated().any() or set(p.record_id) != set(X.index):
        raise ValueError("Policy IDs differ from the development cohort.")
    p = p.set_index("record_id").loc[X.index]
    if not np.array_equal(p.target, y) or not np.array_equal(p.outer_fold, outer):
        raise ValueError("Policy outcomes/folds differ from frozen development data.")
    if not np.isfinite(p[["probability", "threshold"]].to_numpy()).all():
        raise ValueError("Nonfinite policy scores/cutoffs.")
    if not p.probability.between(0, 1).all() or not p.threshold.between(0, 1).all():
        raise ValueError("Policy score/cutoff outside [0,1].")
    return p


def validate_bundle(bundle, freeze):
    if list(bundle["features"]) != FEATURES or freeze["features"] != FEATURES:
        raise ValueError("Frozen feature list changed.")
    if bundle["threshold"] != FROZEN_THRESHOLD or freeze["threshold"] != FROZEN_THRESHOLD:
        raise ValueError("Frozen threshold changed.")
    if bundle["specification"] != freeze["selected"]:
        raise ValueError("Bundle and accepted specification differ.")
    model = bundle["model"]
    if not isinstance(model, Pipeline) or not isinstance(model.named_steps.get("classifier"), RandomForestClassifier):
        raise ValueError("Expected the frozen uncalibrated forest pipeline.")
    if freeze["selected"]["candidate"] != "c06" or freeze["selected"]["calibration"] != "none":
        raise ValueError("Unexpected accepted model; this procedure targets c06.")
    classifier = model.named_steps["classifier"]
    for key, expected in freeze["model_parameters"].items():
        if classifier.get_params().get(key) != expected:
            raise ValueError(f"Frozen model parameter changed: {key}")
    if not np.array_equal(classifier.classes_, [0, 1]):
        raise ValueError("Unexpected class order.")
    return model


def subgroup_table(X, y, policy):
    """Use held-out policy predictions, not full-fit model training accuracy."""
    groups = [("overall", "all", np.ones(len(X), dtype=bool)),
              ("recorded_sex", "sex=0", X.sex.eq(0).to_numpy()),
              ("recorded_sex", "sex=1", X.sex.eq(1).to_numpy()),
              ("age", "age <50", X.age.lt(50).to_numpy()),
              ("age", "age 50-59", X.age.ge(50).to_numpy() & X.age.lt(60).to_numpy()),
              ("age", "age 60+", X.age.ge(60).to_numpy())]
    rows = []
    for dimension, label, mask in groups:
        yy = np.asarray(y)[mask]
        p = policy.probability.to_numpy()[mask]
        decision = p >= policy.threshold.to_numpy()[mask]
        tn, fp, fn, tp = confusion_matrix(yy, decision, labels=[0,1]).ravel()
        positives, negatives = int(tp+fn), int(tn+fp)
        sl, su = wilson(int(tp), positives)
        cl, cu = wilson(int(tn), negatives)
        rows.append(dict(analysis="development_oof_selection_policy", dimension=dimension, subgroup=label,
            n=int(mask.sum()), positive_n=positives, negative_n=negatives,
            tp=int(tp), fn=int(fn), tn=int(tn), fp=int(fp),
            sensitivity=tp/positives if positives else np.nan,
            sensitivity_wilson_lower=sl, sensitivity_wilson_upper=su,
            specificity=tn/negatives if negatives else np.nan,
            specificity_wilson_lower=cl, specificity_wilson_upper=cu,
            roc_auc=roc_auc_score(yy,p) if positives and negatives else np.nan,
            brier=brier_score_loss(yy,p) if len(yy) else np.nan,
            sparse_denominator=bool(min(positives,negatives)<20)))
    return pd.DataFrame(rows)


def explain_and_audit(bundle, freeze, X, y, policy, out):
    model = validate_bundle(bundle, freeze)
    preprocessing, forest = model.named_steps["preprocess"], model.named_steps["classifier"]
    # transform only: no preprocessing/classifier/calibrator fit calls.
    # sklearn forests evaluate float32 inputs internally. Match that precision
    # so values near split thresholds follow identical paths in Tree SHAP.
    transformed = np.asarray(preprocessing.transform(X), dtype=np.float32)
    probability = np.asarray(model.predict_proba(X)[:,1], dtype=np.float64)
    if not np.isfinite(transformed).all() or not np.isfinite(probability).all():
        raise ValueError("Nonfinite frozen model inputs/outputs.")
    # For sklearn RandomForestClassifier the native ('raw') output is class
    # probability, not log-odds. Use development-training path counts stored in
    # the trees; enforce reconstruction against the actual pipeline below.
    explainer = shap.TreeExplainer(forest,
        feature_perturbation="tree_path_dependent", model_output="raw")
    raw = explainer.shap_values(transformed, check_additivity=True)
    if isinstance(raw, list):
        encoded = np.asarray(raw[1])
    else:
        raw = np.asarray(raw)
        if raw.shape != (len(X), transformed.shape[1], 2):
            raise ValueError(f"Unexpected binary SHAP shape: {raw.shape}")
        encoded = raw[:,:,1]
    baseline = float(np.asarray(explainer.expected_value)[1])
    error = float(np.max(np.abs(baseline + encoded.sum(axis=1) - probability)))
    if not np.isfinite(encoded).all() or error > 1e-5:
        raise ValueError(f"SHAP additivity check failed: {error}")
    # Sum encoded columns belonging to the same original input. This retains
    # additivity; it is not a recomputation of grouped-coalition Shapley values.
    grouped = np.zeros((len(X),len(FEATURES)))
    mapping = []
    names = preprocessing.get_feature_names_out()
    offset = 0
    for feature in NUMERIC:
        grouped[:,FEATURES.index(feature)] = encoded[:,offset]
        mapping.append(dict(encoded_feature=names[offset], original_feature=feature))
        offset += 1
    categories = preprocessing.named_transformers_["categorical"].named_steps["encode"].categories_
    for feature, levels in zip(CATEGORICAL,categories):
        width = len(levels)
        grouped[:,FEATURES.index(feature)] = encoded[:,offset:offset+width].sum(axis=1)
        mapping.extend(dict(encoded_feature=names[i], original_feature=feature) for i in range(offset,offset+width))
        offset += width
    if offset != encoded.shape[1] or not np.allclose(grouped.sum(axis=1),encoded.sum(axis=1),atol=1e-12):
        raise ValueError("Encoded-to-original SHAP mapping failed.")
    ranking = pd.DataFrame(dict(feature=FEATURES, mean_abs_grouped_shap=np.abs(grouped).mean(axis=0)))
    ranking = ranking.sort_values("mean_abs_grouped_shap",ascending=False).reset_index(drop=True)
    case_ids = sorted(X.index)[:3]  # Fixed by ID, without selecting outcomes or errors.
    local = []
    for record_id in case_ids:
        i = X.index.get_loc(record_id)
        for j,feature in enumerate(FEATURES):
            local.append(dict(record_id=record_id, feature=feature, raw_value=X.iloc[i][feature],
                              shap_probability_contribution=grouped[i,j]))
    model_rows = pd.DataFrame(dict(record_id=X.index, model_probability=probability,
        baseline_probability=baseline, sum_shap=grouped.sum(axis=1),
        reconstructed_probability=baseline+grouped.sum(axis=1),
        threshold=FROZEN_THRESHOLD, predicted_class=(probability>=FROZEN_THRESHOLD).astype(int),
        role="descriptive_frozen_model_on_training_records_not_validation"))
    subgroup = subgroup_table(X,y,policy)
    out.mkdir(parents=True,exist_ok=True)
    encoded_df = pd.DataFrame(encoded,index=X.index,columns=names).rename_axis("record_id").reset_index()
    grouped_df = pd.DataFrame(grouped,index=X.index,columns=FEATURES).rename_axis("record_id").reset_index()
    tables = {"global_shap.csv":ranking, "local_explanations.csv":pd.DataFrame(local),
        "shap_encoded.csv":encoded_df, "shap_grouped.csv":grouped_df,
        "feature_mapping.csv":pd.DataFrame(mapping), "model_explanation_predictions.csv":model_rows,
        "background_ids.csv":pd.DataFrame(dict(record_id=X.index,
            role="development_source_cohort_for_fitted_tree_path_counts")),
        "subgroup_metrics.csv":subgroup}
    for name,table in tables.items(): table.to_csv(out/name,index=False)
    fig,ax = plt.subplots(figsize=(8,5))
    r = ranking.iloc[::-1]
    ax.barh(r.feature,r.mean_abs_grouped_shap,color="#216b82")
    ax.set(xlabel="Mean absolute summed SHAP contribution (probability units)",
           title="Frozen model: development records only")
    fig.tight_layout();fig.savefig(out/"global_shap.png",dpi=160);plt.close(fig)
    fig,axes = plt.subplots(1,3,figsize=(15,5),sharex=True)
    for ax,record_id in zip(axes,case_ids):
        i=X.index.get_loc(record_id);order=np.argsort(np.abs(grouped[i]))
        values=grouped[i,order]
        ax.barh(np.array(FEATURES)[order],values,color=np.where(values>=0,"#b84a48","#216b82"))
        ax.axvline(0,color="black",linewidth=.7)
        ax.set(title=f"{record_id}\np={probability[i]:.3f}; baseline={baseline:.3f}",
               xlabel="Contribution to CAD probability")
    fig.suptitle("Descriptive development examples; not causal explanations")
    fig.tight_layout();fig.savefig(out/"local_shap.png",dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4.5),sharey=True)
    labels=[f"{r.subgroup} (n={r.n})" for r in subgroup.itertuples()]
    for ax,metric,title in zip(axes,["sensitivity","specificity"],["Sensitivity","Specificity"]):
        for i,r in enumerate(subgroup.to_dict("records")):
            value=r[metric]
            if np.isfinite(value):
                ax.errorbar(value,i,xerr=[[value-r[metric+"_wilson_lower"]],
                    [r[metric+"_wilson_upper"]-value]],fmt="o",color="#216b82",capsize=3)
        ax.set(xlim=(0,1),xlabel=title)
        ax.set_yticks(range(len(labels)),labels)
        ax.grid(axis="x",alpha=.2)
    axes[0].invert_yaxis()
    fig.suptitle("Development OOF policy: descriptive 95% Wilson intervals")
    fig.tight_layout();fig.savefig(out/"subgroup_intervals.png",dpi=160);plt.close(fig)
    if not np.array_equal(model.predict_proba(X)[:,1],probability):
        raise ValueError("Frozen predictions changed during explanation.")
    return dict(additivity_max_abs_error=error, background_source_cohort_n=len(X),
                local_case_ids=case_ids, top_features=ranking.feature.head(5).tolist(),
                subgroup_rows=len(subgroup), development_n=len(X))


def main():
    warnings.filterwarnings("error",category=InconsistentVersionWarning)
    freeze_path = ROOT/"reports/day06/accepted_freeze.json"
    freeze=read_json(freeze_path)
    if freeze["status"] != "accepted_for_project_evaluation" or freeze["model_sha256"] != EXPECTED_MODEL_SHA256:
        raise ValueError("Accepted freeze differs from the reviewed local model identity.")
    model_path=ROOT/"models/day06_candidate.joblib"
    if sha256(model_path) != EXPECTED_MODEL_SHA256:
        raise ValueError("Frozen bundle checksum mismatch. Stop; do not refit or change the hash.")
    day6=read_json(ROOT/"reports/day06/run_manifest.json")
    versions=dict(scikit_learn=sklearn.__version__,numpy=np.__version__,pandas=pd.__version__,joblib=joblib.__version__)
    mismatches={k:dict(current=v,frozen=day6[k]) for k,v in versions.items() if day6[k]!=v}
    if mismatches:
        raise ValueError(f"Restore the Day 6 model environment before loading; do not refit: {mismatches}")
    X,y,outer=load_development()
    policy=verified_policy(X,y,outer)
    print("PASS: accepted local model SHA-256 and environment verified before loading.",flush=True)
    bundle=joblib.load(model_path)
    checks=explain_and_audit(bundle,freeze,X,y,policy,OUT)
    if sha256(model_path) != EXPECTED_MODEL_SHA256:
        raise ValueError("Frozen artifact changed during analysis.")
    inputs=["scripts/day07_explanations.py","scripts/day03_preprocessing.py","scripts/day04_baselines.py",
            "reports/day06/accepted_freeze.json","reports/day06/run_manifest.json",
            "reports/day06/policy_oof_predictions.csv","reports/day01/cleveland_split.csv",
            "reports/day03/development_folds.csv","data/raw/processed.cleveland.data"]
    manifest=dict(**checks,python=platform.python_version(),shap=shap.__version__,**versions,
        frozen_model_sha256=EXPECTED_MODEL_SHA256,threshold=FROZEN_THRESHOLD,
        model_refitted=False,threshold_changed=False,holdout_analyzed=False,
        shap_output="class 1 probability (native raw output of sklearn forest)",
        feature_perturbation="tree_path_dependent",
        background_selection="implicit fitted-tree training path counts; source cohort is development only",
        aggregation="sum encoded contributions per original input; not grouped-coalition SHAP",
        explanation_cohort="frozen full-fit model on development training records; descriptive",
        subgroup_prediction_source="Day 6 nested selection-policy OOF scores and fold-specific cutoffs",
        age_bands=["<50","50-59","60+"],subgroup_interval="Wilson 95%; descriptive; excludes fitting/selection uncertainty",
        hashes={p:sha256(ROOT/p) for p in inputs})
    (OUT/"run_manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Top grouped explanation features:",", ".join(checks["top_features"]))
    print(pd.read_csv(OUT/"subgroup_metrics.csv").to_string(index=False,float_format=lambda v:f"{v:.4f}"))
    print(f"PASS: SHAP sums reconstruct probabilities (max error {checks['additivity_max_abs_error']:.3g}).")
    print("Frozen model and cutoff unchanged. Locked test not analyzed.")
    print(f"Outputs saved to: {OUT}")
    print("Day 7 remains open pending local output review, interpretation, and commit.")


if __name__=="__main__":
    with threadpool_limits(limits=1):
        main()
