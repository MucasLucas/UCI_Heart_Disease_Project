# Day 1 reference audit

| Site | Rows | Disease present | Disease absent | Missing cells |
|---|---:|---:|---:|---:|
| Cleveland | 303 | 139 | 164 | 6 |
| Hungary | 294 | 106 | 188 | 782 |
| Switzerland | 123 | 115 | 8 | 273 |
| VA | 200 | 149 | 51 | 698 |

The initial run found no invalid categorical values or cross-site exact predictor
matches. Hungary and VA each have one duplicated full row; retain flags and make
a documented duplicate policy before external evaluation. Exact equality alone
does not prove that records represent the same person.

All 123 Swiss cholesterol values and 49 VA cholesterol values are zero. VA also
has one zero resting blood pressure. Treat these as data-quality questions;
define a rule from documentation and development knowledge before evaluating
cross-site performance. The primary analysis must not infer normal cholesterol
from zero. Sites have very different observed outcome proportions. These are
source audits, not model performance results or tuning feedback.

Frozen Cleveland split: 242 development rows, 61 locked test rows. No exact
predictor groups overlap between them. Do not repeatedly alter the split.

## Completion review — October 14, 2026
- Lucas ran the audit locally and shared successful terminal output. Cohort
  counts, missingness, duplicates, and split sizes match the reference results.
- Lucas confirmed existing coronary artery disease as the outcome and exclusion
  of ca from the primary model.
- Repository confirmed: https://github.com/MucasLucas/UCI_Heart_Disease_Project
- The committed audit tables and manifest originate from the starter reference
  run. The manifest's package versions describe that run, not Lucas's Windows
  environment. His local environment.txt and manifest have not been supplied.
- The frozen split CSV remains the reference split; the local membership has
  not yet been compared record by record. Use this committed split for EDA.

Day 1 audit and protocol review passed. Repository integration is the final gate.
