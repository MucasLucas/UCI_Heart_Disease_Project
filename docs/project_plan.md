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
- Day 6: complete; uploaded outputs reviewed; pooled policy metrics independently
  reconciled with 242 development predictions. Evaluation specification frozen
  as c06, no sigmoid calibration, cutoff 0.3528716233973672. See
  reports/day06/accepted_freeze.json and interpretation.md. Outer sensitivity
  was 0.8829, below the 0.90 target. Lucas supplied exit code 0 and a local
  checksum comparison returning True on October 20. The printed bundle hash
  matches the accepted freeze. The binary remains local, not independently
  inspected here; repeat checksum verification before future loads.
- Day 7: complete; seven uploaded outputs reviewed, including all three images.
  Six subgroup rows independently recomputed from Day 6 OOF policy predictions;
  12 global inputs and 36 local explanation rows checked against reference
  results. Accepted model identity/cutoff and source hashes match the manifest.
  See reports/day07/interpretation.md and review_checks.json. Full model/SHAP
  matrices and terminal exit code were not supplied; evidence limits are recorded.
- Day 8: complete numerical review with explicit provenance limits; 676 uploaded
  predictions reconcile with all four site point estimates and bootstrap intervals.
  Internal test IDs/labels and six internal subgroup rows independently verified;
  all 24 subgroup rows reconcile algebraically. Six CSVs and two PNGs match run
  checksums; the uploaded site-comparison PNG differs in bytes but visually agrees
  with the metrics. External raw/subgroup membership, local binary, terminal exit
  code and environment.txt were not independently supplied/reloaded for this review.
  See reports/day08/interpretation.md and review_checks.json. The internal test is
  now evaluated. Model and cutoff remain frozen; no retuning follows.
- Day 9: complete; professional report and editable source prepared using the
  reviewed final outputs. All ten PDF pages visually checked; 64 final metric
  values, five figures, full-precision cutoff, and DOI links verified. See
  reports/day09/report.pdf, report.md, report_checks.json, and docs/day09_procedure.md.
  No refitting, new predictions, or threshold changes. Existing evidence limits
  remain explicit; personal editorial feedback can be incorporated later.
- Day 10: report/evidence packaging complete on October 23; model card, one-page
  executive summary, README, environment/access instructions, deterministic
  release-candidate package and evidence verifier prepared. See
  reports/day10/review.json and docs/reproducibility.md. Accepted Windows binary
  and full original local environment exports remain unavailable; independent
  clean-environment accepted-model reproduction is pending. No tagged release
  is created while these gates remain open. All fitting and threshold choices
  remain frozen after test exposure.
- Current task: Lucas's minimal local artifact verification, followed by review
  of clean-install transcript and JSON. Day 10's full reproduction/release gate
  is explicitly partial; documentation and evidence deliverables are complete.
- Scope: existing coronary artery disease classification using UCI Heart Disease.
- Original October 14–23 schedule and completion gates remain in effect.


## Day 10 verification closure: October 23, 2026

Lucas supplied evidence-only and accepted-model verification JSON plus the full
current environment export. Hash reconciliation passed. His clean model
environment pip check reports no broken requirements and verifier exit code 0.
Local model verification reproduces all 676 probabilities, all four raw source
hashes and cohort/subgroup construction. See reports/day10/final_review.json.
This closes the requested local verification review; no tag/release has been
published. Remote review did not execute the binary. Original Day 8 transcript
absence, unresolved image provenance and historical/statistical limits remain
disclosed. Earlier gate entries above are retained as historical records.
