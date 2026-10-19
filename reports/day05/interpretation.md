# Day 5 tree-model review

Reviewed October 18, 2026 (America/Los_Angeles). Lucas uploaded five CSVs:
pooled metrics, fold metrics, predictions, inner-search results, and inner-fold
assignments. The original three filenames containing (1) are stored under their
standard project names. Their source hashes are in review_checks.json.

## Comparison

All scores use the same 242 development records and five outer validation folds.
Tree parameters were selected using three inner folds inside each outer training
set. The outcome is existing CAD. All models use the 12 primary predictors
excluding ca. Classification threshold remains fixed at 0.5.

| Model | ROC-AUC | Average precision | Brier | Sensitivity | Specificity | FN | FP |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dummy prior | 0.4934 | 0.4551 | 0.2483 | 0.0000 | 1.0000 | 111 | 0 |
| Unweighted logistic | 0.8484 | 0.8251 | 0.1571 | 0.7297 | 0.8015 | 30 | 26 |
| Balanced logistic | 0.8486 | 0.8245 | 0.1579 | 0.7748 | 0.8015 | 25 | 26 |
| Nested Random Forest | 0.8660 | 0.8552 | 0.1546 | 0.7477 | 0.8321 | 28 | 22 |
| Nested XGBoost | 0.8485 | 0.8345 | 0.1572 | 0.7117 | 0.8244 | 32 | 23 |

Random Forest has the highest pooled ROC-AUC and AP and the lowest Brier score
among these candidates. Relative to unweighted logistic regression, ROC-AUC is
higher by 0.0176 and AP by 0.0300. It has two fewer false negatives and four fewer
false positives at 0.5. Relative to balanced logistic regression, it trades three
additional false negatives for four fewer false positives. It is a candidate for
further assessment, not a selected final model.

XGBoost ROC-AUC is essentially the same as unweighted logistic regression. AP is
higher by 0.0094, while Brier score is slightly worse. At 0.5, XGBoost has two
additional false negatives and three fewer false positives than unweighted
logistic regression. More model flexibility has not produced a clear improvement
across all metrics.

No model reaches the exploratory 0.90 sensitivity objective at this threshold.
The highest sensitivity is balanced logistic regression at 0.7748. Keep model
ranking, probability calibration, and decision-threshold performance separate.

## Variation across folds and selected settings

Random Forest fold ROC-AUC ranges from 0.8010 to 0.9073, sensitivity from 0.6957
to 0.8182, and specificity from 0.7308 to 0.9231. XGBoost fold ROC-AUC ranges
from 0.7701 to 0.9091, sensitivity from 0.6522 to 0.7727, and specificity from
0.7692 to 0.8846. These are descriptive ranges, not confidence intervals.
Random Forest does not beat unweighted logistic ROC-AUC in every fold.

Reconstructed inner-CV winners, using the documented first-candidate tie rule:

| Outer fold | Random Forest max_depth | Random Forest min_samples_leaf | XGBoost max_depth | XGBoost n_estimators |
|---|---|---|---|---|
| 1 | 3 | 8 | 1 | 250 |
| 2 | 3 | 3 | 1 | 250 |
| 3 | 3 | 8 | 2 | 250 |
| 4 | None | 8 | 2 | 250 |
| 5 | None | 8 | 2 | 250 |

Settings vary across outer training sets. Some inner ROC-AUC differences are
very small, especially for Random Forest in fold 5. Do not treat the most
frequently selected configuration as a globally tuned winner. The nested scores
evaluate a training-and-selection procedure, not one globally fixed fitted model.

## Verification and provenance

- Recomputed 30 metric groups: five pooled and 25 per-fold summaries. All
  reconcile with the 1,210 uploaded out-of-fold predictions within tolerance.
- Each model has exactly one prediction for each of the 242 development IDs.
  Outcomes and outer-fold membership match the frozen development cohort.
  No locked-test IDs appear in the prediction table.
- Checked all 968 inner-assignment rows. Each outer training record has one inner
  validation assignment, both classes occur in each inner training/validation
  partition, and identical predictor groups stay together. Outer validation
  records are absent from that outer fold's inner assignments.
- Checked all 40 search rows against the prespecified four configurations per
  family per outer fold. Inner score means, population SDs, and ranks reconcile.
- Derived selected_parameters.csv from the uploaded candidate scores using the
  documented deterministic selection rule. It was not separately uploaded.
- All five uploaded tables match the independent reference run within numerical
  tolerance. The reviewed script fits preprocessing inside each inner pipeline.
  Membership tables alone cannot prove execution order, but they are consistent
  with that script and the independent reproduction.
- Local run_manifest.json, environment.txt, and terminal exit code were not
  supplied. Do not describe the reference manifest as Lucas's local environment.
  These remain provenance follow-ups; substantive output review has passed.

## Limitations and next step

Only 48–49 records are evaluated per outer fold. Pooled scores and small ranking
differences remain uncertain, with no significance claim or final-test estimate.
Model families were compared on development results, introducing selection
uncertainty if those scores guide the final choice. These historical referral
patients and later-workup predictors do not represent population screening.
Probabilities are uncalibrated and the 0.5 threshold is provisional. Nested tuning
controls parameter-search leakage but does not establish clinical readiness.

Day 5 output review is complete. No final model family, configuration, calibrator,
or threshold is selected or frozen by this review. Day 6 will evaluate calibration
and sensitivity/specificity tradeoffs using development-only validation, then
record the final training and decision rule before any locked-test evaluation.
The 61-record internal test and cross-site cohorts remain outside this review.
