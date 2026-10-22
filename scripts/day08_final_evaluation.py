"""Final frozen-model evaluation: locked Cleveland test and separate external sites."""
import json
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
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, precision_recall_curve, roc_auc_score, roc_curve
from threadpoolctl import threadpool_limits

from day03_preprocessing import COLUMNS, DOMAINS, FEATURES
from day04_baselines import load_development, sha256
from frozen_artifact import EXPECTED_MODEL_SHA256, FROZEN_THRESHOLD, read_json, validate_bundle, wilson

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/day08"
SOURCES = {"cleveland": ("processed.cleveland.data",303),
           "hungarian": ("processed.hungarian.data",294),
           "switzerland": ("processed.switzerland.data",123),
           "va": ("processed.va.data",200)}
BOOTSTRAPS = 2000
AGE_BANDS = [("age <50",0,50),("age 50-59",50,60),("age 60+",60,float("inf"))]


def predictor_keys(frame):
    # Exact primary-predictor matching with missing values treated consistently.
    # Hashes are used as a documented record-similarity heuristic, not patient IDs.
    return pd.util.hash_pandas_object(frame[FEATURES].astype(float),index=False)


def read_source(path,site,expected_n):
    frame=pd.read_csv(path,header=None,na_values="?",index_col=False)
    if frame.shape!=(expected_n,14):
        raise ValueError(f"Unexpected source shape for {site}: {frame.shape}")
    frame.columns=COLUMNS
    frame=frame.apply(pd.to_numeric,errors="raise")
    if not frame.num.isin([0,1,2,3,4]).all():
        raise ValueError(f"Invalid outcome in {site}")
    for feature,domain in DOMAINS.items():
        if not frame[feature].dropna().isin(domain).all():
            raise ValueError(f"Unexpected category {feature} in {site}")
    values=frame[FEATURES].to_numpy(dtype=float)
    if not np.isfinite(values[~np.isnan(values)]).all():
        raise ValueError(f"Nonfinite predictors in {site}")
    frame.index=[f"{site}:{i:04d}" for i in range(len(frame))]
    return frame


def prepare_cohorts(raw,split):
    cleveland=raw["cleveland"]
    if set(cleveland.index)!=set(split.record_id):
        raise ValueError("Cleveland IDs differ from frozen split")
    dev_ids=split.loc[split.partition.eq("development"),"record_id"]
    test_ids=split.loc[split.partition.eq("locked_test"),"record_id"]
    if len(dev_ids)!=242 or len(test_ids)!=61:
        raise ValueError("Expected 242 development / 61 locked test records")
    development_keys=set(predictor_keys(cleveland.loc[dev_ids]))
    test_keys=set(predictor_keys(cleveland.loc[test_ids]))
    if development_keys & test_keys:
        raise ValueError("Primary predictor matches cross internal development/test split; stop for review")
    cleveland_keys=set(predictor_keys(cleveland))
    cohorts={"cleveland_test":cleveland.loc[test_ids].copy()}
    exclusions=[]
    audits=[]
    for site in ["hungarian","switzerland","va"]:
        frame=raw[site]
        duplicate=frame.duplicated(keep="first")
        overlap=predictor_keys(frame).isin(cleveland_keys)
        for record_id in frame.index[duplicate|overlap]:
            reasons=[]
            if duplicate.loc[record_id]:reasons.append("exact_full_source_row_duplicate_keep_first")
            if overlap.loc[record_id]:reasons.append("primary_predictors_match_any_cleveland_record")
            exclusions.append(dict(site=site,record_id=record_id,reason=";".join(reasons)))
        cohorts[site]=frame.loc[~(duplicate|overlap)].copy()
        audits.append(dict(site=site,source_n=len(frame),partition_not_evaluated_n=0,duplicate_source_rows_n=int(duplicate.sum()),
                           primary_overlap_cleveland_n=int(overlap.sum()),excluded_n=int((duplicate|overlap).sum()),
                           evaluation_n=len(cohorts[site])))
    audits.insert(0,dict(site="cleveland_test",source_n=len(cleveland),partition_not_evaluated_n=242,duplicate_source_rows_n=0,
                        primary_overlap_cleveland_n=0,excluded_n=0,evaluation_n=61))
    cleaning=[]
    for site,frame in cohorts.items():
        if len(frame)==0:raise ValueError(f"Empty evaluation cohort: {site}")
        # Only these audited impossible zero physiology values become missing.
        # No site-specific means/modes or other fitted transformations are learned.
        for feature in FEATURES:
            zero_mask=frame[feature].eq(0) if feature in ["chol","trestbps"] and site!="cleveland_test" else pd.Series(False,index=frame.index)
            old_missing=int(frame[feature].isna().sum())
            frame.loc[zero_mask,feature]=np.nan
            cleaning.append(dict(site=site,feature=feature,missing_before_zero_rule=old_missing,
                                 zeros_to_missing_n=int(zero_mask.sum()),missing_before_frozen_imputation=int(frame[feature].isna().sum()),
                                 retained_nonmissing_min=float(frame[feature].min()) if frame[feature].notna().any() else np.nan,
                                 retained_nonmissing_max=float(frame[feature].max()) if frame[feature].notna().any() else np.nan,
                                 evaluation_n=len(frame)))
        # Finite oldpeak values are retained as supplied, including external
        # negative measurements; do not delete an extreme because it is outside
        # the Cleveland training range.
        if frame[["age","trestbps","chol","thalach"]].le(0).any().any():
            raise ValueError(f"Unresolved invalid physiology in {site}; no silent row deletion")
    return cohorts,pd.DataFrame(audits),pd.DataFrame(exclusions,columns=["site","record_id","reason"]),pd.DataFrame(cleaning)


