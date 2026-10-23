# Day 10: reproducibility and portfolio handoff

Completed autonomous scope on October 23, 2026. Full accepted-model reproduction
and verified tagged release remain pending; this is not a clinical release.

## Delivered

- Model card: `docs/model_card.md`.
- One-page executive summary: `reports/day10/executive_summary.pdf`, editable
  Markdown and `scripts/build_day10_summary.py` renderer.
- Polished README and `docs/reproducibility.md` with environment/access limits
  and minimal original-Windows verification commands.
- Read-only `scripts/day10_verify.py`, evidence requirements/environment export,
  verification JSON, four integrity tests and a deterministic public evidence ZIP.
- Release gate review in `reports/day10/review.json`; packaged-file hashes in
  `reports/day10/package_manifest.json` and ZIP's `PACKAGE_MANIFEST.json`.

## Completed checks

A new Python 3.12 virtual environment installed `requirements-evidence.txt`;
`pip check` passed. Its full export is `reports/day10/evidence_environment.txt`.
The verifier recomputed all 140 final site numeric fields, including 2,000-draw
bootstrap intervals, from 676 saved predictions. It checked frozen decisions,
internal split membership, evaluator/dependency identity, reviewed figure hashes
and report artifacts. Reviewed CSV hashes reconcile after explicit CRLF/LF
transport handling; three prose source hashes reconcile with an additional
terminal blank line. Exact differences remain visible in verification JSON.
The summary's one-page layout was rendered and visually checked.

Four tests reject changed probability bytes, an unrecognized version of the
disputed PNG, a missing model, and an altered model before deserialization. The
candidate ZIP is inspected by CRC and SHA-256 for every file and rebuilt twice
to verify deterministic bytes. Relative Markdown links are checked against the
complete working tree. No training, calibration, threshold selection, new test
prediction generation or modification of Day 6-9 evidence occurs.

## Pending verification and release decision

The accepted Windows binary and full original local exports are unavailable.
No independent clean-environment accepted-model probability reproduction was
performed; original Day 8 terminal evidence remains missing. External raw bytes
and demographic memberships were not independently reloaded in this run. The
site-comparison PNG mismatch is preserved, not resolved.

Run the minimal commands in `docs/reproducibility.md` on Lucas's machine to produce
a current full environment capture, clean-install transcript and
`local_model_verification.json`. Passing evidence checks alone does not close
this gate. Review that evidence before tagging. No release or tag is created
by Day 10's package builder. Historical frozen-model metadata remains unchanged.
