# Day 4: development-only baselines

Status: Day 4 complete. Lucas's successful local run and four uploaded CSVs were
reviewed on October 17, 2026. See reports/day04/interpretation.md and
reports/day04/review_checks.json for findings and verification.

## Purpose and fixed analysis choices

Establish whether predictors improve on a no-information baseline and quantify
errors before adding more complex models. The target remains existing CAD.
Use the 242 development records, the exact committed Day 3 validation folds,
and the 12-predictor later-workup setting excluding ca. Each held-out development
record receives a prediction from a model trained without that record's fold.

Three prespecified models:

| Model | Specification |
|---|---|
| dummy_prior | Predict each training fold's CAD prevalence for its validation fold |
| logistic_unweighted | L2 logistic regression, C=1, no class weights |
| logistic_balanced | Same model, balanced weights computed from training labels |

Imputation, scaling, and encoding are inside each fitted pipeline. No resampling,
parameter search, calibration, or threshold optimization is performed. The
threshold is fixed at 0.5 for this baseline comparison. A sensitivity below 0.90
at this threshold is a finding, not a reason to change the evaluation procedure.
Nested CV is not needed for these fixed specifications; future tuning and
threshold/calibration selection require the protocol's inner validation controls.
These development comparisons cannot establish final performance or clinical use.

## Windows procedure

The local starter folder may not be a Git checkout. Run these commands from any
PowerShell directory to download only the new script into the existing project:

```powershell
Set-Location "$env:USERPROFILE\Downloads\heart-disease-day01-starter\heart-disease-ds"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/MucasLucas/UCI_Heart_Disease_Project/main/scripts/day04_baselines.py" -OutFile "scripts\day04_baselines.py"
Test-Path scripts\day03_preprocessing.py
Test-Path reports\day03\development_folds.csv
python -m pip install -r requirements.txt
python scripts/day04_baselines.py
$LASTEXITCODE
```

Both Test-Path results should be True. If either is False, restore the named file
from the committed repository before running. Stop and share any complete error;
do not regenerate or edit the frozen split to bypass a hash check.
After a successful run:

```powershell
python -m pip freeze | Out-File reports\day04\environment.txt -Encoding utf8
```

## Outputs and interpretation

- `oof_metrics.csv`: pooled out-of-fold ROC-AUC, average precision, Brier score,
  sensitivity, specificity, and confusion counts at the fixed 0.5 threshold.
- `fold_metrics.csv`: the same measures for individual folds; inspect variability.
- `oof_predictions.csv`: one prediction per development record per model, with
  its held-out fold and outcome. No test records are included.
- `coefficient_contrasts.csv`: penalized, adjusted odds-ratio descriptions from
  separate full-development logistic fits. These fits do not estimate performance.
- `run_manifest.json`: hashes, fixed choices, and the actual execution environment.

Higher ROC-AUC/AP and lower Brier score indicate better values for their respective
metrics. AP uses average_precision_score, not trapezoidal PR area. The development
prevalence (111/242 = 45.9%) provides context for AP. Fold-specific dummy prevalence
predictions vary slightly, so pooled dummy ROC-AUC need not be exactly 0.5; its
within-fold ROC-AUC is 0.5. Pooled CV scores are exploratory and uncertain.

Coefficient interpretation holds other encoded predictors fixed:

- Numeric odds ratios describe a one-development-SD increase; `raw_units` gives
  that SD in the variable's original units.
- Categorical odds ratios compare each observed category with the lowest observed
  code for that feature. The encoder retains every category, so use coefficient
  differences, not a single dummy coefficient, for these comparisons.
- Values above 1 indicate higher modeled odds, below 1 lower modeled odds.
  Odds are not probabilities. Regularization shrinks coefficients; correlated
  variables and sparse categories affect them. No causal effects, inferential
  confidence intervals, or p-values are claimed.
- Class-weighted probabilities require calibration assessment later.

## Review gate

Paste terminal output and exit code, and provide `oof_metrics.csv`,
`fold_metrics.csv`, and `coefficient_contrasts.csv`. Draft
`reports/day04/interpretation.md` with:

1. How unweighted logistic regression compares with the dummy baseline.
2. How class weighting changes false negatives and false positives at 0.5.
3. Two coefficient contrasts, specifying units or reference category.
4. Limitations: small development cohort, provisional uncalibrated threshold,
   and observational coefficients rather than causal effects.

Day 4's local output and interpretation review has passed; the reviewed files
are committed under reports/day04.
Do not evaluate the 61 locked test records or cross-site cohorts yet. The local
package-version file is a provenance follow-up and can be included with this review.
