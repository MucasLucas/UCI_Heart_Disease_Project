"""Describe only the frozen Cleveland development cohort; never fit models."""
import hashlib
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/day02"
COLUMNS = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
           "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num"]
CONTINUOUS = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL = ["sex", "cp", "fbs", "restecg", "exang", "slope", "thal"]
LABELS = {"age": "Age (years)", "trestbps": "Resting blood pressure (mmHg)",
          "chol": "Total cholesterol (mg/dL)", "thalach": "Maximum heart rate (beats/min)",
          "oldpeak": "ST depression (oldpeak, source scale)"}


def main():
    source = ROOT / "data/raw/processed.cleveland.data"
    manifest = json.loads((ROOT / "reports/day01/manifest.json").read_text(encoding="utf-8"))
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_hash != manifest["source_manifest"][source.name]["sha256"]:
        raise ValueError("Source hash changed; stop and review the input.")
    split_path = ROOT / "reports/day01/cleveland_split.csv"
    split = pd.read_csv(split_path)
    if split["record_id"].isna().any() or split["record_id"].duplicated().any():
        raise ValueError("Missing or duplicate IDs in frozen split.")
    if set(split["partition"]) != {"development", "locked_test"}:
        raise ValueError("Unexpected partition labels.")
    raw = pd.read_csv(source, header=None, names=COLUMNS, na_values="?")
    raw["record_id"] = [f"cleveland:{i:04d}" for i in range(len(raw))]
    if set(raw["record_id"]) != set(split["record_id"]):
        raise ValueError("Source records do not match frozen split.")
    ids = set(split.loc[split["partition"].eq("development"), "record_id"])
    features = CONTINUOUS + CATEGORICAL
    dev = raw.loc[raw["record_id"].isin(ids), features + ["num"]].copy()
    if len(dev) != manifest["development_n"] or len(dev) != 242:
        raise ValueError("Unexpected development cohort size.")
    if dev["num"].isna().any() or not dev["num"].isin([0, 1, 2, 3, 4]).all():
        raise ValueError("Invalid development outcome.")
    dev["target"] = dev.pop("num").gt(0).astype(int)
    if set(dev["target"]) != {0, 1}:
        raise ValueError("Both development outcome classes are required.")
    OUT.mkdir(parents=True, exist_ok=True)
    outcomes = dev["target"].value_counts().sort_index().rename("n").to_frame()
    outcomes["fraction"] = outcomes["n"] / len(dev)
    outcomes.to_csv(OUT / "outcome_balance.csv")
    missing = dev[features].isna().sum().rename("missing_n").to_frame()
    missing["missing_fraction"] = missing["missing_n"] / len(dev)
    missing.sort_values("missing_n", ascending=False).to_csv(OUT / "missingness.csv")
    summary = dev.groupby("target")[CONTINUOUS].agg(
        ["count", "median", lambda x: x.quantile(.25), lambda x: x.quantile(.75)])
    summary.columns = [f"{feature}_{stat}" for feature in CONTINUOUS
                       for stat in ["n", "median", "q25", "q75"]]
    summary.to_csv(OUT / "continuous_by_outcome.csv")
    tables = []
    for feature in CATEGORICAL:
        table = pd.crosstab(dev[feature].fillna("Missing"), dev["target"]).reindex(
            columns=[0, 1], fill_value=0)
        table.columns = ["negative_n", "positive_n"]
        table["total_n"] = table.sum(axis=1)
        table["positive_fraction"] = table["positive_n"] / table["total_n"]
        table.insert(0, "feature", feature)
        table.index.name = "category"
        tables.append(table.reset_index())
    pd.concat(tables, ignore_index=True).to_csv(OUT / "categorical_by_outcome.csv", index=False)
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    for ax, feature in zip(axes.flat, CONTINUOUS):
        ax.boxplot([dev.loc[dev["target"].eq(label), feature].dropna() for label in [0, 1]])
        ax.set_xticks([1, 2], ["CAD absent", "CAD present"])
        ax.set_title(LABELS[feature])
    axes.flat[-1].axis("off")
    fig.suptitle("Cleveland development cohort only (n=242)")
    fig.tight_layout()
    for extension in ["png", "svg"]:
        fig.savefig(OUT / f"continuous_by_outcome.{extension}", dpi=180)
    plt.close(fig)
    (OUT / "run_manifest.json").write_text(json.dumps({
        "source_sha256": source_hash,
        "split_sha256": hashlib.sha256(split_path.read_bytes()).hexdigest(),
        "development_n": len(dev), "excluded_predictors": ["ca"],
        "holdout_summarized": False, "models_fitted": False,
        "python": platform.python_version(), "pandas": pd.__version__,
        "matplotlib": matplotlib.__version__,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Development records: {len(dev)}")
    print("\nOutcome balance:\n", outcomes.to_string())
    print("\nMissingness:\n", missing.to_string())
    print(f"\nOutputs saved to: {OUT}")
    print("Review outputs and documentation before committing or advancing.")


if __name__ == "__main__":
    main()
