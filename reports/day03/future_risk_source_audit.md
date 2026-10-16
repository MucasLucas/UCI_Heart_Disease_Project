# Future cardiovascular-risk source audit

Status: documentation and access audit complete; participant-data audit BLOCKED.
Source reviewed October 15, 2026 (America/Los_Angeles). No Framingham participant
file has been obtained, hashed, profiled, split, or used for model training.
Published source counts below are documentation facts, not observed audit results.

## Candidate and evidence
Candidate: NHLBI BioLINCC Framingham longitudinal teaching dataset.
- Official documentation describes 4,434 participants and 11,627 exam records.
- Repeated exams contain participant-level event information repeated across visits.
- Candidate outcome fields are `CVD` and `TIMECVD`; CHD is a different endpoint.
- Baseline HDL/LDL are unavailable; they appear only at the third exam.
- The teaching page and documentation explicitly state that anonymized teaching
  data are unsuitable for publication. A portfolio must present any permitted
  use as an educational demonstration, not original publishable clinical evidence.
- The request link redirects to BioLINCC login. Website registration and a data
  request are required. No access agreement was accepted or request submitted.

Official references:
1. https://biolincc.nhlbi.nih.gov/teaching/
2. https://biolincc.nhlbi.nih.gov/media/teachingstudies/FHS_Teaching_Longitudinal_Data_Documentation_2021a.pdf
3. https://biolincc.nhlbi.nih.gov/resource_overview/
4. https://biolincc.nhlbi.nih.gov/requests/teaching-dataset-request/

The teaching page describes 20 years of follow-up while the detailed PDF describes
24 years. Confirm the supplied file version and follow-up distribution before
freezing a prediction horizon. Do not infer complete ten-year follow-up for every
participant from a dataset-level description.

## Proposed analysis, pending data and use verification
Use the first examination only. Require one baseline row per participant and no
baseline CHD or stroke for a primary-prevention cohort. Select baseline predictors
only; exclude identifiers, future event fields, event times, and later-exam values
from the predictor matrix. Split by participant before development EDA; protect a
separate locked test. Do not pool or join the Framingham and UCI patients.

Provisional estimand: cumulative incidence of the source-defined first CVD event
within ten years of baseline. Freeze the exact event definition and time convention
only after data verification. This endpoint must be named precisely and must not
be labeled all cardiovascular disease, heart-failure risk, or a validated ASCVD score.

Censoring before the horizon does not create a negative label. Audit deaths before
CVD as competing events; a model that censors them and reports 1 minus survival
does not automatically estimate real-world cumulative incidence. Choose an
appropriate competing-risk method or explicitly narrower estimand before fitting.
Report horizon-specific calibration, discrimination, and uncertainty with methods
that account for censoring and competing events. Keep diagnostic CAD thresholds
separate from future-risk estimation.

## Participant-data audit required after receipt
1. Record original filename, source version, acquisition route, permitted use,
   redistribution terms, file size, and SHA-256; retain unchanged raw inputs locally.
2. Validate schema, missing-value codes, numeric ranges, participant IDs, exam codes,
   duplicate baseline rows, and consistency of event fields across repeated visits.
3. Verify baseline time, prior-disease exclusions, event/time consistency, positive
   follow-up, death timing, and incident events occurring after baseline.
4. Enumerate cohort exclusions, eligible patients, events by horizon, competing
   deaths, and early censoring; verify sufficient follow-up before confirming ten years.
5. Freeze participant-level split and development-only analysis plan. Profile
   predictor missingness only within development after integrity checks.

## Decision and unblock step
Do not yet accept this candidate as the source for a publication-oriented report.
For an educational portfolio, obtain the official teaching download and applicable
terms, then verify that the intended public portfolio use is permitted. For original
clinical research, select a source with research/publication permission and a
feasible access route. Neither an unofficial mirror nor an unsupported `TenYearCHD`
column establishes provenance, broader-CVD labels, or follow-up completeness.

Lucas must obtain the official participant file through the BioLINCC request
process and provide it with its accompanying terms, or identify a suitable
research-permitted alternative. The row-level audit remains incomplete until then.
Continue CAD preprocessing independently; do not invent future-risk results or
hold up the reviewed CAD track while access is pending.