def safe_ratio(a,b):
    return float(a/b) if b else np.nan


def point_metrics(y,p,threshold=FROZEN_THRESHOLD):
    y,p=np.asarray(y,dtype=int),np.asarray(p,dtype=float)
    if len(y)==0:raise ValueError("Metrics require at least one observation")
    decision=p>=threshold
    tn,fp,fn,tp=confusion_matrix(y,decision,labels=[0,1]).ravel()
    positives,negatives=int(tp+fn),int(tn+fp)
    row=dict(n=len(y),positive_n=positives,negative_n=negatives,prevalence=float(y.mean()),threshold=float(threshold),
        tp=int(tp),fn=int(fn),tn=int(tn),fp=int(fp),sensitivity=safe_ratio(tp,positives),specificity=safe_ratio(tn,negatives),
        precision=safe_ratio(tp,tp+fp),npv=safe_ratio(tn,tn+fn),false_positive_fraction=float(fp/len(y)),
        false_negative_fraction=float(fn/len(y)),roc_auc=float(roc_auc_score(y,p)) if positives and negatives else np.nan,
        average_precision=float(average_precision_score(y,p)) if positives and negatives else np.nan,
        brier=float(brier_score_loss(y,p)))
    for metric,a,b in [("sensitivity",tp,positives),("specificity",tn,negatives),
                        ("precision",tp,tp+fp),("npv",tn,tn+fn)]:
        lower,upper=wilson(int(a),int(b));row[metric+"_lower"],row[metric+"_upper"]=lower,upper
    return row


def bootstrap_metrics(y,p,seed,repeats=BOOTSTRAPS):
    y,p=np.asarray(y),np.asarray(p)
    rng=np.random.default_rng(seed)
    values={key:[] for key in ["roc_auc","average_precision","brier"]}
    both_classes=bool(len(np.unique(y))==2)
    for _ in range(repeats):
        idx=rng.integers(0,len(y),size=len(y));yy,pp=y[idx],p[idx]
        values["brier"].append(float(np.mean((yy-pp)**2)))
        if both_classes and len(np.unique(yy))==2:
            values["roc_auc"].append(float(roc_auc_score(yy,pp)))
            values["average_precision"].append(float(average_precision_score(yy,pp)))
    result={}
    for key,array in values.items():
        result[key+"_bootstrap_valid_n"]=len(array)
        low,high=np.quantile(array,[.025,.975]) if array else (np.nan,np.nan)
        result[key+"_lower"],result[key+"_upper"]=float(low),float(high)
    return result


