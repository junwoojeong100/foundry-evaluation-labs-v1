# Authored Contoso Judge calibration

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
budget, data-processing, or retention approval. This integration has not run it
against Azure.

**LIVE execution status: `PENDING_EXECUTION`.** A bounded isolated execution
scope is approved; the integration parent alone performs cloud mutations and
paid execution. The authoritative approval record remains private and governs
spending, request/job limits, processing scope, retention and new-resource-only
RBAC. Approval is not evidence of provisioning, feature access, successful
calibration or passing quality. Existing shared resources and policies are
outside scope. There is no deletion authorization: preserve the new resource
group and its evidence for review. Local mocks are not LIVE evidence, and
`--confirm` does not expand the approved scope.

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
100 cases and prior holdouts. One freeze binds one holdout evaluation attempt.
Known checkpoints may resume; unknown submissions, rejudging, gate relaxation,
optimization and training use of final-test data are blocked.

A 12-row fresh holdout does not satisfy the existing 20-row final-test minimum.
An approved execution limit does not authorize lowering that quality gate.
A smaller local generated set cannot be bound as a final evaluation; scope and
minimum sample size must be reconciled before any final-test execution.

The original 100 cases and train/validation/dev/test splits are unchanged.
`PASS_FOR_WORKSHOP`, execution completion, calibration agreement and manual
operational approval are separate states.
