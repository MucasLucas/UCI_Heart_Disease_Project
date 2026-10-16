# Ten-day project plan

Dates: October 14–23, 2026, America/Los_Angeles. Budget: approximately 2–3 focused
hours daily; allow 3–4 hours on evaluation and report days. Each day must pass
review before advancing. A reminder never marks work complete. If a gate slips,
trim optional ablations and visualization polish before sacrificing validation.

| Day | Date | Work | Completion gate |
|---|---|---|---|
| 1 | Oct 14 | Source audit, target definition, protocol, frozen split | Local audit reviewed; anomalies documented; target and feature timing accepted; commit |
| 2 | Oct 15 | Development-only clinical EDA | Table 1, missingness and distributions with clinical interpretations; commit |
| 3 | Oct 16 | Pipelines, feature sets, imbalance strategy | Fold-fitted imputation/encoding; no leakage; documented feature availability; commit |
| 4 | Oct 17 | Dummy and regularized logistic regression | Reproducible development CV, sensitivity/specificity and coefficient interpretation; commit |
| 5 | Oct 18 | Random Forest and XGBoost | Comparable CV, bounded tuning, no holdout access; commit |
| 6 | Oct 19 | Calibration and threshold selection | Development-only calibration/threshold tradeoff; freeze model and decision rule; commit |
| 7 | Oct 20 | SHAP and subgroup review | Global/local explanations, recorded sex/age counts and uncertainty; commit |
| 8 | Oct 21 | Locked internal and cross-site evaluation | ROC/PR, AP, sensitivity/specificity, calibration, uncertainty; no retuning; commit |
| 9 | Oct 22 | Professional report | Abstract, methods, results, clinical interpretation, limitations, citations; commit |
| 10 | Oct 23 | GitHub and reproducibility | Fresh-environment run, README, model card, executive summary, tagged release; commit |

## Report outline
Title; structured abstract; clinical question and intended use; source cohorts and
eligibility; predictor timing; outcome definition; leakage controls; statistical
analysis; results with confidence intervals; explanation and subgroup analysis;
clinical implications; limitations; reproducibility; references and attribution.

## Review contract
For every day: explain why the step matters, supply runnable Python, ask Lucas to
run it, review real outputs/errors, record decisions, and create a descriptive Git
commit. Never invent results or advance solely because the calendar changes.
Direct GitHub pushes require a specified accessible repository and reviewed work.

## Progress
- Day 1: local audit and protocol reviewed; committed as b460a31.
- Day 2: local EDA returned exit code 0; uploaded tables and figure reviewed;
  documentation and reproducible reference outputs prepared for commit.
- Next gate: Day 3 preprocessing and predictor availability.
