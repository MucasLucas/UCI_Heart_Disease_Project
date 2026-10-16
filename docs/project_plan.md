# Ten-day project plan

Dates: October 14–23, 2026, America/Los_Angeles. Budget: approximately 2–3 focused
hours daily; allow 3–4 hours on evaluation and report days. Each day must pass
review before advancing. A reminder never marks work complete. If a gate slips,
trim optional ablations and visualization polish before sacrificing validation.

| Day | Date | Work | Completion gate |
|---|---|---|---|
| 1 | Oct 14 | Source audit, target definition, protocol, frozen split | Local audit reviewed; anomalies documented; target and feature timing accepted; commit |
| 2 | Oct 15 | Development-only clinical EDA | Table 1, missingness and distributions with clinical interpretations; commit |
| 3 | Oct 16 | Dual-objective protocol, longitudinal-data audit, CAD pipelines | Verified longitudinal source/use/endpoint or explicit access blocker; fold-fitted CAD preprocessing; commit |
| 4 | Oct 17 | CAD dummy/logistic baseline; future-risk baseline if data gate passes | Reproducible development validation and correct censoring/competing-risk strategy; commit |
| 5 | Oct 18 | Focused model comparison for available cohorts | Comparable validation; bounded tuning; no holdout access; prioritize rigor over number of models; commit |
| 6 | Oct 19 | Calibration, CAD threshold, future-risk horizon | Development-only calibration; freeze models and decisions separately; commit |
| 7 | Oct 20 | SHAP and subgroup review | Global/local explanations, recorded sex/age counts and uncertainty; commit |
| 8 | Oct 21 | Separate locked evaluations; CAD cross-site stress test | CAD metrics; censoring/competing-risk-aware future metrics if available; uncertainty; no retuning; commit |
| 9 | Oct 22 | Report with separate diagnostic/prognostic sections | Separate endpoints, cohorts, limitations and references; no future-risk results without data; commit |
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
  interpretation, script, and reproducible reference outputs committed as 2b96f81.
- Day 3: objective amended; longitudinal documentation/access audit completed.
  Participant-data audit blocked pending official data and use verification.
- Next gate: obtain a permitted longitudinal source; proceed with leakage-safe
  CAD preprocessing independently while access is pending.

The October 23 target remains, but two completed models depend on prompt data
access. If the prognostic source is delayed, document the extension transparently.
