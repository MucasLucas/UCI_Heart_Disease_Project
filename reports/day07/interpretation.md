# Day 7 explanation and subgroup review

Reviewed October 20, 2026 (America/Los_Angeles). All seven uploaded files are
accessible, including the three PNGs previously reported as missing. The images
were inspected and match their accompanying tables. Original uploaded copies
are retained under the standard Day 7 filenames; run_manifest(1).json is stored
as run_manifest.json without altering its contents.

## Explanation scope and integrity

The manifest identifies the accepted Windows model SHA-256 and unchanged cutoff
0.3528716233973672, with model_refitted=False, threshold_changed=False, and
holdout_analyzed=False. It reports SHAP 0.50.0 with tree-path attribution on
class-1 probability, using development-training path counts as background.
Reported maximum probability reconstruction error is 7.771561172376096e-16.
Code/input hashes match the reviewed sources; Windows CRLF endings explain the
two split-file hash differences from LF reference bytes.

Explanations describe the frozen forest on its 242 development training records.
They are not test performance, causal effects, or independent clinical findings.
One-hot-column contributions are summed to their original inputs; these sums
preserve additivity but are not recomputed grouped-coalition Shapley values.
Tree structure, correlated inputs, and background assumptions affect attribution.

## Global explanation

| Feature | Mean absolute summed contribution (probability units) |
|---|---:|
| thal | 0.1106 |
| cp | 0.0768 |
| slope | 0.0600 |
| sex | 0.0590 |
| exang | 0.0553 |

These are the five leading explanatory inputs. For example, thal's 0.1106 is an
average absolute probability-scale attribution of about 11.1 percentage points,
not a coefficient, relative risk, or percentage of all predictive importance.
Global absolute magnitudes do not determine whether an input increases or
decreases a particular record's prediction. thal is a diagnostic test result,
not a thalassemia diagnosis; the later-workup setting remains essential.
Do not infer that fbs, the lowest-ranked input here, is clinically unimportant.

## Local explanation

The examples are the first three development IDs in lexical order, selected
without looking for errors or dramatic contributions. Their supplied values
match source measurements and their attributions match the independent
reference calculation within numerical tolerance.

For cleveland:0001:

- exang=1 contributes +0.08913, approximately +8.91 probability percentage points
  relative to the explanation baseline.
- thal=3 contributes -0.08902, approximately -8.90 probability percentage points.

Together with all other contributions, these move the baseline of approximately
0.4602 to the displayed probability of approximately 0.8691. The opposite signs
illustrate why global absolute rankings cannot substitute for local explanations.
For cleveland:0003, oldpeak contributes about +11.26 points while thal contributes
about -10.25 points; other negative contributions bring its probability to about
0.2688, below the unchanged cutoff. These are descriptive training-record
predictions, not validated individual diagnostic advice.

## Subgroup audit of the development selection policy

Use Day 6 nested out-of-fold policy predictions and each fold's selected cutoff,
not the frozen model's training predictions. The overall confusion counts remain
98 TP, 13 FN, 82 TN, and 49 FP. These policy estimates are not a subgroup validation
of the single final frozen forest; that assessment belongs to Day 8.

| Group | n | CAD-positive / negative | Sensitivity | Specificity |
|---|---:|---:|---:|---:|
| Overall | 242 | 111 / 131 | 88.3% | 62.6% |
| sex=0 | 77 | 18 / 59 | 83.3% | 84.7% |
| sex=1 | 165 | 93 / 72 | 89.2% | 44.4% |
| Age <50 | 66 | 22 / 44 | 77.3% | 77.3% |
| Age 50–59 | 107 | 54 / 53 | 88.9% | 58.5% |
| Age 60+ | 69 | 35 / 34 | 94.3% | 50.0% |

Specificity differs by about 40.3 percentage points between the recorded sex
codes. The false-positive counts are 9/59 negatives for sex=0 and 40/72 for
sex=1. This deserves reporting as an observed development-policy disparity;
it does not by itself identify its causes or establish fairness or unfairness.
The distributions of outcomes, predictors, and workup selection differ between
these subgroups, and no adjusted comparison is performed here.

Only 18 sex=0 records are CAD-positive. Its sensitivity is 15/18, with a
descriptive 95% Wilson interval of about 60.8%–94.2%. Specificity intervals are
about 73.5%–91.8% for sex=0 and 33.5%–55.9% for sex=1. The intervals are not
formal fairness tests and omit dependence and model/threshold-selection uncertainty.

Sensitivity is lowest below age 50 (17/22, 77.3%) and highest at age 60+ (33/35,
94.3%), while specificity decreases across these age bands. Report denominators,
not just percentages. Do not move age cutoffs or retune the frozen model to
improve these descriptive subgroup results.

## Review checks and evidence limits

- Recomputed all six subgroup rows, including confusion counts, rates, ROC-AUC,
  Brier score, and Wilson limits directly from reviewed policy predictions.
  Sex-code and age partitions each sum to the overall denominators/counts.
- Checked all 12 ranked features, all 36 local contribution rows, deterministic
  example IDs, and their original source values. All three uploaded CSVs match
  the independent reference results within numerical tolerance.
- Local sums reconstruct the corresponding reference model probabilities.
  The full user model binary, full encoded/grouped SHAP matrices, and background
  file were not uploaded, so the user model's complete SHAP computation is
  supported by the manifest and matching reference checks rather than a second
  independent load of that binary.
- The local manifest records Python 3.12.10, scikit-learn 1.9.1, NumPy 2.5.4,
  pandas 2.3.3, joblib 1.6.0, and SHAP 0.50.0. No Day 7 terminal exit code or
  full environment export was supplied; do not invent either.
- No retraining, threshold adjustment, locked-test prediction, or cross-site
  evaluation was performed in this review.

Day 7 output review and interpretation are complete. Day 8 is the first locked
internal and cross-site evaluation. Use the same accepted artifact and full-
precision cutoff, verify its hash before loading, and report results without
retuning in response to the test. The original exploratory sensitivity objective
remains unmet on the Day 6 policy outer assessment and is not certified by SHAP
or by the favorable age-60+ subgroup point estimate.
