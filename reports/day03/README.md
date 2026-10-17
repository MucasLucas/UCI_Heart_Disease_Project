# Day 3 preprocessing check

Status: Day 3 complete. On October 16, 2026 (America/Los_Angeles), Lucas supplied
local PowerShell output matching all five reference folds and exit code 0, then
explicitly confirmed the three study decisions below.

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

## Confirmed decisions

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

## Local review evidence

Lucas's pasted terminal output showed training sizes 193, 193, 194, 194, 194;
validation sizes 49, 49, 48, 48, 48; training-positive counts 88, 89, 89, 89, 89;
and validation-positive counts 23, 22, 22, 22, 22. Each fold reported 24 transformed
columns and finite=True. The script printed PASS and returned exit code 0.
This is user-supplied terminal evidence, not a separate uploaded local run manifest.

Lucas also ran the environment export command without a reported error. The
local environment.txt has not been provided or uploaded to GitHub; its contents
remain unverified and can be added later. The committed run manifest remains
reference-run evidence.

Next: Day 4 dummy and regularized logistic-regression baselines. Reuse the
preprocessor inside each classifier pipeline; do not preprocess the entire
development cohort before cross-validation.
