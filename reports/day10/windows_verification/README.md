# Windows verification evidence

Reviewed October 23, 2026. These unchanged uploads document Lucas's local
verification of snapshot `78dbe295b3e3d977114ef0fc7317b749ad19763a`.
The environment export hash matches the model verification JSON. The supplied
terminal output reports verifier exit code 0 and `No broken requirements found.`
for the clean model environment. Installation logs were not uploaded.

The model verifier reports matching accepted binary identity, all four raw
source hashes, cohort membership, all 676 probabilities and decisions, cohort
cleaning/exclusions and subgroup tables. No fitting or threshold changes occurred.
These are user-machine execution records reviewed remotely; no model binary was
uploaded or independently loaded by the reviewer.

The evidence-only record correctly leaves model checking pending: it was run
without `--model`. The model record supersedes that scope for this local run.
Its generic `tagged_release_gate: pending` is deliberately hard-coded by the
verifier; no tag or release is created by verification. See `../final_review.json`
for the review conclusion. Historical reports and earlier review records remain
unchanged as records of the evidence available when written.
