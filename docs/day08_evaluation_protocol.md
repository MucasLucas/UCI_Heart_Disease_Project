# Day 8: final evaluation protocol and run procedure

Specified October 21, 2026 (America/Los_Angeles), before computing final model
predictions. Status: script prepared; Lucas's actual local evaluation and output
review remain pending. The preparation tests use synthetic data, not a substitute
model evaluated on the actual test patients.

## Frozen question and artifact

Classify existing CAD using the accepted c06 forest and unchanged decision rule
probability >= 0.3528716233973672. Verify SHA-256
948f8939076cdc1e001a74d7bb414b28c88e21b7de32b0a2172fdc4a805ce1ae
before loading models/day06_candidate.joblib. Require the recorded Day 6 package
versions. Use all 61 records assigned to the frozen Cleveland locked_test partition.
No fitting, tuning, recalibration, class reweighting, or threshold selection is
performed. ca and num are never predictors.

## Pre-evaluation data-rule addendum

Earlier work audited impossible zero physiology and source duplicates but did
not fully specify external handling. The rules below operationalize that work
before the first final predictions; do not describe them as all fixed on Day 1.
They change no fitted model parameters or cutoff. Report this clarification in
the final Methods and limitations.

1. Verify all four raw source hashes against reports/day01/manifest.json before
   any evaluation. Require their original sizes/cohorts: Cleveland 303, Hungary
   294, Switzerland 123, and VA 200. Require valid source targets/categorical codes.
2. Keep the Cleveland test at its 61 frozen records. The other 242 Cleveland
   records are training/development, not evaluation exclusions. If identical
   primary predictors cross that development/test boundary, stop for review
   rather than silently changing the locked cohort.
3. For each external site, keep the first occurrence of exact full-source-row
   duplicates and record removed IDs. Full-source equality includes all 14 fields
   and matching missing values; primary-predictor similarity alone does not imply
   the same person. Records with differing fields/outcomes are not merged.
4. Exclude external rows whose 12 primary predictors match any Cleveland record,
   irrespective of outcome. This conservatively extends the protocol's original
   development-overlap exclusion to all Cleveland rows, avoiding overlap between
   the reported internal and external cohorts as well. Record exact exclusion
   reasons and counts. External sites remain separate; no pooled external score
   is produced. Cross-external identity cannot be established from these files.
5. For external data only, replace the previously audited zero chol and zero
   trestbps values with missing. Use the existing frozen Cleveland imputer,
   scaler, and encoder; never learn site-specific means, modes, scaling, or codes.
   Preserve valid zeros such as exang=0, fbs=0, and oldpeak=0. Retain finite
   oldpeak measurements as supplied, including negative external values, rather
   than deleting observations for being outside the training range. Report
   per-feature missingness, zero corrections, and retained ranges. Other
   nonpositive age/pressure/cholesterol/heart-rate values stop for review.

These matching and duplicate rules are record-level heuristics, not verified
patient identifiers. Residual duplicates or repeated patients can affect the
independence assumptions of uncertainty estimates. The exact matched primary
predictor fields use their raw source values before zero correction.

## Estimates and uncertainty

For the internal test and each external site separately, report sample size,
positive/negative counts, prevalence, TP/FN/TN/FP, sensitivity, specificity,
precision/PPV, NPV, ROC-AUC, average precision, and Brier score. Also report
FP/n and FN/n as fractions of all records; these are different from FP/negative_n
and FN/positive_n. Average precision is not trapezoidal PR area.

Use descriptive 95% Wilson intervals for sensitivity, specificity, PPV, and NPV.
Use 2,000 ordinary row-bootstrap resamples within each cohort for percentile 95%
intervals of ROC-AUC, AP, and Brier score, with fixed seeds 8100–8103. Keep the
model and cutoff fixed throughout resampling. A single-class bootstrap draw is
omitted for ROC-AUC/AP; record the number of valid replicates for each metric.
If the original cohort has one outcome class, ROC-AUC/AP stay undefined. Brier
uses all bootstrap replicates. Undefined rates remain blank, not zero.

