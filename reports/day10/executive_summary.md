# Strong internal results; uneven external performance

**Lucas Medina | UCI Heart Disease project | October 23, 2026**

## Question and approach

Can a Cleveland-trained model classify existing coronary artery disease across
historical hospital cohorts? This educational study compared logistic regression,
Random Forest, and XGBoost with fold-fitted preprocessing. Development-only
calibration and cutoff selection froze a 200-tree Random Forest (c06), with no
added sigmoid calibrator, at probability >=0.3528716233973672. Twelve later-workup
predictors exclude ca; record-level timing before diagnosis remains unverified.

## Final results: same model and cutoff at every site

| Cohort | n | ROC-AUC (95% interval) | Sensitivity | Specificity |
|---|---:|---|---:|---:|
| Cleveland test | 61 | 0.957 (0.907-0.990) | 92.9% | 78.8% |
| Hungarian | 293 | 0.903 (0.864-0.939) | 92.5% | 67.4% |
| Switzerland | 123 | 0.766 (0.591-0.925) | 88.7% | 50.0% |
| VA Long Beach | 199 | 0.721 (0.639-0.799) | 93.9% | 23.5% |

The internal test missed 2/28 positive records and flagged 7/33 negatives.
VA detected 139/148 positives but flagged 39/51 negatives. Swiss sex=0 sensitivity
was 3/10 (95% interval 10.8%-60.3%); specificity was undefined with no negatives.
These are descriptive findings, not a fairness certification.

## What the results mean

External transportability is the central finding. Strong internal discrimination
did not translate into consistent specificity or probability calibration across
sites. Swiss cholesterol was entirely missing; other external workup inputs
were frequently unavailable. These shifts may matter, but no causal explanation
was established. SHAP highlighted thal, cp and slope as prediction contributors,
not biological causes. No clinical benefit or cost saving was measured.

The 90% sensitivity objective was exploratory. The nested development selection
policy achieved 88.3%; final internal sensitivity's interval was 77.4%-98.0%.
Neither the final point estimate nor selection scores guarantee a population
target. Intervals condition on the fitted model and exclude selection uncertainty.

## Delivery and remaining verification

The report, model card, saved predictions and evidence verifier are packaged.
The frozen model and cutoff remain unchanged after test exposure. Historical
referral data, sparse groups and uncertain feature timing limit intended use to
education and technical review.

Accepted Windows binary/full environment exports remain unavailable to independent
review; clean-environment artifact reproduction and tagged release remain pending.
External raw/demographic memberships were not independently reloaded in the
numerical review. The site-comparison PNG hash discrepancy remains unresolved.

Evidence: reports/day09/report.pdf; reports/day08/site_metrics.csv;
reports/day08/review_checks.json; docs/model_card.md; docs/reproducibility.md.
Dataset: Janosi et al., UCI Heart Disease, DOI 10.24432/C52P4X.