def subgroup_rows(site,frame,p):
    masks=[("overall","all",np.ones(len(frame),dtype=bool)),
           ("recorded_sex","sex=0",frame.sex.eq(0).to_numpy()),
           ("recorded_sex","sex=1",frame.sex.eq(1).to_numpy())]
    masks += [("age",label,frame.age.ge(lo).to_numpy() & frame.age.lt(hi).to_numpy()) for label,lo,hi in AGE_BANDS]
    if frame.sex.isna().any():masks.append(("recorded_sex","sex missing",frame.sex.isna().to_numpy()))
    if frame.age.isna().any():masks.append(("age","age missing",frame.age.isna().to_numpy()))
    rows=[]
    for dimension,label,mask in masks:
        if not mask.any():
            rows.append(dict(site=site,dimension=dimension,subgroup=label,n=0,positive_n=0,negative_n=0,sparse_denominator=True))
            continue
        y=frame.num.gt(0).astype(int).to_numpy()[mask]
        row=point_metrics(y,p[mask])
        rows.append(dict(site=site,dimension=dimension,subgroup=label,**row,
                         sparse_denominator=bool(min(row["positive_n"],row["negative_n"])<20)))
    return rows


def curve_tables(site,y,p):
    curves=[];bins=[]
    if len(np.unique(y))==2:
        fpr,tpr,thresholds=roc_curve(y,p)
        curves.extend(dict(site=site,curve="ROC",x=float(a),y=float(b),threshold=float(c)) for a,b,c in zip(fpr,tpr,thresholds))
        precision,recall,thresholds=precision_recall_curve(y,p)
        curves.extend(dict(site=site,curve="PR",x=float(a),y=float(b),threshold=float(c))
                      for a,b,c in zip(recall,precision,np.r_[thresholds,np.nan]))
    assignments=np.minimum((p*5).astype(int),4)
    for i in range(5):
        mask=assignments==i
        bins.append(dict(site=site,bin=i,n=int(mask.sum()),
                         mean_probability=float(p[mask].mean()) if mask.any() else np.nan,
                         observed_fraction=float(y[mask].mean()) if mask.any() else np.nan))
    return curves,bins


def plots(predictions,metrics,curves,bins,out):
    sites=list(predictions.site.unique())
    colors=dict(zip(sites,["#216b82","#a34d47","#735393","#59834b"]))
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for site in sites:
        row=metrics.loc[metrics.site.eq(site)].iloc[0]
        for ax,kind,key in [(axes[0],"ROC","roc_auc"),(axes[1],"PR","average_precision")]:
            part=curves.loc[curves.site.eq(site)&curves.curve.eq(kind)]
            if len(part):ax.plot(part.x,part.y,color=colors[site],label=f"{site}: {key}={row[key]:.3f}")
        axes[1].axhline(row.prevalence,color=colors[site],linestyle=":",alpha=.5)
    axes[0].plot([0,1],[0,1],"k--",linewidth=1)
    axes[0].set(xlabel="False-positive rate",ylabel="Sensitivity",title="Frozen model ROC")
    axes[1].set(xlabel="Recall / sensitivity",ylabel="Precision",title="PR curves; dotted lines show site prevalence")
    for ax in axes:ax.set_xlim(0,1);ax.set_ylim(0,1.02);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(out/"roc_pr.png",dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(10,9))
    for ax,site in zip(axes.flat,sites):
        part=bins.loc[bins.site.eq(site)&bins.n.gt(0)]
        ax.plot(part.mean_probability,part.observed_fraction,"o-",color=colors[site])
        for r in part.itertuples():ax.annotate(f"n={r.n}",(r.mean_probability,r.observed_fraction),xytext=(3,4),textcoords="offset points",fontsize=8)
        ax.plot([0,1],[0,1],"k--",linewidth=1)
        ax.set(xlabel="Mean predicted probability",ylabel="Observed CAD fraction",title=site,xlim=(0,1),ylim=(0,1.08))
    fig.suptitle("Frozen model calibration: five fixed bins; no recalibration")
    fig.tight_layout();fig.savefig(out/"calibration.png",dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(13,4.5),sharey=True)
    for ax,key,title in zip(axes,["roc_auc","sensitivity","specificity"],["ROC-AUC","Sensitivity","Specificity"]):
        for i,site in enumerate(sites):
            r=metrics.loc[metrics.site.eq(site)].iloc[0]
            v,lo,hi=r[key],r[key+"_lower"],r[key+"_upper"]
            if np.isfinite([v,lo,hi]).all():
                # Percentile bootstrap intervals need not contain the point estimate.
                ax.hlines(i,lo,hi,color=colors[site],linewidth=2)
                ax.plot(v,i,"o",color=colors[site])
        ax.set(xlim=(0,1),xlabel=title)
        ax.set_yticks(range(len(sites)),[f"{s} (n={int(metrics.loc[metrics.site.eq(s),'n'].iloc[0])})" for s in sites])
        ax.grid(axis="x",alpha=.2)
    axes[0].invert_yaxis();fig.suptitle("Final evaluation: descriptive 95% intervals")
    fig.tight_layout();fig.savefig(out/"site_comparison.png",dpi=160);plt.close(fig)


