# Authored Contoso Judge calibration

This is a supporting library/reference dataset, not a required step in the
current ten-step participant guide. The main workshop uses Microsoft Foundry managed
evaluation and Agent Optimizer; its setup and cleanup are documented separately.

`fixtures.jsonl` contains **16 newly authored synthetic examples**, including
correct answers, policy-date mistakes, fabricated approvals, stale retrieval,
missing retrieval, boundary errors, clarification, human escalation, refusal,
irrelevance, and an instruction-injection attempt.

These are **reference labels authored with AI assistance**, not human reviews,
captured customer responses, or measured LIVE scores. Every fixture starts with
`human_review_state: not_reviewed`. A fixture file alone is not a completed
calibration.

## Independent evaluator inputs

- `policy_correctness` and `relevance`: question, full response JSON,
  authoritative policy, reference answer, expected route, and actual conversation.
- `groundedness`: question, response, and **only actual observed retrieval**.
  Missing retrieval remains unavailable; policy/reference text is never used as
  fallback. Stale retrieval may support an incorrect business answer.
- `reference_labels` are used only after judging to measure agreement. They are
  not sent to either judge or to the agent.

Definitions, versions, strict integer 1–5 schemas, and prompts live in
`config/evaluators/`. `lab.calibration.run_calibration(config, calibration_id,
confirm=True)` uses the configured, verified Azure CLI identity and Judge
deployment. It is a **paid execution path**: caller confirmation does not replace
budget, data-processing, or retention approval.

This reusable reference makes no claim that calibration has run in your
environment. Execution completion and calibration quality are separate
outcomes. Keep your actual run IDs, agreement results, failures, and receipts
in a private run folder, not in the guide. Missing-retrieval fixtures are not
applicable to retrieval scoring, not fabricated perfect scores; do not remove
references, relabel results, or lower thresholds to manufacture agreement.

The authoritative approval record remains private. Existing/shared resources
and policies are outside scope. There is no deletion authorization. Local mocks
are not LIVE evidence and `--confirm` does not expand the approved scope.

Results are written under `ARTIFACTS/calibration/<id>/`: immutable metadata,
per-fixture raw response IDs/checkpoints, and `report.json`. All 16 references
remain in the report. Agreement uses the full applicable denominator; unavailable
retrieval is explicitly not applicable. Errors, disagreement IDs, critical false
accepts, model drift, and access blockers remain visible. A failed or unknown
attempt cannot be rejudged under the same ID.

## Freeze and final-test boundary

`lab.governance.freeze_candidate` snapshots calibration/review states together
with prompt, actual model snapshot, search, evaluator, gates, implementation and
data hashes. AI review is always `actor_type: ai`; imported human claims are
`external_unverified`, not authenticated approval. No local function grants
operational approval.

Fresh final-test data is generated or registered **after** the freeze, exclusively
under `ARTIFACTS/governance/holdouts/`. Built-in recipes are honestly identified as
`authored_template_variants`, not independently sampled customer data. ID/group,
exact-text and numeric-normalized near-duplicate checks include the original
100 cases, all 16 calibration cases, the supplemental dialogue and prior
holdouts. One freeze binds one holdout evaluation attempt.
Known checkpoints may resume; unknown submissions, rejudging, gate relaxation,
optimization and training use of final-test data are blocked.

The explicit
[`contoso-atlas-fresh-holdout@1.0.0` sample contract](../../config/evaluators/fresh-holdout-gates.v1.json)
declares a **separate 12-row post-freeze workshop final test**. The original
[`config/gates.json`](../../config/gates.json) still requires 20 rows for its
original test contract. Freeze records both the legacy gates and the derived
fresh gates, plus the sample-contract file/hash, **before** holdout creation or
results. All rate, semantic, relevance, error, critical-case and regression
thresholds are inherited unchanged; only the declared sample-size contract
differs. This is not a silent rewrite of the original gate.

`create_holdout(..., count=None)` derives its count from the frozen contract.
An explicit `--count 12` selects the same sample size. The default twelve include one
scripted clarification → explicit user follow-up → final response case:
**12 final cases normally require 13 agent capture turns**, not 12 turns or
12 total model/planner/Judge requests. Template variants remain synthetic
workshop evidence, not independent customer samples.

`sample_contract_sha256` binds registration, the one-shot attempt, run metadata,
Judge submission and the final result. Undersized sets, wrong/missing hashes,
tampering, repeated attempts and missing/error/critical failures remain blocked
or `HOLD`. Existing freezes/results are never rewritten to opt into the new
contract. Final reports expose the fresh contract, actual sample count and the
unchanged legacy minimum of 20; neither contract grants operational approval.

The original 100 cases and train/validation/dev/test splits are unchanged.
`PASS_FOR_WORKSHOP`, execution completion, calibration agreement and manual
operational approval are separate states.