These intervals condition on the fitted model/cutoff and sampled cohort. They do
not include model training/selection uncertainty, duplicated-patient dependence,
or prospective population transportability. Small negative counts, especially
in Switzerland, produce unstable specificity and other estimates. Do not assert
clinical safety from a high point estimate or crossing the 90% sensitivity target.

Use the same recorded sex-code and age bands (<50, 50–59, >=60) for final subgroup
summaries. Report denominators and Wilson intervals; include missing demographic
groups if present. Empty or single-class subgroup estimates remain undefined.
Flag denominators below 20. No subgroup retuning or fairness certification follows.

Plots: ROC/PR curves, five-bin calibration diagrams with bin counts, and a site
comparison with intervals. Calibration curves are descriptive; do not fit a new
calibrator from them. Prevalence lines in PR plots are site-specific references.

## Run locally in Windows PowerShell

The complete raw files from Day 1 must still be in data/raw. This download block
updates code and reviewed text files, not your model or raw data:

```powershell
Set-Location "$env:USERPROFILE\Downloads\heart-disease-day01-starter\heart-disease-ds"
$day8Base = "https://raw.githubusercontent.com/MucasLucas/UCI_Heart_Disease_Project/main"
$day8Files = @(
    "scripts/day08_final_evaluation.py",
    "scripts/frozen_artifact.py",
    "docs/day08_evaluation_protocol.md",
    "reports/day01/manifest.json",
    "reports/day06/accepted_freeze.json",
    "reports/day06/run_manifest.json"
)
foreach ($day8File in $day8Files) {
    Invoke-WebRequest -Uri "$day8Base/$day8File" -OutFile $day8File
}
```

Keep the same environment used for the frozen model. No new dependencies are
needed beyond the installed project requirements. If an input/hash/version check
fails, share the error and restore the verified input or environment. Do not
refit the model or modify a recorded hash to bypass the check.

Run when ready to expose the final evaluation outcomes:

```powershell
python scripts/day08_final_evaluation.py
$LASTEXITCODE
```

The script checks all source files and integrity before predictions. It prints
each site as evaluation proceeds and may take several minutes for bootstrap
intervals. Once it runs, internal test outcomes have been exposed: keep all
results regardless of quality and do not tune in response to them. An identical
successful rerun reuses verified saved outputs rather than generating new scores.
If a technical error interrupts evaluation, retain its logs/outputs and complete
the same fixed procedure; any substantive correction must be documented.

After exit code 0:

```powershell
python -m pip freeze | Out-File reports\day08\environment.txt -Encoding utf8
```

## Review gate

Paste terminal output and exit code. Upload from reports/day08:

- site_metrics.csv: point estimates, confusion counts, and uncertainty by cohort.
- predictions.csv: record IDs, outcomes, probabilities, cutoff, and predicted class.
- subgroup_metrics.csv: final subgroup denominators, rates, and intervals.
- cohort_audit.csv and exclusions.csv: the final analysis populations.
- missingness_and_cleaning.csv: exact pre-imputation zero and missing-value rules.
- roc_pr.png, calibration.png, and site_comparison.png.
- run_manifest.json: frozen artifact, source/output hashes, methods, and parameters.

Retain roc_pr_curves.csv, calibration_bins.csv, and environment.txt as well. The
manifest labels holdout_unlocked_for_final_evaluation=True; this is expected at
Day 8. The earlier Day 6/7 manifests correctly remain marked holdout_analyzed=False
for their historical development-only runs.

After review, document internal discrimination, operating-point errors and
uncertainty, calibration, site-specific transportability, missingness, subgroup
counts, and all limitations. Do not present cross-site testing as prospective
validation. Day 8 remains open until actual local outputs and interpretation
are reviewed and committed; then Day 9 writes the professional report.

## Implementation validation scope

Preparation tests use synthetic cohorts and known probabilities. They check
metric identities and zero/single-class cases; exclusion/zero rules; retention
of valid zeros and negative oldpeak; internal contamination rejection; subgroup
partitions; and plot rendering. No actual locked-test or external predictions
were generated during script preparation, and the separate reference bundle
was not substituted for the accepted local artifact.
