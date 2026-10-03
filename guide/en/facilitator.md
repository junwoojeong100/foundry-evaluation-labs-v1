# Facilitator guide · improve the measured result {#facilitator-guide}

[Ten participant steps](handbook.md#setup) · [Operator handoff](admin-setup.md#handoff) · [Execution issues](troubleshooting.md) · [Latest v2 verification](verification.md)

Teach **evaluate → learn → improve → reevaluate** using business-specific tasks and real managed results. Do not manufacture a weak baseline or promise that every future evaluation will improve.

## Before class {#prepare}

Decide whether participants perform 01–03 or receive an operator-prepared environment. Self-setup requires access, cost authorization, and a cleanup owner. Prepared classes need a complete [handoff](admin-setup.md#handoff) and verified project, Agent, retrieval, and dataset registration.

**Separate environment preparation from learning evaluation in beginner classes.** Prefer operator preparation for 02–03, but still have participants verify their own account, project, and completion evidence. Assign SDK-command responsibility before class; do not distribute the operator's sign-in or ownership records.

Start together with the [six basic terms](handbook.md#basics) and [question → answer → scoring diagram](handbook.md#evaluation-flow). Ask participants to explain that **the Agent answers and the Judge scores**, and that **instructions, not model weights, will change**. Do not require memorized terminology or high scores to begin.

Steps 04–06 use one evaluation wizard, not three evaluations. Read one scored example together in 07 before independent analysis. If a group shares an Agent, assign one owner for v2 creation and paid submissions.

New lab Agents use `lab-en-iq` or `lab-ko-iq`. Do not assume the historical `contoso-eval-en-sol` already exists in a new project. Verify [model roles and identity](admin-setup.md#prepare), and reserve time for cleanup in 10.

Both v1 and v2 are full immutable Agent versions. Their model, tools, reasoning, and strict output schema match; only instructions differ. Do not weaken v1 to create improvement. The default path creates one reviewed v2 and reevaluates it; only operators who verified draft support use a separate draft workflow.

Keep English and Korean data/Agents separate. The Korean guide explains the procedure; the current published measurements are **English-data results only**.

## Verify completion across all ten steps {#checkpoints}

| Step | Required action | Completion evidence |
|---|---|---|
| 01 Environment | Check account, subscription, permissions, Python, CLI, and language variables | Matching identity and successful local commands |
| 02 Provisioning | Plan, authorize, preflight, apply, and inspect status | APPLIED, generated `.env`, and runtime preflight PASS |
| 03 Agent setup | Verify model/retrieval and create `native-agent` v1 | Actual JSON response and Agent tool call |
| 04 Dataset | Register or reuse unchanged three-column JSONL | All 12 rows, registration/version, and SHA-256 |
| 05 Criteria | Relevance 4, TaskAdherence 1, and the actual Judge | Saved remote definition and query-only input |
| 06 Baseline | Foundry Evaluation against pinned v1 | Completed actual run ID and all 12 items |
| 07 Analysis | Read actual answers, scores, reasons, and policies | Concrete improvement hypothesis, including failures |
| 08 Optimization | Instruction-only optimization and candidate-diff review | Job/candidate IDs, reviewed file, and provenance |
| 09 Reevaluation | Evaluate same-criteria v2 and open Compare runs | Complete paired evidence and retain/accept/hold decision |
| 10 Cleanup | Preserve evidence, inspect scope, authorize, and delete | Dedicated-group absence or a shared-resource retention handoff |

Use **Individual turns / One time / Existing dataset**. The upload preview can show only five rows; the experiment still contains 12. Version selection can clear the target checkbox: reselect it and confirm one target.

## Discuss the actual cases {#evaluation-sharing}

Ask participants to connect **question → actual answer → evaluator score and reason → policy/reference answer**. `conversation_id → User view` shows the conversation; the evaluator reasons belong in **Detailed metrics result**, such as `Relevance.reason` and `TaskAdherence.reason`.

Discuss at least one weak case and one strong case. If no failure is observed, use the lowest-scoring case and say no failure was found. Never weaken v1, omit a difficult row, change a reference answer or substitute local scores.

The latest public record includes all 12 synthetic questions, both actual responses and the managed evaluator reasons. Those results are not credentials. Exclude tokens, cookies, signed URLs and private account metadata, not unsuccessful outcomes.

## Interpret improvements correctly {#interpret-results}

<a id="review"></a>

**Relevance 4/5 is not 80% accuracy. TaskAdherence 1 is Pass, not a poor one-out-of-five score.** Report each evaluator separately, all-criteria passes, errors and coverage.

`scripts/compare_foundry_eval.py` requires complete matched cases, identical data/model/tools/settings, per-item version/instruction attestation, no lower pass counts or means, and at least one strict measured quality improvement. Malformed responses remain failures; the helper never repairs them into a pass.

Read answers for unsupported certainty, incorrect policy arithmetic, action claims and wrong routing even if the generic evaluator passed them. A request demanding an impossible certainty must not be satisfied with invented facts.

Optimizer ranking is internal selection evidence, not the direct managed reevaluation mean or pass rate. A higher ranking alone does not establish a better v2.

## Recover without changing the experiment {#resume}

| Symptom | Response |
|---|---|
| Wrong identity, 401/403 | Confirm the approved account/project; do not widen shared permissions |
| Catalog or deployment succeeds but Agent fails | Record the actual API/runtime error; verify the intended role |
| Portal Add run item-schema error | Use the official SDK helper with the existing baseline data source, not a different scorer |
| No custom evaluators available | Switch **Custom only OFF** or select **View built-in evaluators** |
| Duplicate local receipt or existing remote run | Retrieve that same run; do not rename it to force another submission |
| Candidate changes model/tools/reasoning/schema | Reject an instruction-only comparison claim |
| Draft becomes a numbered release | Stop; draft support is not enabled as expected |
| Existing released v2 differs from local source | Do not overwrite it or create v3; preserve the release and inspect the mismatch |
| Missing output or metrics | Report incomplete execution; do not reduce the denominator |
| Statistical comparison is Inconclusive | Report that result; do not claim significance or equivalence |

Relevance maps to `{{sample.output_text}}`; TaskAdherence maps to `{{sample.output_items}}`. Do not overwrite service-generated bindings or feed `ground_truth` into the Agent. The actual remote Judge overrides any stale local default.

After a timeout, identify **which existing job ID to resume** first. Use the [issue record](troubleshooting.md) to prevent deletion/recreation or paid retries “until it succeeds.” Do not mark a blocked step completed.

## Correct common misconceptions {#misconceptions}

| Claim | Correction |
|---|---|
| “V2 is a prompt file number only.” | It is a complete Agent version; this experiment changes only its instructions |
| “A more powerful model makes v2 better than old-model v1.” | Both versions must use the same model for the instruction comparison |
| “A better v2 can be guaranteed before execution.” | Only observed improvement can be established; future stochastic results are not guaranteed |
| “Keep only successful rows.” | Keep every case, including failures and missing/error outcomes |
| “The source schema certifies correct business decisions.” | It controls output structure, not policy truth or proper routing |
| “Public evidence must include cookies and raw logs.” | Publish actual synthetic responses and reasons through an allowlist, not authentication data |

## Finish with one current report {#finish}

<a id="next-loop"></a>

Publish **the latest v2 verification and its frozen v1 control**, not a sequence of obsolete current-version reports. Keep earlier raw receipts for audit without relabeling them as this pair.

Report the same-model result, native statistical comparison, any latency/token tradeoffs and the remaining limits of a reused synthetic dev set. Candidate activation is a separate operator decision; no production publication is part of this workshop.

**Before ending class, perform [the cleanup checks in 10](handbook.md#cleanup) together.** Confirm dedicated-group deletion or a named owner and deadline for retained shared resources. Hand off actual outcomes and issue records privately; do not delete ownership records first.
