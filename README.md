# Interpretable Coronary Artery Disease Classification

An evaluation-first study of the historical UCI Heart Disease cohorts, emphasizing
sensitivity, calibration, predictor availability, and cross-site transportability.
Status: Day 3 preprocessing reviewed and decisions confirmed; no models trained.
Next: Day 4 dummy and regularized logistic-regression baselines.

## Start here
Requires Python 3.10 or newer. From this directory:

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/day01_audit.py --data-dir data/raw
python -m pip freeze > reports/day01/environment.txt
```

The starter package includes unchanged copies of the four uploaded processed
files for local execution. Git ignores these raw inputs. Review the generated
audit and study protocol before moving to Day 2. The supplied audit outputs are
a reference run; rerun on your machine and share outputs/errors for review.
Keep the split manifest unchanged; do not inspect holdout-specific outcomes or
predictor distributions during development. The script audits source-level class
counts for integrity; subsequent EDA uses development rows only.

## Deliverables
- Reproducible audit, cohort definitions, and frozen validation protocol.
- Leakage-safe model comparison, calibration, and sensitivity-driven thresholds.
- SHAP interpretation, uncertainty estimates, and cross-site/subgroup analyses.
- Research report and one-page executive summary for healthcare audiences.

## Development-only EDA
After the Day 1 review, run `python scripts/day02_eda.py` from this directory.
The script verifies the source hash and frozen split, excludes `ca`, and produces
development-only summaries and PNG/SVG boxplots. See
`reports/day02/interpretation.md` for reviewed observations and limitations.
The committed run manifest records the independent reference environment.

See docs/protocol.md, docs/data_dictionary.csv, and docs/project_plan.md.
Lucas completed the local audit on October 14, 2026; its terminal results matched
the reference summary. The target is existing coronary artery disease, with ca
excluded from the primary model. See docs/day01_review.md for provenance and
remaining local environment evidence.

## First commit (after review)
Inside a cloned target repository, use:

```bash
git add .gitignore README.md requirements.txt scripts docs data/raw/README.md reports/day01
git commit -m "chore: establish CAD study protocol, source audit, and frozen validation split"
git push
```

For a new local repository, initialize main and configure the user-provided remote
before pushing: git init -b main; git remote add origin YOUR_REPOSITORY_URL;
then use git push -u origin main after the first commit.
