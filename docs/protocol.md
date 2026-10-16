# Study protocol — dual objectives, amended before modeling

## Research question
How well can interpretable models identify existing angiographic coronary artery
disease in the historical Cleveland referral cohort, and how does performance
change in other UCI cohorts with different case mix and data completeness?

The UCI component is a retrospective educational diagnostic classification study.
It does not estimate future myocardial infarction, mortality, or 10-year ASCVD risk.
It does not establish clinical readiness, AHA endorsement, or treatment benefit.

## Added objective: future cardiovascular event risk
Requested October 15, 2026. Add an independent longitudinal cohort and model for
future event risk; never reinterpret UCI `num` or its prediction as a future label
or risk estimate. Preserve the existing UCI split and all diagnostic-study rules.
The Framingham longitudinal teaching source is a candidate pending access and
use verification; its documentation warns against publication use. See
`reports/day03/future_risk_source_audit.md` for findings and the blocked data gate.

Provisional target: ten-year cumulative incidence of the source-defined first CVD
event in participants without baseline CHD or stroke. Confirm endpoint, follow-up,
and eligibility against the actual file before freezing this target. Use one
baseline exam per participant, baseline predictors only, and a separate participant
split. Account for early censoring and competing death; do not code early censoring
as a ten-year non-event. Evaluate horizon-specific calibration and discrimination
with uncertainty. A Cox survival probability alone is not automatically a
competing-risk cumulative incidence estimate.

Keep cohort definitions, preprocessing, models, calibration, performance claims,
and report sections separate for the two objectives. No patient linkage across
unrelated sources. Source counts and suitability review are not a completed
participant-data audit. If data access or permitted use cannot be resolved within
the project, report this objective as an uncompleted extension, not a trained model.

## Outcome and sources
Use original UCI processed files with 13 predictors and num. Binary outcome:
num=0 maps to 0; num in {1,2,3,4} maps to 1. Validate num before binarizing.
Preserve num for provenance; never include num as a predictor.
Use processed Cleveland (303), Hungary (294), Switzerland (123), and VA (200).
The original unprocessed Cleveland file is documented as corrupted.
Do not treat differently processed copies as independent patients.

## Predictor availability
Primary clinically motivated analysis: pre-angiography information, excluding
ca because it is angiography-related. Exercise-test variables and thal require
an explicitly later diagnostic-workup setting; thal is a test result, not a
thalassemia diagnosis. Verify timing against documentation and acknowledge
that record-level timestamps are unavailable.
Secondary: conventional 13-feature benchmark, explicitly labeled as including
angiography-related information with possible target proximity/leakage.
Optional ablation: basic presentation features only (age, sex, cp, trestbps,
chol, fbs, restecg). No smoking, BMI, HDL, or longitudinal outcome is supplied
in the processed feature set; do not invent them.

## Validation
Use Cleveland for development with a frozen approximately 20% internal holdout.
Freeze the first fold of seeded five-fold stratified group splitting; identical
predictor rows stay together. Exact matching does not prove patient identity:
processed files do not support definitive patient-level deduplication.
Inspect cross-site exact matches and predefine their exclusion from external
evaluation if they overlap development; document limitations of this heuristic.
Development-only EDA informs feature and preprocessing choices. Cross-site files
are audited for schema/missingness now but are not used for tuning.

Within development, fit preprocessing, feature engineering, imbalance handling,
and tuning within training folds. Use regularized logistic regression, Random
Forest, and XGBoost with a fixed small tuning budget and dummy baseline.
Prefer class-weight comparisons to automatic SMOTE; resampling, if used, belongs
inside training folds only. Encode nominal numeric codes as categorical values.
Audit zero-valued physiologic measurements; justify treatment without replacing
valid zeros in other variables. Do not silently delete extreme observations.

For performance estimation, use nested CV where feasible: tune models,
calibration, and thresholds inside outer training folds; assess on outer held-out
folds. Estimate the final threshold using cross-fitted development predictions.
Fit any calibrator only with development data using internal CV; never calibrate
on the final holdout. Freeze the full pipeline and threshold before Day 8.

## Decision objective and metrics
Exploratory engineering objective: sensitivity >=0.90 on development validation,
then maximize specificity among qualifying thresholds. This is a proposed study
constraint, not an AHA recommendation or demonstrated safety target. If it is
infeasible or uncertainty is broad, report that plainly. Do not change it to make
test performance look better. Discuss false negatives and false-positive referral
burden together; higher sensitivity alone does not establish utility.

Report sensitivity, specificity, PPV/precision, NPV, confusion matrix counts,
ROC-AUC, precision-recall curves and average precision (AP), Brier score, and
calibration plots. AP and trapezoidal PR-AUC are distinct; name the estimator.
Include the prevalence reference for PR performance. Bootstrap uncertainty for
continuous performance measures and suitable binomial intervals for sensitivity
and specificity; quantify instability from the small test sample. Bootstrap
intervals conditional on the fitted model do not capture all training uncertainty.

Final evaluation: one locked internal test and untouched cross-site evaluation
as a retrospective transportability stress test, not prospective validation.
Report subgroup counts and intervals by recorded sex and prespecified age bands;
sparse subgroups cannot establish fairness. Protected/site attributes used for
auditing are not automatically model inputs. Do not pool site results alone.

## Explanation and reporting
Logistic regression is inherently interpretable conditional on its specification;
Random Forest and XGBoost require post-hoc explanation. Provide odds ratios with
appropriate scaling and SHAP global/local explanations using development-only
background data. Explain score/probability scale. SHAP is not causal evidence.
Use a descriptive Table 1, missingness figure, ROC/PR curves, calibration plot,
threshold tradeoff, SHAP plot, and site/subgroup results in the final report.
Discuss selection bias, historical data, sample size, missingness, feature timing,
and the lack of prospective and deployment validation.

## Attribution
UCI Heart Disease, DOI 10.24432/C52P4X. Acknowledge Andras Janosi,
William Steinbrunn, Matthias Pfisterer, and Robert Detrano as requested by the
source documentation. Reference Detrano et al. (1989), American Journal of
Cardiology 64:304–310. Copy the exact license from the current UCI source before
redistributing data; repository code licensing and dataset licensing are separate.
