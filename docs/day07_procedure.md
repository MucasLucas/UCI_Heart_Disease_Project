# Day 7: frozen-model explanations and development subgroup review

Status: runnable procedure prepared; Lucas's local execution, interpretation, and
completion review remain pending. Use the accepted Day 6 model without refitting,
recalibration, threshold changes, or test access.

## Two analyses with different purposes

1. **SHAP explanations:** describe predictions of the frozen full-development
   model on the 242 development records. These are training-record explanations,
   not independent validation results. No training accuracy is reported.
2. **Subgroup audit:** use the already reviewed Day 6 out-of-fold selection-policy
   predictions and their fold-specific cutoffs. These scores come from models
   that excluded their own outer validation fold. They evaluate the selection
   procedure, not the single final frozen forest. Do not mix the two roles.

The accepted model remains c06: uncalibrated Random Forest, 200 trees,
max_depth=None, min_samples_leaf=3, max_features=sqrt, seed 42, with cutoff
0.3528716233973672 and the same 12 later-workup predictors excluding ca.
The model artifact stays at models/day06_candidate.joblib.

## Integrity checks

Before joblib loading, the script checks the artifact against the reviewed
SHA-256, accepted freeze status, and exact Day 6 scikit-learn, NumPy, pandas, and
joblib versions. It checks the model specification, feature order, class order,
and cutoff after loading. Day 6 policy predictions are checked against a reviewed
canonical file hash, development IDs, outcomes, and fold assignments. Day 1
source and split integrity checks remain in force.

No fit, fit_transform, resampling, or optimization is performed. Only the
existing preprocessing transform is used. The script rechecks artifact bytes and
model probabilities after explanations. A mismatch is a stop for investigation,
not permission to regenerate the frozen artifact or edit an expected hash.

## SHAP specification

- TreeExplainer with tree_path_dependent perturbation and native raw output.
  For this scikit-learn RandomForestClassifier, that output is class probability,
  not a log-odds margin; reconstruction is checked against predict_proba.
- Background is implicit in the fitted training counts along tree paths. Its
  source cohort is development only. No test or external data enter it.
  background_ids.csv lists the eligible training cohort, not uniform background
  weights or the repeated/subsampled observations in each bootstrap tree.
- Explain all 242 development rows. Verify that baseline probability plus SHAP
  contributions reconstructs predict_proba for class 1 within 1e-5.
- Sum one-hot-column contributions for each original input, preserving additivity.
  Global ranking uses mean absolute values of these summed contributions.
- Local examples are the first three development record IDs in lexical order,
  selected before inspecting outcomes, errors, or contributions.

A +0.05 contribution means five probability percentage points above the
background baseline in this explanation. It is not a five-percent relative
probability change, coefficient, odds ratio, clinical effect, or causal claim.
The threshold affects the predicted class; it does not change SHAP contributions.

Summing dummy-column SHAP values is not recomputing exact original-variable or
coalition SHAP. Tree-path attribution uses the background assumptions implied
by the fitted tree structure and training path counts. Correlated predictors,
encoding, and these background assumptions affect attribution.
Do not label an important feature as an independent cause or a treatment target.

Method reference: SHAP TreeExplainer documentation:
https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html

## Subgroups fixed before this Day 7 computation

Report overall, recorded sex codes 0 and 1, and age bands <50, 50–59, and >=60.
Age cutoffs are specified for this Day 7 descriptive review, before subgroup
results, not inferred as previously fixed in the original protocol. Recorded
binary sex codes are not a comprehensive measure of gender identity.

Each row includes total n, positive and negative denominators, confusion counts,
sensitivity, specificity, ROC-AUC when both outcomes are present, and Brier score.
Sensitivity and specificity receive descriptive 95% Wilson intervals. An undefined
metric stays blank rather than becoming zero. Flag positive/negative denominators
below 20 so sparse results remain visible.

These intervals do not include training, calibration, threshold/model selection,
reused-fold dependence, or multiple-comparison uncertainty. They are descriptive
intervals rather than a complete uncertainty analysis. Overlapping or separated
intervals are not formal fairness tests. Sparse subgroup scores cannot establish
fairness or deployment readiness. Do not change the frozen model based on these
results. More formal final subgroup evaluation remains part of Day 8 reporting.

## Windows PowerShell procedure

Download the new script, current dependencies, and the authoritative review files.
The Day 6 review files are small text files; this does not replace your model.

```powershell
Set-Location "$env:USERPROFILE\Downloads\heart-disease-day01-starter\heart-disease-ds"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/MucasLucas/UCI_Heart_Disease_Project/main/scripts/day07_explanations.py" -OutFile "scripts\day07_explanations.py"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/MucasLucas/UCI_Heart_Disease_Project/main/requirements.txt" -OutFile "requirements.txt"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/MucasLucas/UCI_Heart_Disease_Project/main/reports/day06/accepted_freeze.json" -OutFile "reports\day06\accepted_freeze.json"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/MucasLucas/UCI_Heart_Disease_Project/main/reports/day06/run_manifest.json" -OutFile "reports\day06\run_manifest.json"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/MucasLucas/UCI_Heart_Disease_Project/main/reports/day06/policy_oof_predictions.csv" -OutFile "reports\day06\policy_oof_predictions.csv"
python -m pip install -r requirements.txt
```

After installation:

```powershell
python scripts/day07_explanations.py
$LASTEXITCODE
```

After exit code 0:

```powershell
python -m pip freeze | Out-File reports\day07\environment.txt -Encoding utf8
```

SHAP is pinned to the tested version 0.50.0. If installation fails or a package
version check fails, share the complete error. Do not rerun Day 6 to make a new
model under changed packages. Restore the recorded Day 6 environment instead.
Never load a substitute bundle merely because it has the same parameter settings.

## Outputs and review

Share terminal output and exit code, then upload these from reports/day07:

- global_shap.csv and global_shap.png: original-input aggregate ranking.
- local_explanations.csv and local_shap.png: the three deterministic examples.
- subgroup_metrics.csv and subgroup_intervals.png: counts, rates, and intervals.
- run_manifest.json: integrity, environment, cohort roles, and SHAP additivity check.

Retain the additional audit files: shap_encoded.csv, shap_grouped.csv,
feature_mapping.csv, model_explanation_predictions.csv, and background_ids.csv.
No separate fitted model is created.

Draft interpretation.md after results are available: name the leading explanatory
features; interpret one local positive and one negative contribution in probability
units; describe subgroup denominators and uncertainty without claiming fairness;
and state that explanations are descriptive and subgroup scores assess the Day 6
selection policy. Commit only after output review. Keep Day 7 open until then.

## Reference validation scope

The development-analysis core is tested using a separate reference forest fitted
in the independent environment, not Lucas's unuploaded Windows artifact. This
checks SHAP shape/additivity, encoded-feature aggregation, subgroup calculations,
interval edge cases, and plotting. The tested tree-path configuration reconstructs
probabilities to numerical precision. An initially tested interventional setup
failed the independent probability reconstruction check and is not used. It does not independently load or verify the
user's accepted binary. The normal script requires Lucas's exact accepted hash;
there is no command-line checksum bypass or refitting option.
