"""Check fold-fitted preprocessing; do not train classifiers or inspect holdout."""
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
NUMERIC = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL = ["sex", "cp", "fbs", "restecg", "exang", "slope", "thal"]
FEATURES = NUMERIC + CATEGORICAL
COLUMNS = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
           "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num"]
DOMAINS = {"sex": [0, 1], "cp": [1, 2, 3, 4], "fbs": [0, 1],
           "restecg": [0, 1, 2], "exang": [0, 1], "slope": [1, 2, 3],
           "thal": [3, 6, 7]}


def make_preprocessor():
    """Return an unfitted transformer; put it inside each future model Pipeline."""
    return ColumnTransformer([
        ("numeric", Pipeline([
            ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scale", StandardScaler()),
        ]), NUMERIC),
        ("categorical", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent", keep_empty_features=True)),
            ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), CATEGORICAL),
    ], remainder="drop")


def main():
    source = ROOT / "data/raw/processed.cleveland.data"
    split_path = ROOT / "reports/day01/cleveland_split.csv"
    manifest = json.loads((ROOT / "reports/day01/manifest.json").read_text())
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_hash != manifest["source_manifest"][source.name]["sha256"]:
        raise ValueError("Source hash changed; review before continuing.")
    split_bytes = split_path.read_bytes()
    canonical_split = split_bytes.replace(b"\r\n", b"\n")
    blob_hash = hashlib.sha1(
        f"blob {len(canonical_split)}\0".encode() + canonical_split
    ).hexdigest()
    if blob_hash != "37417c4d1976cbae3b00492ad014ab13c1f826a5":
        raise ValueError("Frozen split differs from reviewed GitHub version.")
    split = pd.read_csv(split_path)
    if split.record_id.isna().any() or split.record_id.duplicated().any():
        raise ValueError("Invalid split IDs.")
    if split.partition.value_counts().to_dict() != {"development": 242, "locked_test": 61}:
        raise ValueError("Expected 242 development / 61 locked records.")
    raw = pd.read_csv(source, header=None, names=COLUMNS, na_values="?")
    raw.index = [f"cleveland:{i:04d}" for i in range(len(raw))]
    if set(raw.index) != set(split.record_id):
        raise ValueError("Source IDs differ from frozen split.")
    ids = split.loc[split.partition.eq("development"), "record_id"]
    dev = raw.loc[ids, FEATURES + ["num"]].copy()
    if not dev.num.isin([0, 1, 2, 3, 4]).all():
        raise ValueError("Invalid development outcome.")
    X, y = dev[FEATURES], dev.num.gt(0).astype(int)
    if set(y) != {0, 1}:
        raise ValueError("Both development classes required.")
    for feature, allowed in DOMAINS.items():
        if not X[feature].dropna().isin(allowed).all():
            raise ValueError(f"Unexpected category in {feature}.")
    if not np.isfinite(X.to_numpy()[~X.isna().to_numpy()]).all():
        raise ValueError("Nonfinite development input.")
    positive = ["age", "trestbps", "chol", "thalach"]
    if X[positive].le(0).any().any() or X.oldpeak.lt(0).any():
        raise ValueError("Nonpositive physiology/negative oldpeak requires review; no rows deleted.")

    # Identical primary predictor rows stay together, even if ca differs.
    groups = pd.util.hash_pandas_object(X, index=False)
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    checks, assignments = [], []
    for fold, (train, valid) in enumerate(cv.split(X, y, groups), 1):
        if set(groups.iloc[train]) & set(groups.iloc[valid]):
            raise ValueError("Predictor group crossed fold boundary.")
        if set(y.iloc[train]) != {0, 1} or set(y.iloc[valid]) != {0, 1}:
            raise ValueError("A fold lacks an outcome class.")
        prep = make_preprocessor()
        train_matrix = prep.fit_transform(X.iloc[train])
        valid_matrix = prep.transform(X.iloc[valid])
        if not np.isfinite(train_matrix).all() or not np.isfinite(valid_matrix).all():
            raise ValueError("Nonfinite transformed values.")
        learned = prep.named_transformers_["numeric"].named_steps["impute"].statistics_
        if not np.allclose(learned, X.iloc[train][NUMERIC].median().to_numpy()):
            raise ValueError("Imputer statistics differ from training-only medians.")
        checks.append(dict(fold=fold, train_n=len(train), valid_n=len(valid),
                           train_positive_n=int(y.iloc[train].sum()),
                           valid_positive_n=int(y.iloc[valid].sum()),
                           transformed_columns=train_matrix.shape[1], finite=True))
        assignments.extend(dict(record_id=X.index[i], validation_fold=fold) for i in valid)

    out = ROOT / "reports/day03"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(checks).to_csv(out / "fold_checks.csv", index=False)
    pd.DataFrame(assignments).sort_values("record_id").to_csv(out / "development_folds.csv", index=False)
    later = {"thalach", "exang", "oldpeak", "slope", "thal"}
    pd.DataFrame([
        dict(feature=f, included=True,
             setting="later diagnostic workup" if f in later else "basic presentation/workup",
             timing="Assumed from variable meaning; individual timestamps unavailable")
        for f in FEATURES
    ] + [dict(feature="ca", included=False, setting="angiography-related", timing="Excluded from primary model"),
         dict(feature="num", included=False, setting="outcome", timing="Never a predictor")]
    ).to_csv(out / "feature_availability.csv", index=False)
    (out / "run_manifest.json").write_text(json.dumps(dict(
        source_sha256=source_hash, split_sha256=hashlib.sha256(split_bytes).hexdigest(),
        development_n=len(X), locked_test_n=61, holdout_analyzed=False,
        classifiers_fitted=False, python=platform.python_version(),
        pandas=pd.__version__, numpy=np.__version__, scikit_learn=sklearn.__version__,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    ), indent=2) + "\n")
    print(pd.DataFrame(checks).to_string(index=False))
    print("PASS: preprocessing fitted independently in five development training folds.")
    print("Locked test not analyzed. No classifier trained. Review outputs before advancing.")


if __name__ == "__main__":
    main()
