# Day 8: final internal and external evaluation review

The submitted final evaluation uses the accepted c06 forest and fixed cutoff
0.3528716233973672 for existing CAD. Internal test outcomes have now been exposed.
This closes the numerical review for Day 8, with the provenance limitations below;
it does not authorize further model or threshold selection on these cohorts.

## Final results

| Cohort | n (CAD positive / negative) | ROC-AUC (95% bootstrap CI) | Sensitivity (95% Wilson CI) | Specificity (95% Wilson CI) | TP / FN / TN / FP | Brier |
|---|---:|---|---|---|---|---:|
| Cleveland test | 61 (28 / 33) | 0.957 (0.907–0.990) | 92.9% (77.4–98.0%) | 78.8% (62.2–89.3%) | 26 / 2 / 26 / 7 | 0.099 |
| Hungarian | 293 (106 / 187) | 0.903 (0.864–0.939) | 92.5% (85.8–96.1%) | 67.4% (60.4–73.7%) | 98 / 8 / 126 / 61 | 0.133 |
| Switzerland | 123 (115 / 8) | 0.766 (0.591–0.925) | 88.7% (81.6–93.3%) | 50.0% (21.5–78.5%) | 102 / 13 / 4 / 4 | 0.211 |
| VA | 199 (148 / 51) | 0.721 (0.639–0.799) | 93.9% (88.8–96.8%) | 23.5% (14.0–36.8%) | 139 / 9 / 12 / 39 | 0.200 |

The internal result is encouraging but based on only 61 records. Its sensitivity
interval extends well below 90%; neither it nor the external point estimates
establishes a population sensitivity guarantee. The development nested-policy
estimate (98/111 sensitivity) measured a selection procedure, whereas this final
test measures the single frozen forest. They must not be merged or treated as
independent estimates of the same fitting procedure.

Performance varies substantially by external site. Hungary retains relatively
strong discrimination with more false positives than the internal cohort.
Switzerland misses 13/115 positive records and falls below the 90% sensitivity
selection target. Only eight negative records inform its specificity. VA detects
139/148 positives but flags 39/51 negatives: a 76.5% false-positive rate among
negative records, distinct from FP/n = 19.6%. These retrospective results do not
support a claim of consistent cross-site performance or clinical readiness.

Average precision is 0.955, 0.856, 0.979, and 0.864 respectively. Compare it with
each site's prevalence (45.9%, 36.2%, 93.5%, 74.4%). Switzerland's high AP and PPV
(96.2%) coexist with weaker ROC discrimination and NPV of 23.5%; its high disease
prevalence is essential context. Do not rank transportability using AP alone.

## Calibration and uncertainty

The five fixed-bin plots describe calibration without recalibration. Cleveland's
observed fractions exceed mean probabilities in the upper occupied bins, but
those bins contain only 6 and 12 records. Hungary shows departures from the
diagonal in both directions. Switzerland shows observed fractions above mean
probabilities throughout, and VA shows this pattern across most occupied bins.
This supports concern about probability transportability; a calibration curve
alone does not identify why it changes. No calibrator is fitted after evaluation.

Intervals use the prespecified 2,000 within-site ordinary row bootstraps and
Wilson intervals. Switzerland has 1,999 valid ROC-AUC/AP resamples because one
draw has only one outcome class; Brier retains all 2,000. All other cohorts retain
2,000 for each metric. Intervals condition on this model/cutoff and do not include
training/selection uncertainty or dependence from unrecognized repeated patients.
There is no pooled external estimate or formal between-site significance claim.

## Cohorts, cleaning, and subgroups

The 61 Cleveland test IDs exactly match the frozen split; all 242 development
records are absent from that final internal cohort. The submitted cohort audit
removes one exact full-source duplicate each from Hungary (hungarian:0102) and
VA (va:0187), leaving 293 and 199 respectively. Switzerland retains all 123.
The audit reports zero external primary-predictor overlaps with Cleveland.
Exclusion counts reconcile, and neither excluded ID appears in saved predictions.

The submitted cleaning table records all 123 Swiss cholesterol zeros converted
to missing; VA has 49 cholesterol zeros and one resting-pressure zero converted.
After correction, cholesterol is missing in 123/123 Swiss and 56/199 VA records.
Hungary has slope missing in 189/293 and thal in 265/293; VA has thal missing in
165/199. All use the frozen Cleveland imputer. Negative external oldpeak values
are retained. These differences are plausible contributors to transportability
problems, not demonstrated causal explanations. External rules were specified
in the Day 8 pre-evaluation addendum, not all fixed on Day 1.

The 24 overall/sex/age rows reconcile with site totals and their confusion counts,
rates, Wilson intervals, and sparse-denominator flags. All six Cleveland subgroup
rows also reproduce from the source demographics and saved probabilities.
External demographic membership was not independently reloaded in this review.
The submitted Swiss sex=0 subgroup detects only 3/10 positive records (seven
missed), versus 99/105 for sex=1; there are no negative sex=0 records, so its
specificity is undefined. Hungary's sex=0 sensitivity is 9/12 versus 89/94 for
sex=1. These are concerning descriptive differences with small denominators,
not evidence to dismiss because of the overall sensitivity or enough evidence
to establish a population disparity. Preserve them explicitly in the report.
Sparse negative groups, especially in Switzerland and VA, limit interpretation;
the subgroup results provide no fairness certification and prompt no retuning.

## Verification and provenance limits

Review recomputed all site point estimates and bootstrap intervals from the 676
uploaded probabilities. Every class decision matches the accepted cutoff. The
script/dependency hashes and accepted model identity agree with the run manifest.
Six uploaded CSVs, roc_pr.png, and calibration.png match their recorded hashes.
The three images were accessible and visually reviewed despite attachment errors.

The uploaded site_comparison.png has SHA-256
bc8eea4723b74a4f1658ed970cbb2171ebe61574591312c77ba894b6d94e41ea,
whereas the run manifest records
15fff2a5d14f03fbf49016f27c1e46a41e5edce15f3ae3644c13864a58543e57.
Its displayed point estimates and intervals agree with the verified metrics, so
the uploaded image is retained unchanged as a reviewed display. Exact original
image-byte provenance remains unresolved; do not label it checksum verified or
replace the historical manifest to conceal this discrepancy.

The accepted Windows model binary remains local. Identity rests on the submitted
manifest and earlier local checksum evidence, not a new independent model load.
External source hashes/cleaning/exclusions are documented by that run; external
raw bytes were not reloaded during this review. Terminal output, exit code, and
full environment.txt were not supplied for Day 8; package versions appear in the
manifest. These limits remain visible rather than being represented as completed
independent checks.

roc_pr_curves.csv and calibration_bins.csv were reconstructed from the uploaded
probabilities for inspection; their original local CSV bytes were not supplied.
The original run_manifest.json is preserved. Git text storage may normalize line
endings, so uploaded CSV-byte checks refer to the original attachments, not a
claim that every repository checkout reproduces their Windows byte hashes.
See review_checks.json for the exact checks and original verified hashes.

## Next step

Day 9 writes the professional report using these final results, explicit
uncertainty, missingness and case-mix limitations, existing-CAD scope, and the
recorded explanation/subgroup evidence. Preserve this model, cutoff, split, and
evaluation results; do not improve reported test performance through retuning.
