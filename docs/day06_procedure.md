# Day 6: calibration, decision threshold, and proposed model freeze

Status: procedure prepared; local run and accepted freeze remain pending.
Target: existing CAD. Primary predictors: the same 12 later-workup variables,
excluding ca. The 61-record test set and external cohorts remain untouched.

## What changes today

Calibration assesses whether predicted probabilities agree with observed disease
frequencies. Threshold selection determines which probabilities trigger a positive
classification. A higher ROC-AUC does not determine the best decision cutoff.
The development objective remains sensitivity >=0.90, then maximum specificity.
This is an exploratory engineering constraint, not a demonstrated clinical standard.

## Candidate set fixed before the Day 6 run

Ten candidates: unweighted L2 logistic regression (C=1) and four Random Forest
configurations, each without calibration and with sigmoid calibration. Forest
settings are exactly the Day 5 grid: max_depth in {3, None} crossed with
min_samples_leaf in {3, 8}, 200 trees, max_features=sqrt, no class weights,
random_state=42. No configuration is picked merely because it was the most common
Day 5 winner. The complete fixed set is evaluated again inside selection folds.

The shortlist is informed by exploratory Days 4–5: logistic is the interpretable
reference and Random Forest led pooled discrimination. XGBoost and balanced
logistic remain reported Day 5 comparators. They are not Day 6 selection candidates.
This is an explicit resource/scope choice, not evidence they cannot work. Flexible
thresholds already permit sensitivity changes without adding class weighting.
No isotonic calibration is added to this small cohort. Do not expand candidates
in response to Day 6 outer scores.

## Three levels of development validation

1. **Outer assessment:** retain the same five development folds. Within each
   outer training set, generate three-fold out-of-fold predictions for every
   candidate. These predictions determine the candidate and cutoff. The outer
   validation outcomes never enter that selection.
2. **Candidate selection:** among all unique probability cutoffs, use the rule
   positive iff probability >= cutoff. Require TP >= ceil(0.90 * positive_count).
   For each candidate, maximize specificity, breaking threshold ties toward the
   highest cutoff. Then select the candidate with highest feasible specificity,
   breaking ties by lower Brier score and candidate ID. This rule is fixed before
   running, rather than changed to favor an observed model.
3. **Calibration fitting:** inside each training partition for each sigmoid
   candidate, obtain three-fold calibration scores from fresh complete pipelines.
   CalibratedClassifierCV uses method=sigmoid, ensemble=False. The calibrator fits
   these scores, and a single base pipeline is refitted on that training partition.
   Calibration outcomes are never used to train their own base score. The outer
   validation set is absent from all preprocessing, calibration, and selection.

Every split is stratified and groups identical primary-predictor rows together.
Group hashes are record-similarity controls, not verified patient identifiers.
CalibratedClassifierCV uses decision_function when available (logistic), otherwise
predict_proba (Random Forest). Sigmoid calibration is learned, not assumed to help.

The outer validation prediction for the selected candidate uses the cutoff learned
within its outer training set. Pooled outer results estimate the complete selection
procedure. They may miss the 90% sensitivity objective even when selection-fold
sensitivity met it. This is an honest finding, not a reason to use test labels.

## Final review candidate

After outer assessment, select the final candidate and cutoff using the pooled
cross-fitted predictions for all 242 development records, following the same
rule. This full-development selection uses five folds rather than the three used
inside smaller outer training sets. Fit that candidate on development only.
This is permitted training/selection for the future locked-test evaluation.
Its selection scores are optimistic for the selected winner and are not a fresh
performance estimate. Calibration curves for candidates are also development
comparisons; reused Days 4–5 folds and an adaptive shortlist limit confirmation.

A threshold of zero can satisfy sensitivity by flagging everyone. Feasibility
alone does not establish utility. Inspect specificity and false-positive burden.
Report low specificity or an unmet outer sensitivity objective plainly.

The script writes a proposed model bundle to models/day06_candidate.joblib and
candidate_freeze.json with specification, threshold, feature list, and bundle
SHA-256. Its status is explicitly pending review. Keep the bundle locally; models/
is ignored by Git. A joblib bundle is environment-dependent, so record package
versions. The exact bundle hash, accepted rule, and source hashes should be recorded
in the completion review before Day 8. Later refitting changes the bundle hash and
requires review. Do not change the cutoff after inspecting the locked test.

## Run in Windows PowerShell

From any directory:

```powershell
Set-Location "$env:USERPROFILE\Downloads\heart-disease-day01-starter\heart-disease-ds"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/MucasLucas/UCI_Heart_Disease_Project/main/scripts/day06_calibration.py" -OutFile "scripts\day06_calibration.py"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/MucasLucas/UCI_Heart_Disease_Project/main/requirements.txt" -OutFile "requirements.txt"
Test-Path scripts\day03_preprocessing.py
Test-Path scripts\day04_baselines.py
Test-Path reports\day03\development_folds.csv
python -m pip install -r requirements.txt
```

All path checks should return True. After installation:

```powershell
python scripts/day06_calibration.py
$LASTEXITCODE
```

Allow several minutes. The script prints each outer fold and caps numerical-library
threads at one. After success:

```powershell
python -m pip freeze | Out-File reports\day06\environment.txt -Encoding utf8
```

## Outputs and review gate

Paste the terminal output and exit code. Upload:

- policy_oof_metrics.csv and policy_fold_metrics.csv: outer performance of the
  complete selection procedure, using cutoffs chosen in outer training data.
- outer_selection.csv: each outer training set's chosen candidate and cutoff.
- candidate_freeze.json: the proposed final rule and bundle hash.
- final_selection_metrics.csv: threshold-selection scores for all ten candidates,
  explicitly not independent performance of the final winner.
- calibration_threshold.png: binned calibration and final-selection tradeoff.
- run_manifest.json and environment.txt: execution provenance.

Retain all outputs for audit. Additional files are candidate_specifications.csv,
candidate_oof_predictions.csv, candidate_oof_metrics_at_05.csv,
inner_oof_predictions.csv, inner_selection_metrics.csv, policy_oof_predictions.csv,
threshold_tradeoff.csv, calibration_bins.csv, and validation_membership.csv.
The plot's cXX labels map to candidate_specifications.csv. Five fixed probability
bins may contain few observations; no calibration confidence bands are implied.

After review, document calibration changes, sensitivity/specificity and false
positives, selection stability, limits, and the accepted model/cutoff/hash. Commit
that accepted freeze record before moving to explanations and final evaluation.
Do not upload or evaluate the locked test. Day 6 is not complete merely because
the script finishes or a pending candidate exists.

## Independent reference check (not Lucas's local freeze)

The tested reference environment used scikit-learn 1.8.0. Reconstructed all five
inner candidate/cutoff selections independently from their recorded scores,
reconciled policy metrics, checked calibration membership boundaries, and verified
input hashes, bundle SHA-256, and successful model reload. Tied-score and separated-
score threshold cases agree with independent confusion-matrix calculations.

Outer selection-policy results: sensitivity 98/111 = 0.8829, specificity 82/131 =
0.6260, 13 false negatives, 49 false positives. The sensitivity objective was not
met on this outer assessment. Do not raise the reported value to the target.

Full-development selection proposed c06 (uncalibrated Random Forest, 200 trees,
max_depth=None, min_samples_leaf=3) at cutoff 0.3528716233973672, with selection
sensitivity 0.9009 and specificity 0.6718. This is a pending proposal from the
reference environment, not an accepted local model or independent performance
estimate. Local results and bundle hashes may differ with package versions.
