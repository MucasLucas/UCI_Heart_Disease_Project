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
- Day 2: complete; local EDA returned exit code 0; uploaded tables and figure
  reviewed; interpretation and reproducible outputs committed as 2b96f81.
- Day 3: complete; Lucas's local five-fold preprocessing run returned exit code 0
  and matched the reference results. On October 16, 2026, Lucas confirmed the
  12-predictor later-workup setting excluding ca, unweighted baseline without
  automatic oversampling, and retention of extreme observations pending verification.
  See reports/day03/README.md. Local environment.txt upload remains a provenance
  follow-up, not a modeling gate.
- Day 4: complete; local baseline execution returned exit code 0. Four uploaded
  CSVs reviewed and 18 metric groups independently reconciled against 726
  development-only predictions. Interpretation recorded in
  reports/day04/interpretation.md. No model or threshold selected.
  Local environment and run-manifest uploads remain provenance follow-ups.
- Day 5: complete; five uploaded CSVs reviewed. All 1,210 predictions reconcile
  with 30 metric groups. Inner assignments exclude outer validation and 40 search
  candidates match the prespecified grids. Selected parameters reconstructed from
  uploaded search results. See reports/day05/interpretation.md. Local manifest,
  environment, and terminal exit-code evidence remain provenance follow-ups.
- Current task: Day 6 calibration and threshold selection using development data.
  No final model, calibrator, configuration, or decision threshold is selected yet.
- Scope: existing coronary artery disease classification using UCI Heart Disease.
- Original October 14–23 schedule and completion gates remain in effect.