def main():
    warnings.filterwarnings("error",category=InconsistentVersionWarning)
    freeze=read_json(ROOT/"reports/day06/accepted_freeze.json")
    if freeze["status"]!="accepted_for_project_evaluation" or freeze["model_sha256"]!=EXPECTED_MODEL_SHA256 or freeze["threshold"]!=FROZEN_THRESHOLD:
        raise ValueError("Accepted model/cutoff differs from reviewed freeze")
    model_path=ROOT/"models/day06_candidate.joblib"
    if sha256(model_path)!=EXPECTED_MODEL_SHA256:raise ValueError("Frozen artifact hash mismatch; stop without refitting")
    expected=read_json(ROOT/"reports/day06/run_manifest.json")
    versions=dict(scikit_learn=sklearn.__version__,numpy=np.__version__,pandas=pd.__version__,joblib=joblib.__version__)
    mismatch={k:dict(current=v,frozen=expected[k]) for k,v in versions.items() if v!=expected[k]}
    if mismatch:raise ValueError(f"Restore the Day 6 environment, not the model: {mismatch}")
    audit=read_json(ROOT/"reports/day01/manifest.json")
    paths=[ROOT/"data/raw"/name for name,_ in SOURCES.values()]
    missing=[str(p) for p in paths if not p.exists()]
    if missing:raise FileNotFoundError(f"All four unchanged source files are required before evaluation: {missing}")
    source_hashes={p.name:sha256(p) for p in paths}
    for name,value in source_hashes.items():
        if value!=audit["source_manifest"][name]["sha256"]:raise ValueError(f"Source hash changed: {name}")
    # Reuse the established split-integrity validation; no refitting occurs.
    load_development()
    dependency_hashes={p:sha256(ROOT/p) for p in ["scripts/frozen_artifact.py","scripts/day03_preprocessing.py","scripts/day04_baselines.py"]}
    if (OUT/"run_manifest.json").exists():
        prior=read_json(OUT/"run_manifest.json")
        if prior["model_sha256"]!=EXPECTED_MODEL_SHA256 or prior["threshold"]!=FROZEN_THRESHOLD or prior["source_sha256"]!=source_hashes or prior["script_sha256"]!=sha256(Path(__file__)) or prior["dependency_sha256"]!=dependency_hashes:
            raise ValueError("Existing final evaluation has different inputs/code; preserve it for review, do not overwrite")
        for name,value in prior["output_sha256"].items():
            if sha256(OUT/name)!=value:raise ValueError(f"Existing evaluation output changed: {name}")
        print("Existing verified final evaluation reused; no new predictions generated.")
        print(pd.read_csv(OUT/"site_metrics.csv").to_string(index=False));return
    raw={site:read_source(ROOT/"data/raw"/name,site,n) for site,(name,n) in SOURCES.items()}
    split=pd.read_csv(ROOT/"reports/day01/cleveland_split.csv")
    cohorts,cohort_audit,excluded,cleaning=prepare_cohorts(raw,split)
    model=validate_bundle(joblib.load(model_path),freeze)
    all_predictions=[];metric_rows=[];subgroups=[];curve_rows=[];bin_rows=[]
    for i,(site,frame) in enumerate(cohorts.items()):
        print(f"Evaluating {site}: {len(frame)} records with frozen cutoff...",flush=True)
        X=frame[FEATURES];y=frame.num.gt(0).astype(int).to_numpy()
        p=np.asarray(model.predict_proba(X)[:,1],dtype=float)
        if not np.isfinite(p).all() or ((p<0)|(p>1)).any():raise ValueError(f"Invalid model output in {site}")
        metric_rows.append(dict(site=site,**point_metrics(y,p),**bootstrap_metrics(y,p,seed=8100+i)))
        all_predictions.extend(dict(site=site,record_id=frame.index[j],target=int(y[j]),probability=float(p[j]),
                                    threshold=FROZEN_THRESHOLD,predicted_class=int(p[j]>=FROZEN_THRESHOLD)) for j in range(len(frame)))
        subgroups.extend(subgroup_rows(site,frame,p))
        curves,bins=curve_tables(site,y,p);curve_rows.extend(curves);bin_rows.extend(bins)
    if sha256(model_path)!=EXPECTED_MODEL_SHA256:raise ValueError("Model artifact changed during evaluation")
    OUT.mkdir(parents=True,exist_ok=True)
    predictions=pd.DataFrame(all_predictions);metrics=pd.DataFrame(metric_rows)
    curves=pd.DataFrame(curve_rows);bins=pd.DataFrame(bin_rows)
    tables={"predictions.csv":predictions,"site_metrics.csv":metrics,"subgroup_metrics.csv":pd.DataFrame(subgroups),
            "cohort_audit.csv":cohort_audit,"exclusions.csv":excluded,"missingness_and_cleaning.csv":cleaning,
            "roc_pr_curves.csv":curves,"calibration_bins.csv":bins}
    for name,table in tables.items():table.to_csv(OUT/name,index=False)
    plots(predictions,metrics,curves,bins,OUT)
    outputs=list(tables)+["roc_pr.png","calibration.png","site_comparison.png"]
    manifest=dict(python=platform.python_version(),**versions,model_sha256=EXPECTED_MODEL_SHA256,threshold=FROZEN_THRESHOLD,
        script_sha256=sha256(Path(__file__)),dependency_sha256=dependency_hashes,source_sha256=source_hashes,
        accepted_freeze_sha256=sha256(ROOT/"reports/day06/accepted_freeze.json"),
        split_sha256=sha256(ROOT/"reports/day01/cleveland_split.csv"),
        holdout_unlocked_for_final_evaluation=True,model_refitted=False,threshold_changed=False,calibrator_fitted=False,
        external_zero_rule="chol/trestbps zeros -> missing; frozen Cleveland imputer only",
        external_exclusion_rule="exact full source duplicates keep first; exclude primary-predictor matches to any Cleveland row",
        internal_test_rule="all 61 frozen records; stop if primary predictor overlap with development",
        bootstrap_replicates=BOOTSTRAPS,bootstrap_seeds=[8100,8101,8102,8103],
        interval_methods="Wilson for binomial rates; ordinary within-site percentile bootstrap for ROC-AUC/AP/Brier",
        bootstrap_limitation="conditional on fitted model/cutoff; no training/selection uncertainty; single-class AUC/AP resamples omitted",
        patient_identity_limitation="record-matching/deduplication heuristics do not establish unique patients",
        no_external_pooling=True,subgroup_bands=["<50","50-59","60+"],
        output_sha256={name:sha256(OUT/name) for name in outputs})
    (OUT/"run_manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(metrics[["site","n","roc_auc","average_precision","brier","sensitivity","specificity","tp","fn","tn","fp"]].to_string(index=False,float_format=lambda v:f"{v:.4f}"))
    print("PASS: final evaluation complete with accepted model and unchanged cutoff.")
    print("Internal test outcomes are now exposed. Do not retune or replace the frozen model.")
    print(f"Outputs saved to: {OUT}")
    print("Day 8 remains open pending local output review, interpretation, and commit.")


if __name__=="__main__":
    with threadpool_limits(limits=1):main()
