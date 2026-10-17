# Day 3 preprocessing check

Status: independent reference run passed. Lucas's local run and review of feature
availability and imbalance decisions remain pending; Day 3 is not complete.

From the project root, after installing requirements, run:

```powershell
python scripts/day03_preprocessing.py
$LASTEXITCODE
python -m pip freeze | Out-File reports\day03\environment.txt -Encoding utf8
```

The script verifies the Cleveland source hash and reviewed frozen split, then
uses only the 242 development records. It fits median imputation and scaling for
continuous variables and mode imputation and one-hot encoding for categorical
variables independently in each training fold. Identical primary predictor rows
stay in the same fold. Both `ca` and the outcome are excluded from predictors.

The reference run produced five finite training/validation matrices with 24
columns each. Training folds contained 193–194 records; validation folds contained
48–49. Numeric imputer statistics matched training-only medians in every fold.
The 61 locked test records were not analyzed, and no classifier was trained.
`run_manifest.json` records the reference environment, source, split, and script
hashes; it does not describe Lucas's Windows environment.

## Decisions for review

- Retain all 12 primary predictors for the later diagnostic-workup setting.
  `feature_availability.csv` marks assumed timing; individual timestamps are
  unavailable. This feature set does not represent an initial-presentation model.
- Keep median/mode imputation inside the future model pipeline. Learn encoding
  categories within training folds; unseen validation categories are ignored.
- Keep observed extreme values unless source verification identifies an error.
  Invalid physiology triggers review rather than silent replacement or deletion.
- Start with an unweighted baseline: 111 positive and 131 negative development
  outcomes do not justify automatic oversampling. Compare class weights later
  using development validation only. No SMOTE is applied in this check.

Before advancing, review the local terminal output, generated fold checks, and
these decisions, then commit the local evidence. Reuse the preprocessor inside
each future classifier pipeline; do not preprocess the entire development cohort
before cross-validation.
