# Interpretable Coronary Artery Disease Classification

An evaluation-first study of the historical UCI Heart Disease cohorts, emphasizing
sensitivity, calibration, predictor availability, and cross-site transportability.
Status: Day 9 professional report complete.
Next: Day 10 reproducibility, model card, executive summary, and release packaging. The 61-record internal test has been evaluated;
no retuning follows. See reports/day08/interpretation.md for final results and
provenance limits, and reports/day06/accepted_freeze.json for the unchanged model.
The local model binary was not uploaded.

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

## Frozen-model explanations and subgroup review
Day 7's runnable procedure is docs/day07_procedure.md. It verifies the accepted
local bundle before loading, explains the frozen forest, and uses Day 6
out-of-fold policy predictions for descriptive subgroup metrics. It does not fit
models or inspect the locked test set. Reviewed uploaded results and limitations are recorded in reports/day07/interpretation.md.

## Final internal and external evaluation
Day 8's procedure is docs/day08_evaluation_protocol.md. Before generating final
predictions, it verifies the frozen artifact/environment, all four raw source
hashes, the 61-record internal split, and the declared external exclusion/zero
rules. It reports each cohort separately with confidence intervals. The actual local outputs have been reviewed: Cleveland test ROC-AUC 0.957,
Hungarian 0.903, Switzerland 0.766, and VA 0.721. Sensitivity/specificity, uncertainty,
calibration, cohort handling, and the site-comparison image checksum discrepancy
are recorded in reports/day08/interpretation.md. Cross-site performance varies;
these historical results do not establish clinical readiness.


## Research report

Read the [10-page research report](reports/day09/report.pdf) or its
[editable Markdown source](reports/day09/report.md). It covers the methods,
final results with uncertainty, calibration, SHAP, subgroup findings, and evidence
limits. See [Day 9 procedure](docs/day09_procedure.md) for review and PDF rendering.
Day 10's clean-environment checks and release packaging remain open.

