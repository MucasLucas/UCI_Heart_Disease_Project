# Model card: c06 coronary artery disease classifier

**Owner:** Lucas Medina. **Card date:** October 23, 2026.
**Status:** historical educational study; report and evidence package available.
Accepted-artifact reproduction in a clean environment remains pending.

## Intended use and target

Classify existing coronary artery disease (CAD) in historical UCI Heart Disease
records: `num > 0` versus `num = 0`. This is a later-workup research setting,
not future heart-disease risk prediction. The audience is technical reviewers
and healthcare analytics hiring teams. No prospective clinical workflow,
screening/triage use, treatment recommendation, or AHA endorsement is established.
Record-level predictor timing before diagnosis is unverified.

## Model identity and interface

| Item | Frozen value |
|---|---|
| Candidate | c06, RandomForestClassifier within preprocessing Pipeline |
| Training cohort | 242 Cleveland development records |
| Trees / depth / minimum leaf | 200 / unlimited / 3 |
| Feature sampling / weights / seed / jobs | sqrt / none / 42 / 1 |
| Added probability calibration | None |
| Positive decision | `probability >= 0.3528716233973672` |
| Local binary | `models/day06_candidate.joblib` (not distributed) |
| SHA-256 | `948f8939076cdc1e001a74d7bb414b28c88e21b7de32b0a2172fdc4a805ce1ae` |

Input columns, in order: `age`, `trestbps`, `chol`, `thalach`, `oldpeak`,
`sex`, `cp`, `fbs`, `restecg`, `exang`, `slope`, `thal`. Units and category codes
are in [data_dictionary.csv](data_dictionary.csv). `ca` is excluded. The pipeline
median-imputes and standardizes continuous inputs, mode-imputes and one-hot
encodes categorical inputs with unknown-category handling. All transformations
are fitted on development records; the class-1 probability is the output.

External `chol`/`trestbps` zeros become missing before the frozen imputer;
other legitimate zeros and finite negative `oldpeak` values remain. Exact full
external duplicate rows keep the first, and primary-predictor matches to any
Cleveland record are excluded. These are record heuristics, not patient identity.
The rules were documented before final predictions on Day 8, not all on Day 1.

## Selection and evaluation

Day 6 compared logistic regression and four forest settings, each with/without
sigmoid calibration. Within each outer training fold, select maximum specificity
at sensitivity >=90%; break candidate ties by Brier then ID. Within a candidate,
use the highest feasible cutoff at maximum specificity. The nested policy yielded
88.3% sensitivity and 62.6% specificity, below the objective. Full-development
selection reached 90.1%/67.2%; these selection scores are not independent
performance estimates. Earlier model-family shortlisting reused development
evidence. Final model/cutoff were frozen before Day 8 test exposure.

| Final cohort | n | ROC-AUC (95% interval) | Sensitivity | Specificity | TP/FN/TN/FP | Brier |
|---|---:|---|---:|---:|---|---:|
| Cleveland test | 61 | 0.957 (0.907-0.990) | 92.9% | 78.8% | 26/2/26/7 | 0.099 |
| Hungarian | 293 | 0.903 (0.864-0.939) | 92.5% | 67.4% | 98/8/126/61 | 0.133 |
| Switzerland | 123 | 0.766 (0.591-0.925) | 88.7% | 50.0% | 102/13/4/4 | 0.211 |
| VA Long Beach | 199 | 0.721 (0.639-0.799) | 93.9% | 23.5% | 139/9/12/39 | 0.200 |

See [site_metrics.csv](../reports/day08/site_metrics.csv) for full rate intervals,
AP, PPV and NPV. Wilson rate intervals and 2,000 within-site bootstrap draws are
conditional on the fitted model; they exclude model-selection/training uncertainty.
Single-class AUC/AP draws are omitted. Switzerland has only eight negatives.
Internal sensitivity's 95% interval is 77.4%-98.0%; 90% is not guaranteed.
AP depends on prevalence; the sites must not be pooled or ranked using AP alone.

## Explanation and subgroup evidence

Tree-path SHAP on development training records attributes predictions mainly to
`thal`, `cp`, and `slope`. It is descriptive, not causal or validation evidence.
One-hot contributions are summed to inputs rather than recomputing grouped
coalition values. Day 7 subgroup metrics assess the OOF selection policy; Day 8
subgroups assess the final frozen model. Do not mix them.

The final Swiss sex=0 subgroup detected 3/10 positives (95% Wilson interval
10.8%-60.3%); its specificity is undefined with no negatives. VA sex=1 specificity
is 10/48 (20.8%). Sparse groups and uncertain external demographic memberships
limit interpretation, without making missed cases unimportant. No fairness
certification or formal adjusted disparity analysis is claimed.

## Limitations and access

- Historical referral populations, uncertain predictor timing, small internal
  test and sparse external groups limit transportability.
- Missingness shifts are large: Swiss cholesterol is entirely unavailable;
  Hungary/VA have extensive missing workup inputs. Calibration differs by site.
- No clinical utility, cost saving, causal effect, or prospective benefit was measured.
- Accepted Windows binary has not been independently supplied/reloaded. Earlier
  local checksum evidence and submitted manifests support its identity. A Linux
  reference bundle must never replace it.
- Full local environment exports and Day 8 exit-code evidence were not supplied.
  Manifest versions are partial records, not a complete dependency lock.
- External raw bytes and demographic memberships were not independently reloaded
  in the numerical review. The site-comparison PNG differs from its run hash;
  retained bytes and the discrepancy remain documented.

The public repository contains code, reviewed probabilities, tables and report;
raw data and model are excluded. Data attribution: Janosi, Steinbrunn, Pfisterer,
Detrano, UCI Heart Disease, DOI [10.24432/C52P4X](https://doi.org/10.24432/C52P4X).
The report records UCI's CC BY 4.0 data terms. Dataset terms do not license project
code; no new code license is asserted by this card. See
[reproducibility.md](reproducibility.md) for access, environment and verification.
Any future adaptation requires separately reserved validation data; exposed
cohorts cannot serve as a new untouched test set.
