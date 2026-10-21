# Day 6 review and accepted project freeze

Reviewed October 19, 2026 (America/Los_Angeles), using Lucas's seven uploaded
outputs. The previously reported image-path error is resolved: the supplied PNG
is accessible, readable, and visually consistent with the tabulated results.
The original candidate_freeze.json is retained unchanged. accepted_freeze.json
records the reviewed rule for subsequent project evaluation.

## Keep performance and selection scores separate

| Analysis | Sensitivity | Specificity | TP | FN | TN | FP |
|---|---:|---:|---:|---:|---:|---:|
| Nested selection-policy outer validation | 0.8829 | 0.6260 | 98 | 13 | 82 | 49 |
| Final candidate threshold-selection scores | 0.9009 | 0.6718 | 100 | 11 | 88 | 43 |

The outer assessment evaluates the entire candidate/calibration/cutoff selection
procedure. Its ROC-AUC is 0.8418, AP 0.8149, and Brier score 0.1598. It does not
meet the exploratory 0.90 sensitivity objective. The selection scores describe
how the final candidate and cutoff were chosen from development data. They are
not independent performance estimates of the fitted final model. There are no
locked-test results yet. Do not present selection sensitivity as validated safety.

At the outer-validation operating points, 49 of 131 CAD-negative records were
classified positive (37.4%). This burden must accompany the increased sensitivity.
The outer policy uses different models/cutoffs across folds, so it is not the
same fixed-model assessment as Day 5's 0.5-threshold comparisons. Do not attribute
all differences to lowering one common cutoff.

## Accepted specification for project evaluation

- Candidate c06: Random Forest, 200 trees, max_depth=None,
  min_samples_leaf=3, max_features=sqrt, no class weights, seed 42.
- No additional sigmoid calibration.
- Complete pipeline: training-fitted numeric median imputation and scaling;
  categorical mode imputation and full one-hot encoding with unknown categories
  ignored. Same 12 later-workup predictors; ca remains excluded.
- Classify positive iff probability >= 0.3528716233973672. Preserve full precision.
- Fitted on all 242 development records. Retain the exact local bundle at
  models/day06_candidate.joblib; do not refit or alter the rule after test access.
- Local reported bundle SHA-256:
  948f8939076cdc1e001a74d7bb414b28c88e21b7de32b0a2172fdc4a805ce1ae

The accepted record binds the evaluation specification to Lucas's reported local
bundle identity. The binary was not uploaded, so its checksum and contents have
not been independently inspected here. Verify the local file against that hash
before loading it for explanations or final evaluation. The independent reference
bundle is a different file and is not a substitute for Lucas's frozen artifact.
Acceptance is for the educational evaluation, not clinical deployment or evidence
that the sensitivity objective has been achieved on unseen patients.

## Calibration and selection stability

c06 and c07 (the corresponding sigmoid-calibrated forest) share selection
specificity 0.6718 at sensitivity 0.9009. The tie is broken by Brier score:
0.1494065 for c06 versus 0.1495604 for c07. The small difference supports the
prespecified deterministic choice, not a significance claim.

Calibration helped probability-error scores for some other specifications. For
example, shallow forest c02 Brier 0.1556099 improved to 0.1493167 for calibrated
c03, and logistic c00 0.1571434 improved to 0.1553309 for calibrated c01.
Therefore, do not claim calibration never helps or is always necessary.

The calibration figure shows five probability bins without uncertainty bands.
Visual proximity to the diagonal does not establish reliable calibration in a
small cohort. Its right panel is a final-selection tradeoff, not a test curve.

Outer training sets selected c00 twice, c02 once, c07 once, and c06 once. Cutoffs
range from approximately 0.2106 to 0.3578; they span different fitted probability
scales and are not interchangeable. This variation indicates selection instability.
No outer-validation results were used to adjust the documented selection rule.

## Verification and limitations of supplied evidence

- Recomputed all pooled policy metrics from 242 uploaded prediction rows.
  IDs, outcomes, outer folds, probabilities, and per-fold cutoffs reconcile.
  No locked-test IDs occur in these predictions.
- Checked the ten final candidate summaries against confusion-count denominators
  and reconstructed the winning summary under the specified specificity/Brier/ID
  ordering. The uploaded freeze agrees with that winner and cutoff.
- The uploaded summary tables and policy predictions match the independent
  reference execution within numerical tolerance. Full local candidate-level
  predictions and inner membership files were not supplied, so the local final
  cutoff search and nested membership were not directly reconstructed from those
  local files. The independent reference audit did reconstruct them.
- All reported source/code hashes match the reviewed files. The two split CSV
  SHA-256 values differ from LF reference bytes exactly as expected from Windows
  CRLF endings; normalization preserves identical reviewed records/folds.
- The local manifest reports Python 3.12.10, scikit-learn 1.9.1, pandas 2.3.3,
  NumPy 2.5.4, and joblib 1.6.0. It is retained as local-run provenance. A subsequent terminal transcript supplies exit code 0 and a successful local
  checksum comparison. The full environment export file was not supplied.
- The small historical referral cohort, adaptive Day 5 shortlist, reused folds,
  sparse calibration bins, and selection uncertainty limit interpretation.
  No confidence intervals or prospective validation are established by this review.

## Local artifact preflight

From the project root in PowerShell:

```powershell
$freeze = Get-Content reports\day06\candidate_freeze.json -Raw | ConvertFrom-Json
(Get-FileHash models\day06_candidate.joblib -Algorithm SHA256).Hash.ToLowerInvariant() -eq $freeze.model_sha256
```

Expected result: True. If False or the file is missing, stop and report the result.
Do not replace the recorded hash to bypass a mismatch. The local candidate JSON
can retain its original pending status; the repository's accepted_freeze.json is
the authoritative review decision and must agree on model identity and cutoff.

The Day 6 methodological review and specification freeze are complete. Day 7
covers explanations and subgroup review after artifact preflight. Day 8 remains
the first locked internal and cross-site evaluation, without retuning.

## Local preflight completion — October 20, 2026

Lucas supplied the complete local Day 6 run showing all five outer folds,
selection of c06, the accepted cutoff and bundle hash, PASS, and exit code 0.
The package-version export command completed without a reported error. The
PowerShell comparison of the local joblib SHA-256 against candidate_freeze.json
returned True. The printed hash matches accepted_freeze.json. This is reviewed
user-supplied local verification, not an independent inspection of the binary.
Day 6 is complete; proceed to Day 7 using the same frozen artifact and cutoff.
The internal test remains locked. Recheck the accepted hash before loading.
