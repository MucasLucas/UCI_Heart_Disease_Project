# Reproducibility and artifact access

## Two verification levels

1. **Evidence-only:** recompute all four sites' point estimates and 2,000-draw
   bootstrap intervals from 676 saved probabilities, verify frozen decisions,
   internal split membership, original evaluation dependencies, reviewed artifact
   hashes and Day 9 report hashes. No raw files/model needed; no fitting occurs.
2. **Accepted-model reproduction:** independently restore the exact accepted
   Windows bundle and source bytes, restore its environment, reconstruct cohort
   membership and cleaning, reproduce all probabilities and final subgroup tables.
   This level is pending, not implied by passing the first level.

`requirements-evidence.txt` pins the tested evidence/report environment, not the
model environment. The Day 6/8 manifests record Python 3.12.10, NumPy 2.5.4,
pandas 2.3.3, scikit-learn 1.9.1 and joblib 1.6.0; Day 7 records SHAP 0.50.0.
These partial records do not capture every dependency, wheel, OS or numerical
library. `requirements.txt` is a historical broad-range specification, not a lock.
Do not install newer packages into the accepted model environment to render PDFs.

## Run evidence verification in a new environment

From a complete repository checkout, Python 3.12:

```powershell
python -m venv .venv-evidence
.\.venv-evidence\Scripts\python.exe -m pip install -r requirements-evidence.txt
.\.venv-evidence\Scripts\python.exe scripts\day10_verify.py --output reports\day10\local_evidence_verification.json
```

Linux/macOS use `.venv-evidence/bin/python`. Exit code 0 means the requested
checks passed; inspect JSON scope. Default status explicitly leaves model
verification pending. Recomputing intervals may take a minute. The checker writes
only its selected JSON, never Day 6-9 outputs. It preserves the known image
mismatch rather than silently accepting unrelated changes.

## Minimal local accepted-model verification (Lucas's Windows machine)

Use the existing project folder containing the original model and four raw inputs.
Download/checkout the committed Day 10 scripts into that folder first. Do not
re-run Day 6. Keep the original environment and artifacts unchanged.

```powershell
# Run with the ORIGINAL Python used for the accepted bundle.
New-Item -ItemType Directory -Force reports\day10 | Out-Null
python --version
python -m pip freeze | Out-File reports\day10\local_environment.txt -Encoding utf8
python -m pip check
python -m venv .venv-model-check
.\.venv-model-check\Scripts\python.exe -m pip install -r reports\day10\local_environment.txt
.\.venv-model-check\Scripts\python.exe -m pip check
.\.venv-model-check\Scripts\python.exe scripts\day10_verify.py --model --output reports\day10\local_model_verification.json
$LASTEXITCODE
```

Capture the terminal transcript, including install success and exit code 0, plus
`local_environment.txt` and `local_model_verification.json`. This captures the
current local environment; it does not retroactively establish a complete Day 6
training lock. If Python/package checks fail, restore the recorded original
runtime; report the error without refitting, bypassing checks, or substituting a
reference binary. Installation failure is a pending gate, not a reason to loosen
versions. `pip freeze` can contain private/local package paths: inspect before
sharing; preserve the original privately if a redacted copy is supplied.

`--model` verifies the SHA-256 before joblib deserialization, validates Pipeline
and forest parameters, checks exact source hashes, reproduces 676 saved
probabilities/decisions, cohort audit, exclusions, missingness and all 24 subgroup
rows, then rechecks model bytes. Only the known trusted original artifact may be
loaded; do not load arbitrary downloaded joblib files. No fitting or retuning is
performed, and no historical predictions are overwritten.

Do not use `day08_final_evaluation.py` as the Day 10 verifier: its reuse guard
correctly rejects the preserved site-comparison PNG mismatch and reconstructed
curve/bin bytes. Do not alter its historical manifest to hide that discrepancy.

## Access and known evidence limits

- Repository contains reviewed predictions, tables, report and code. It does not
  contain `models/day06_candidate.joblib`, four raw source files, full Windows
  environment exports, or the original Day 8 terminal transcript.
- Obtain unchanged processed cohorts from the UCI source documented in
  `data/raw/README.md`; all source hashes must match Day 1. Differences in line
  endings change SHA-256; preserve original bytes. Do not silently normalize raw
  inputs or rewrite historical manifests.
- The committed split's Day 9 hash differs from the original Windows CSV hash
  recorded on Day 6/8. Historical CSV line-ending normalization is disclosed in
  the report. Evidence checks verify the committed Day 9 hash; cohort reproduction
  verifies IDs/partition and raw labels rather than pretending original bytes.
- Three Day 5-7 interpretation source hashes recorded during Day 9 match the
  committed prose with one additional terminal blank line; this is recorded as
  text equivalence, not byte identity. Day 8 CSV/manifest CRLF-to-LF transport
  differences are likewise retained in the Day 10 verification JSON.
- External raw bytes and demographic memberships were not independently reloaded
  in prior numerical review. A successful future `--model` check would supply new
  evidence, without changing the older review's historical scope.
- `site_comparison.png` remains byte-discrepant. The report excludes it; preserved
  expected/received hashes are in `reports/day08/review_checks.json`.
- Curve/bin CSVs were reconstructed from uploaded probabilities, not supplied
  original local bytes. Broad requirements and a reference model cannot establish
  identity of the accepted Windows artifact.

## Tagged release gates

No tagged verified release is authorized until all of these pass:

| Gate | Current status |
|---|---|
| Evidence verification in a new environment; dependency check | See reports/day10/verification.json and environment evidence |
| Report/model-card/summary consistency and visual PDF review | Recorded in reports/day10/review.json |
| Exact accepted binary available and SHA-256 validated independently | Pending |
| Full current local environment captured; clean install and pip check recorded | Pending |
| Clean-environment `--model` probabilities, sources, exclusions and subgroups pass | Pending |
| Local transcript/results reviewed; provenance limits carried into release notes | Pending |

The image discrepancy need not be erased for a transparent release; preserve and
explicitly disclose it. Do not call the package fully reproducible while model
verification is pending. No tag or GitHub release is created in this state.
The deterministic ZIP is a **release candidate / evidence package**, not a
verified model release. It excludes raw data, models, local environment exports,
and scratch files. Its per-file hashes identify exact packaged bytes. To rebuild:
`python scripts/build_day10_package.py` from a complete checkout.
