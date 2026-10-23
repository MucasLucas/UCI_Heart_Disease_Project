# Day 9: professional research report

Prepared and reviewed October 22, 2026 (America/Los_Angeles).

## Deliverables

- reports/day09/report.pdf: 10-page research report with structured abstract,
  methods, cohort/development tables, final internal and separate external results,
  five figures, subgroup findings, limitations, evidence map, and references.
- reports/day09/report.md: editable report source.
- reports/day09/table1.csv and missingness_percent.csv: derived report tables.
- reports/day09/report_checks.json: input hashes, report hashes, and review scope.
- scripts/build_day09_report.py: PDF renderer; never loads a fitted model or raw data.

## Read and review

Read the abstract and final-results section first, then the subgroup and
limitations sections. Keep development baseline results, nested selection-policy
estimates, threshold-selection scores, and final fixed-model test estimates
distinct. Check that the report's educational scope and existing-CAD target match
the intended portfolio description. Wording corrections can be made in the
Markdown source without reopening model or threshold selection.

The report was checked against the reviewed Day 8 tables at commit
77d45a3f8b63d22df73f23742006975d9c69f6cb. All ten rendered pages were visually
inspected; 64 final metric values, five figures, full-precision cutoff, and DOI
links were checked. This is report validation, not a fresh model reproduction.
The numerical and source-provenance limits in the Day 8 review remain visible.

The source lists verified bibliographic references and dataset attribution.
Its reporting topics draw on TRIPOD+AI; no formal compliance certification is
claimed. No project-specific funding/conflicts declaration was supplied.

## Optional local PDF rendering

The checked PDF is already committed; Lucas does not need to rerun an evaluation
to read or review it. To regenerate the PDF from the committed Markdown and five
existing PNG files, use a separate reporting environment from the frozen model:

```powershell
python -m venv .venv-report
.\.venv-report\Scripts\python.exe -m pip install reportlab
.\.venv-report\Scripts\python.exe scripts\build_day09_report.py
```

Run from a complete repository checkout. The renderer uses DejaVu fonts when
installed, with a built-in Helvetica fallback. The report content and figures
are fixed; font availability can affect pagination. The reviewed build uses
DejaVu and has ten pages. The PDF carries ordinary build-time metadata, so a
new render is not promised to match the committed PDF's byte hash.

## Completion and next step

Day 9 report drafting, numerical review, PDF layout review, and documentation are
complete. Personal editorial feedback can be incorporated afterward. No new
predictions, fitting, calibration, or cutoff selection occurred.

Day 10 remains open: capture the full local environment, verify reproducibility
without substituting a different model binary, prepare the model card and
one-page executive summary, improve repository onboarding, and package a release.
Do not mark those checks complete or tag a verified release based on this report.
