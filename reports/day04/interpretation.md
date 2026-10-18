# Day 4 baseline review

Completed October 17, 2026 (America/Los_Angeles). Lucas supplied the successful
Windows terminal run (exit code 0) and four generated CSVs. The review uses those
uploaded files, not substituted reference results. The study remains existing
CAD classification with 12 primary predictors excluding ca, in the later
workup setting.

## Baseline comparison

All performance below uses out-of-fold predictions on the same 242 development
records (111 CAD-positive, 131 CAD-negative). Classification threshold: 0.5.

| Model | ROC-AUC | Average precision | Brier | Sensitivity | Specificity | TN | FP | FN | TP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dummy prior | 0.4934 | 0.4551 | 0.2483 | 0.0000 | 1.0000 | 131 | 0 | 111 | 0 |
| Unweighted logistic | 0.8484 | 0.8251 | 0.1571 | 0.7297 | 0.8015 | 105 | 26 | 30 | 81 |
| Balanced logistic | 0.8486 | 0.8245 | 0.1579 | 0.7748 | 0.8015 | 105 | 26 | 25 | 86 |

The unweighted model improves ranking and probability-error metrics over the
no-information baseline. Development prevalence is 45.9%, providing context for
average precision. Dummy probabilities differ slightly between folds, explaining
why pooled dummy ROC-AUC is not exactly 0.5; within each fold it is 0.5.

Balanced weights increase sensitivity by 4.5 percentage points, reducing false
negatives from 30 to 25. A paired prediction check confirms exactly five positive
records switch from negative to positive and no negative records change class.
ROC-AUC changes by only about 0.0001, average precision is slightly lower, and
Brier score is slightly worse. These differences do not establish superiority.
Neither model reaches the proposed 0.90 sensitivity objective at this threshold.
No model or threshold is selected or frozen by this review.

## Fold variability

Unweighted ROC-AUC ranges from 0.7492 to 0.9073, sensitivity from 0.6087 to
0.7727, and specificity from 0.6154 to 0.9231. Balanced sensitivity ranges from
0.6957 to 0.8182. Fold 1 has the lowest ROC-AUC and specificity for both models.
Each fold has only 48–49 records, including 22–23 positives. A single outcome
therefore materially changes sensitivity. These ranges describe variation,
not confidence intervals. Do not remove or redesign the weakest fold in response.

## Coefficient interpretation

These are penalized, adjusted descriptions from separate fits on the full
242-record development cohort. They are not held-out performance estimates,
univariate effects, causal effects, or inferential significance tests.

- In unweighted logistic regression, a one-development-SD increase in maximum
  heart rate (thalach: 23.20 beats/minute) has an odds ratio of 0.661, holding
  other encoded predictors fixed: approximately 33.9% lower modeled CAD odds.
- A one-development-SD increase in oldpeak (1.178 original units) has an odds
  ratio of 1.832: approximately 83.2% higher modeled CAD odds, conditional on the
  other predictors.
- For a categorical example, exercise-induced angina code 1 versus code 0 has
  an odds ratio of 1.738, holding other predictors fixed. With full one-hot
  encoding, this contrast uses the difference between category coefficients.

Odds ratios do not describe equivalent percentage changes in probability.
Scaling uses the fitted population-standard-deviation convention of StandardScaler.
Regularization, correlations, and sparse categories limit coefficient stability.

## Verification and provenance

- Recomputed pooled and five-fold metrics for each model: 18 metric groups;
  all match the uploaded summaries within numerical tolerance.
- Confirmed 242 unique development IDs per model, one prediction per ID, valid
  probabilities, correct outcomes, and exact Day 3 fold assignments.
- Confirmed no locked-test IDs appear among the 726 prediction rows.
- All four uploaded tables match the independent reference calculation within
  numerical tolerance. Uploaded copies are committed unchanged.
- The uploaded files and reviewed script support development-only execution.
  No locked-test or cross-site performance was calculated in this review.
- Lucas's full local run_manifest.json and environment.txt were not uploaded.
  The earlier terminal log identifies Python 3.12 and scikit-learn 1.9.1, but
  this is not a substitute for the complete environment export. Those files
  remain provenance follow-ups, not blockers for completing the baseline review.

## Limitations and next step

The cohort is small, historical, and selected for diagnostic workup. These
exploratory development comparisons have no final holdout evaluation or reported
performance confidence intervals yet. A fixed, uncalibrated 0.5 threshold is a
baseline choice; class weighting can change probability calibration. Coefficients
are observational and penalized. Comparing models on these development folds
also creates selection uncertainty if the same results guide model choice.

Day 4 is complete: local execution, uploaded outputs, consistency checks, and
interpretation have been reviewed. Day 5 will compare Random Forest and XGBoost
under the same development-only evaluation framework, with tuning restricted to
inner training validation. Calibration and threshold selection remain Day 6 tasks.
The 61-record test set stays locked until the planned final evaluation.
