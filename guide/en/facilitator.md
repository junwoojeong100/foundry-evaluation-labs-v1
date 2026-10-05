# Lab checklist · improve the measured result {#facilitator-guide}

[Ten lab steps](handbook.md#setup) · [Environment and result worksheet](admin-setup.md#handoff) · [Troubleshooting](troubleshooting.md)

Use this checklist to review your own **evaluate → learn → improve → reevaluate** lab. It is not an alternative to the [hands-on guide](handbook.md#setup). Do not manufacture a weak baseline or promise that every future evaluation will improve.

## Check before starting {#prepare}

**Every participant performs 01–10 directly.** Use your own account, computer, dedicated environment, and Agent; do not delegate creation, commands, or cleanup. Confirm provisioning and role-assignment access, spending authorization, and deletion/retention scope before starting.

Follow [01's Windows/macOS/Linux installation](handbook.md#setup-local), complete [version checks](handbook.md#setup-verify) for **Python 3.11–3.14, Git, and Azure CLI**, and create the virtual environment. Resolve installation approvals, PATH, and proxy issues first.

After planning in 02, copy the [worksheet](admin-setup.md#handoff) into your `notes.md`. Add actual values and completion evidence at each step. Never use another person's configuration, sign-in, or ownership records; use your originals when resuming.

Read the [six basic terms](handbook.md#basics) and [question → answer → scoring diagram](handbook.md#evaluation-flow). Check that you can explain **the Agent answers and the Judge scores**, and **instructions, not model weights, will change**. Memorized terms and high scores are not starting conditions.

Steps 04–06 use one evaluation wizard, not three evaluations. In 07, connect one case's scores, reasons, and policy before analyzing the whole result.

Use each **code ↔ portal** table to connect **inputs → actual service call → saved result → the same portal object**. Do not execute implementation panels separately from the existing command. In particular, [06's lookup code](handbook.md#baseline-code-portal) does not submit, and [08 Optimizer](handbook.md#optimizer-code-portal) runs through actual portal actions.

New lab Agents use `lab-en-iq` or `lab-ko-iq`. If the environment prefix differs, use the actual name printed by the command. Verify [model roles and identity](admin-setup.md#prepare) and reserve time for cleanup in 10.

Both v1 and v2 are full immutable Agent versions. Their model, tools, reasoning, and strict output schema match; only instructions differ. Do not weaken v1 to create improvement. Create one reviewed v2 and reevaluate under the same criteria.

Keep English and Korean data/Agents separate and compare each language's actual executions independently. Translating another language's result does not constitute a new run.

## Verify completion across all ten steps {#checkpoints}

| Step | Required action | Completion evidence |
|---|---|---|
| 01 Environment | Check account, subscription, permissions, Python 3.11–3.14, Git, Azure CLI, and language variables | Matching identity, all three version checks, and successful local commands in the virtual environment |
| 02 Provisioning | Plan, authorize, preflight, apply, and inspect status | APPLIED, generated `.env`, and runtime preflight PASS |
| 03 Agent setup | Verify model/retrieval and create `native-agent` v1 | Actual JSON response and Agent tool call |
| 04 Dataset | Register or reuse unchanged three-column JSONL | All 12 rows, registration/version, and SHA-256 |
| 05 Criteria | Relevance 4, TaskAdherence 1, and the actual Judge | Record the unsubmitted wizard settings and query-only input |
| 06 Baseline | Foundry Evaluation against pinned v1 | Completed actual run ID and all 12 items |
| 07 Analysis | Read actual answers, scores, reasons, and policies | Concrete improvement hypothesis, including failures |
| 08 Optimization | Instruction-only optimization and candidate-diff review | Job/candidate IDs, reviewed file and provenance, or the reason to retain v1 without a different candidate |
| 09 Reevaluation | With a reviewed candidate, evaluate same-criteria v2 and open Compare runs | Complete paired evidence and retain/accept/hold decision; without a different candidate, continue to 10 |
| 10 Cleanup | Preserve results and ownership, then clean up your dedicated resources | Verified authorized group absence, or the actual inventory, cost responsibility, and review date for approved retention |

Use **Individual turns / One time / Existing dataset**. The upload preview can show only five rows; the experiment still contains 12. Version selection can clear the target checkbox: reselect it and confirm one target.

## Check quality using actual cases {#evaluation-sharing}

Connect **question → actual answer → evaluator score and reason → policy/reference answer**. `conversation_id → User view` shows the conversation; the evaluator reasons belong in **Detailed metrics result**, such as `Relevance.reason` and `TaskAdherence.reason`.

Analyze at least one weak case and one strong case. If no failure is observed, use the lowest-scoring case and say no failure was found. Never weaken v1, omit a difficult row, change a reference answer, or substitute local scores. Use your own actual results when discussing with other participants too.

Keep the selected lab's twelve synthetic questions, actual responses and managed evaluator reasons in separate private run records. Preserve unsuccessful outcomes; remove tokens, cookies, signed URLs and private account metadata if results need to be shared.

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

## Finish with a separate lab record {#finish}

<a id="next-loop"></a>

Keep the actual environment, run IDs, comparison conditions, and final decision in your private records. Do not append execution results or validation history to reusable guides; correct instructions only when they are wrong.

Record the same-model result, native statistical comparison, latency/token tradeoffs, and limits of a reused synthetic dev set. A lab adoption decision is not authorization to publish or activate in production; publication is outside this lab.

**Finally, perform [the cleanup/retention checks in 10](handbook.md#cleanup) yourself.** Confirm authorized deletion, or the actual retained inventory, cost responsibility, and review date. Do not delete records needed to establish ownership or reopen the environment.
