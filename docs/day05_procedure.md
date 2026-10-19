# Day 5: nested tree-model comparison

Status: procedure prepared. Day 5 remains open until Lucas's local outputs,
interpretation, and completion commit are reviewed. Existing CAD remains the
outcome. The 12 primary predictors exclude ca and require the later-workup setting.

## Why this step matters

Random Forest averages many trees. XGBoost builds trees sequentially to improve
its objective. Both can capture nonlinear relationships and interactions without
specifying them in advance. More flexible models may overfit this small dataset,
so compare them with the fixed Day 4 baselines rather than assuming improvement.

## Prespecified design

- Reuse all 242 development records and the exact Day 3 five-fold assignments.
  Keep the 61-record internal test and all external cohorts out of evaluation.
- For each outer training set, use three stratified group inner folds. Identical
  primary predictor rows remain together in both inner and outer folds.
- Fit the complete preprocessing/model pipeline afresh in every inner fit.
  Select each tree family's configuration by highest mean inner ROC-AUC.
- Refit the winning configuration on that outer training set only. Evaluate on
  its outer validation fold. Each record receives exactly one outer validation
  prediction per model. Outer validation does not enter parameter selection.
- Tie rule: first candidate in deterministic ParameterGrid order.
- No resampling, tree class weights, early stopping, calibration, threshold search,
  or final model selection. Evaluate the fixed 0.5 threshold for baseline comparability.
  The proposed sensitivity objective remains unchanged. ROC-AUC is the Day 5 inner
  ranking metric, not a substitute for the later sensitivity/specificity decision.

| Family | Four configurations | Fixed settings |
|---|---|---|
| Random Forest | max_depth in {3, None} crossed with min_samples_leaf in {3, 8} | 200 trees, max_features=sqrt, no class weights, seed 42 |
| XGBoost | max_depth in {1, 2} crossed with n_estimators in {100, 250} | learning_rate=0.03, min_child_weight=5, reg_lambda=5, full row/column sampling, scale_pos_weight=1, hist trees, seed 42 |

Budget: 120 inner candidate fits, 10 outer tree refits, and 15 fixed-baseline
fits. Single-worker execution limits resource use. The script prints outer-fold
progress and may take several minutes on a laptop. Grids are fixed before the
reference run. Do not expand them in response to outer-fold scores.

The script imports the reviewed Day 3 preprocessor and Day 4 loader/metrics.
It independently reruns the dummy and both fixed logistic models on the same
outer folds, so Day 4 result files need not be downloaded or modified.
Preprocessing is retained for comparability, including scaling even though tree
splits do not require it. Keep feature sets constant for this comparison.

## Windows procedure

From PowerShell:

```powershell
Set-Location "$env:USERPROFILE\Downloads\heart-disease-day01-starter\heart-disease-ds"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/MucasLucas/UCI_Heart_Disease_Project/main/scripts/day05_tree_models.py" -OutFile "scripts\day05_tree_models.py"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/MucasLucas/UCI_Heart_Disease_Project/main/requirements.txt" -OutFile "requirements.txt"
Test-Path scripts\day03_preprocessing.py
Test-Path scripts\day04_baselines.py
Test-Path reports\day03\development_folds.csv
python -m pip install -r requirements.txt
```

All three path checks should return True. Once installation succeeds:

```powershell
python scripts/day05_tree_models.py
$LASTEXITCODE
```

After success:

```powershell
python -m pip freeze | Out-File reports\day05\environment.txt -Encoding utf8
```

If a hash validation fails, share the complete error. Restore the reviewed files
rather than editing a hash constant or regenerating the frozen test split.

## Review outputs

All outputs are written to reports/day05:

- oof_metrics.csv: pooled outer-validation metrics for all five model families.
- fold_metrics.csv: scores and confusion counts for each outer fold.
- oof_predictions.csv: model, record ID, fold, outcome, and probability.
- inner_search_results.csv: all candidate scores, inner-fold scores, ranks, parameters.
- selected_parameters.csv: winning parameters within each outer training fold.
- inner_fold_assignments.csv: auditable inner validation membership by outer fold.
- run_manifest.json: environment, grids, fixed settings, safeguards, and input hashes.

Share the terminal output and exit code, plus oof_metrics.csv, fold_metrics.csv,
selected_parameters.csv, and run_manifest.json. Retain all generated files for
the review commit. Full predictions and inner-search results allow independent
metric reconciliation and inspection of the tuning process.

In reports/day05/interpretation.md, document:

1. Whether the tree families improve ROC-AUC, average precision, or Brier score
   relative to unweighted logistic regression. Name the metrics separately.
2. False-negative and false-positive counts at 0.5, not sensitivity alone.
3. Fold variability and whether selected settings vary between outer folds.
4. Limits: small historical cohort, uncalibrated probabilities, no final test
   results, and uncertainty from model-family comparison on development data.

The nested estimates evaluate each tree family's inner-selection procedure, not
one globally fixed tree configuration. Small score differences do not prove
superiority. Do not use the outer results as a new tuning loop. Choosing the final
family from these estimates introduces selection uncertainty; final performance
requires the locked test after the complete pipeline and threshold are frozen.
Day 6 will handle calibration and threshold selection under development-only
validation controls. No final model artifact is saved by the Day 5 script.
