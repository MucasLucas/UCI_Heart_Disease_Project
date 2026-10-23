# Interpretable Coronary Artery Disease Classification

**A frozen-model study of cross-site transportability using UCI Heart Disease.**
Built by Lucas Medina. Strong internal performance did not translate into
consistent external specificity or probability calibration.

**Status:** report and Day 10 evidence package complete; accepted-model clean-
environment reproduction and a tagged release are pending local artifacts.
The 61-record test has been evaluated. The accepted c06 Random Forest and cutoff
`0.3528716233973672` remain frozen; no retuning follows.

## Read the project

- [Research report: 10-page PDF](reports/day09/report.pdf) / [editable source](reports/day09/report.md)
- [One-page executive summary](reports/day10/executive_summary.pdf) / [source](reports/day10/executive_summary.md)
- [Model card](docs/model_card.md)
- [Reproducibility, artifact access and exact local commands](docs/reproducibility.md)
- [Release-candidate evidence package](reports/day10/release_candidate.zip)
- [Day 10 checks and remaining gates](reports/day10/review.json)

## Final results

| Cohort | n | ROC-AUC (95% interval) | Sensitivity | Specificity |
|---|---:|---|---:|---:|
| Cleveland test | 61 | 0.957 (0.907-0.990) | 92.9% | 78.8% |
| Hungarian | 293 | 0.903 (0.864-0.939) | 92.5% | 67.4% |
| Switzerland | 123 | 0.766 (0.591-0.925) | 88.7% | 50.0% |
| VA Long Beach | 199 | 0.721 (0.639-0.799) | 93.9% | 23.5% |

At VA, 39/51 negatives were flagged. The Swiss sex=0 subgroup detected 3/10
positives; small counts and uncertainty require attention. All 676 saved
predictions are available. [Full estimates and intervals](reports/day08/site_metrics.csv)
and [subgroups](reports/day08/subgroup_metrics.csv) preserve denominators.

The exploratory 90% sensitivity objective was not met by the nested development
selection policy (88.3%). Final internal sensitivity has a 77.4%-98.0% interval.
Conditional intervals exclude model-selection uncertainty. These results establish
neither clinical utility nor a guaranteed sensitivity target.

## What was built

- Fold-fitted preprocessing with logistic, Random Forest and XGBoost comparisons.
- Development-only calibration and threshold selection, followed by frozen evaluation.
- Separate internal/external estimates, Wilson/bootstrap intervals and calibration plots.
- SHAP explanations, recorded-sex/age subgroup review, and explicit provenance checks.

The target is **existing CAD**, not future cardiovascular risk. Twelve historical
later-workup predictors exclude `ca`; feature timing remains unverified. This is
an educational portfolio study, with no clinical deployment or AHA endorsement.
See the [protocol](docs/protocol.md) and [predictor dictionary](docs/data_dictionary.csv).

## Verify the saved evidence

Python 3.12, from this directory:

```powershell
python -m venv .venv-evidence
.\.venv-evidence\Scripts\python.exe -m pip install -r requirements-evidence.txt
.\.venv-evidence\Scripts\python.exe scripts\day10_verify.py --output reports\day10\local_evidence_verification.json
```

Linux/macOS: use `.venv-evidence/bin/python`. This recomputes saved-probability
metrics/intervals and verifies reviewed hashes. It neither loads nor fits a model.
The separate evidence environment is not a replacement for the frozen Windows
model environment. See [reproducibility.md](docs/reproducibility.md) for the optional
accepted-artifact check and release gates. Avoid rerunning training scripts now
that test outcomes are exposed.

## Evidence and access limits

The accepted Windows binary is local and not distributed. Full local environment
exports and Day 8 terminal evidence are missing; partial package versions are
recorded in manifests. Prior review did not independently reload external raw
bytes/demographics. The uploaded site-comparison PNG does not match its manifest
hash; both hashes and retained bytes remain preserved. The report uses the
checksum-matching ROC/PR and calibration figures instead. Reconstructed curve/bin
CSVs are identified as derived evidence. These limits block a verified tagged
release, not access to the report or numerical evidence.

Raw processed UCI files are Git-ignored; a clone does **not** include them. Source
access/hashes are documented in [data/raw/README.md](data/raw/README.md) and Day 1's
manifest. No reference model may replace the accepted evaluated binary.

## Repository map

| Path | Contents |
|---|---|
| docs/ | Protocol, data dictionary, daily procedures, model card and reproducibility |
| scripts/ | Audit, preprocessing, comparisons, selection, explanations, evaluation and packaging |
| reports/day01-day07/ | Audit, frozen split, development evidence and accepted specification |
| reports/day08/ | Final predictions, metrics, cohorts, figures and provenance review |
| reports/day09/ | Research report, editable source and report checks |
| reports/day10/ | Executive summary, verification and candidate package |

[Project plan and gate status](docs/project_plan.md). No new code license is
asserted; data terms are separate. Dataset attribution: Janosi, Steinbrunn,
Pfisterer and Detrano, *Heart Disease*, UCI Machine Learning Repository (1989),
DOI [10.24432/C52P4X](https://doi.org/10.24432/C52P4X). The report records UCI's
CC BY 4.0 data terms and methodological references.
