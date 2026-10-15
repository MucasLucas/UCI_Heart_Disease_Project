"""Audit original UCI processed files; freeze a duplicate-group-aware split.

Run from the repository root: python scripts/day01_audit.py --data-dir data/raw
No imputation, resampling, feature selection, or model fitting occurs here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import StratifiedGroupKFold

COLUMNS = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
           "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num"]
SITES = {"cleveland": 303, "hungarian": 294, "switzerland": 123, "va": 200}
DOMAINS = {"sex": {0, 1}, "cp": {1, 2, 3, 4}, "fbs": {0, 1},
           "restecg": {0, 1, 2}, "exang": {0, 1}, "slope": {1, 2, 3},
           "ca": {0, 1, 2, 3}, "thal": {3, 6, 7}, "num": {0, 1, 2, 3, 4}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--out-dir", type=Path, default=Path("reports/day01"))
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    frames, audit, manifest, missingness = {}, [], {}, []
    for site, expected in SITES.items():
        path = args.data_dir / f"processed.{site}.data"
        if not path.is_file():
            raise FileNotFoundError(f"Missing required source: {path.resolve()}")
        raw = pd.read_csv(path, header=None, dtype=str, keep_default_na=False)
        if raw.shape != (expected, 14):
            raise ValueError(f"{path.name}: expected {(expected, 14)}, got {raw.shape}")
        raw.columns = COLUMNS
        raw = raw.apply(lambda col: col.str.strip()).replace("?", np.nan)
        df = raw.apply(pd.to_numeric, errors="raise")
        if not np.isfinite(df.to_numpy(dtype=float)[~df.isna().to_numpy()]).all():
            raise ValueError(f"Non-finite value in {site}")
        if df["num"].isna().any() or not df["num"].isin(DOMAINS["num"]).all():
            raise ValueError(f"Missing or invalid target in {site}")
        invalid = {col: sorted(float(v) for v in set(df[col].dropna()) - allowed)
                   for col, allowed in DOMAINS.items()}
        invalid = {col: values for col, values in invalid.items() if values}
        df["target"] = (df["num"] > 0).astype("int8")
        df["record_id"] = [f"{site}:{row:04d}" for row in range(len(df))]
        df["site"] = site
        # Hash only predictors. Exact matches stay together even if labels conflict.
        canonical = df[COLUMNS[:-1]].to_csv(index=False, na_rep="NA", float_format="%.12g")
        lines = canonical.splitlines()[1:]
        df["feature_group"] = [hashlib.sha256(line.encode()).hexdigest() for line in lines]
        frames[site] = df
        audit.append({"site": site, "rows": len(df), "negative": int((df.target == 0).sum()),
                      "positive": int(df.target.sum()), "prevalence": float(df.target.mean()),
                      "missing_cells": int(df[COLUMNS].isna().sum().sum()),
                      "duplicate_full_rows": int(df.duplicated(COLUMNS).sum()),
                      "duplicate_predictors": int(df.duplicated("feature_group").sum()),
                      "conflicting_label_groups": int((df.groupby("feature_group").target.nunique() > 1).sum()),
                      "invalid_categories": json.dumps(invalid, sort_keys=True),
                      "zero_chol": int((df.chol == 0).sum()),
                      "zero_trestbps": int((df.trestbps == 0).sum()),
                      "zero_thalach": int((df.thalach == 0).sum())})
        for col in COLUMNS:
            missingness.append({"site": site, "feature": col,
                                "missing_n": int(df[col].isna().sum()),
                                "missing_fraction": float(df[col].isna().mean())})
        manifest[path.name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                               "bytes": path.stat().st_size}

    cleveland = frames["cleveland"]
    # First pre-specified fold only: do not search seeds/folds for favorable results.
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    dev, test = next(splitter.split(cleveland[COLUMNS[:-1]], cleveland.target,
                                    groups=cleveland.feature_group))
    if set(cleveland.iloc[dev].feature_group) & set(cleveland.iloc[test].feature_group):
        raise RuntimeError("Duplicate predictor groups leaked across the split")
    for indices in (dev, test):
        if cleveland.iloc[indices].target.nunique() != 2:
            raise RuntimeError("Split lacks one outcome class")
    split = cleveland[["record_id", "site", "feature_group"]].copy()
    split["partition"] = "development"
    split.loc[test, "partition"] = "locked_test"
    split.to_csv(args.out_dir / "cleveland_split.csv", index=False)
    combined = pd.concat(frames.values(), ignore_index=True)
    overlap = combined.groupby("feature_group").site.nunique()
    cross_site = combined.loc[combined.feature_group.isin(overlap[overlap > 1].index),
                              ["record_id", "site", "feature_group"]]
    cross_site.to_csv(args.out_dir / "cross_site_exact_matches.csv", index=False)
    pd.DataFrame(audit).to_csv(args.out_dir / "cohort_audit.csv", index=False)
    pd.DataFrame(missingness).to_csv(args.out_dir / "missingness.csv", index=False)
    metadata = {"source_manifest": manifest, "seed": 42,
                "split_method": "First fold, StratifiedGroupKFold(n_splits=5)",
                "development_n": len(dev), "locked_test_n": len(test),
                "python": platform.python_version(), "pandas": pd.__version__,
                "numpy": np.__version__, "scikit_learn": sklearn.__version__}
    (args.out_dir / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(pd.DataFrame(audit).to_string(index=False))
    print(f"\nCleveland development: {len(dev)}; locked test: {len(test)}")
    print(f"Cross-site exact-match records: {len(cross_site)}")
    print(f"Audit saved to: {args.out_dir.resolve()}")
    print("Day 1 needs review. Do not impute values or fit models yet.")


if __name__ == "__main__":
    main()
