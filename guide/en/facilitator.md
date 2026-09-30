# Facilitator guide · the evaluation learning loop {#facilitator-guide}

[Six participant steps](handbook.md#start) · [Operator prerequisites](admin-setup.md#handoff) · [Measured verification](verification.md)

Teach **evaluate → learn from failure → improve → reevaluate**. Require an actual question, answer, evaluator reason, and policy reference—not just “the score improved.” Representative company-owned tasks, policy edge cases, and known failures make domain evaluation useful; this workshop demonstrates the method with synthetic Contoso data only.

## Before the session {#prepare}

The operator prepares the environment, sample agent, and SDK prerequisites. Participants start with the dataset. Use **Microsoft Foundry managed Evaluation**, **instruction-only Agent Optimizer**, then **one SDK command for the real candidate run and portal Compare runs**. It is not a local Judge. Keep exactly two evaluators and six steps.

- Confirm the project and authorization from the [operator handoff](admin-setup.md#handoff). English preparation is verified: **`contoso-eval-en` version `1`**, **`lab-agent-dea3cec5`**, existing **read-only knowledge connection preserved**. The Korean counterpart is operator-prepared **`contoso-eval-ko`**; no new Korean execution or measured results are claimed.
- English **`contoso-eval-en-dev12` version `1`** is registered from unchanged `data/en/optimizer/dev.jsonl`, 12 cases. Retain its SHA-256. Korean uses `data/optimizer/dev.jsonl`, also 12 cases, with separately confirmed `contoso-eval-ko-dev12` registration.
- Distinguish the one-fixture **`gpt-6-luna` / `2026-09-22` compatibility check**, the completed configuration pilot, and the clean corrected comparison. Direct Responses/pinned prompt-agent v2 failed with HTTP 500 here, not everywhere. Keep **`gpt-4.1-mini` / `2025-04-14`** as the verified agent runtime.
- Use **`lab-judge-luna-dea3cec5`** for the `gpt-6-luna` Judge and **`lab-planner-dea3cec5`** for the **`gpt-5.5` / `2026-04-24`** instruction generator. The generator is not the agent being optimized or the Judge. `gpt-6-luna` is not on the [supported optimization-model list](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models).
- Confirm Agent Optimizer access and one candidate. If a required role is unverified, do not lead participants through a submission as though support were established.
- Complete [SDK prerequisites](admin-setup.md#sdk-prerequisites): prepared venv, `requirements.lock`, `az login` and verified account/subscription, operator project endpoint/subscription, and baseline URL/Raw JSON IDs. Do not treat a missing helper/dependency as permission to change the scoring method.

Screenshots illustrate the **English UI and English-data rehearsal**, not a participant's current result or a Korean run. Use them to locate controls. Read current measured status from verification; do not turn historical images or a reading checkbox into execution evidence.

**Canonical baseline complete:** `contoso-en-learning-loop` has **12 rows, 10 passed / 2 failed / 0 errored; Relevance 10/12, binary TaskAdherence 12/12** on pinned v1 and the same Judge. The earlier `contoso-en-baseline-luna-judge` remains a **CONFIGURATION PILOT**. Actual IDs are in [step 03](handbook.md#baseline); do not mix pilot aggregates into the canonical comparison.

**Optimizer succeeded with one candidate:** `opt_e44bcf5701a348deb62a1cd4f9cb3910`, same dataset, `gpt-5.5` generator / `gpt-6-luna` Judge, no model comparison. UI **0.635 → 0.646**, **UI-reported +0.010**, **264,260 reported tokens** are optimization results, not the final direct comparison. Promote created verified lab-only v2 with exact candidate instructions and unchanged model/knowledge tool.

**Promotion warning:** active-version changes affect **all channels** and belong only to the **isolated, unpublished lab, never production**. After HOLD, active v1 was restored; candidate v2 remains available. Use explicit versions and the saved baseline rather than assuming “latest” is active.

**Native SDK execution verified; adoption HOLD:** candidate **`evalrun_f3b710fc835d444fb8aa0d2bb7797bdf`**, v2, completed under **`eval_94feef6f6f644fabb22a5680f5f24fb1`** with **12 rows, 11 passed / 1 failed / 0 errored**, versus v1 **10 passed / 2 failed / 0 errored**. Matched dataset/evaluators/Judge/model/tools leave only instructions/version changed. Relevance passes rose 10/12→11/12 but mean fell **4.4167→4.3333**; TaskAdherence stayed **12/12, binary mean 1.0**. The portal's **PairedTTest is Inconclusive for both metrics**, not proof of overall improvement.

Observed latency worsened: **p50 5,891.09→7,287.52 ms; p95 8,817.33→16,038.35 ms**. Agent tokens rose **35,187→43,751**. Keep pinned v1 pending further review/new representative cases; do not present Optimizer +0.010 or the native pass-count increase alone as success.

## Keep the six-step path explicit {#checkpoints}

| Participant step | Portal action and exact choice | Completion signal |
|---|---|---|
| [01 Dataset](handbook.md#start) | For a fresh agent still latest v1: New experience → Build → Evaluations → Create, Pin currently latest, reselect **1 target**; Individual turns / One time / Existing dataset. For the recorded promoted agent, inspect its existing v1 baseline | Correct pinned version/data, n = 12 and hash; never confuse latest v2 with baseline v1 |
| [02 Criteria](handbook.md#prepare) | Query only, no custom override; retain **Relevance threshold 4 + TaskAdherence binary pass 1**, generic TaskAdherence **Threshold 1** if shown; explicit Judge | Two criteria with distinct scales and settings recorded |
| [03 Baseline](handbook.md#baseline) | Open the completed **`contoso-en-learning-loop`** baseline; do not resubmit | 12 rows and canonical metric results; separate from the pilot |
| [04 Analysis](handbook.md#analyze) | Read **Detailed metrics result** reasons; **conversation_id → User view** opens the question/JSON response, not a Judge panel | Actual response, Relevance.reason / TaskAdherence.reason, and policy reference connected |
| [05 Optimization](handbook.md#optimize) | Recorded job succeeded; inspect original/candidate and diff. For fresh setup: Custom only OFF → built-in rows → Configure... → Apply, Relevance 4 / TaskAdherence 1 | One real candidate, verified lab v2; latest-active warning respected |
| [06 Comparison](handbook.md#decision) | Reuse the completed **`scripts/add_foundry_eval_run.py`** run's receipt; **Evaluation runs → both checkboxes → Compare runs → Baseline dropdown: original `contoso-eval-en`**, not first-selected `candidate-v2` | Verified execution, measured tradeoffs, PairedTTest Inconclusive both; HOLD adoption, no production approval |

The dataset preview shows the **first five rows**, not the total. In the observed English wizard, the matching schema **auto-resolved Field mapping**, then proceeded to **Configure agents → leave custom prompt override unset → Criteria**. If a schema-dependent mapping screen appears, use **query → query**. Never append `context` or `ground_truth` to generation. Use Upload new dataset only when the authorized project lacks the intended registration.

Remove extras from the **23 suggested evaluators**. **Relevance is 1–5, threshold 4. TaskAdherence is Binary Pass/Fail, raw 0/1, pass 1**; set its generic UI **Threshold to 1** if shown. The [official definitions](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators) confirm this distinction. The pilot's TaskAdherence Threshold 4 yielded `score=1`, `passed=true`; the generic setting did not define a meaningful 1–5 rubric.

Use **`lab-judge-luna-dea3cec5`**. Catalog links showed `relevance` **v14** / `task_adherence` **v17**, but service criteria had **`evaluator_version` empty/default**: do not teach those links as fully pinned private rubric versions.

The corrected submission confirmed **Relevance `response={{sample.output_text}}`** and **TaskAdherence `response={{sample.output_items}}`**. UI defaults also showed `query={{item.query}}` and TaskAdherence's `tool_definitions={{sample.tool_definitions}}`. Inspect **Raw JSON** and **do not override generated mappings** with the earlier UI output-text value for TaskAdherence. They are service bindings, not extra dataset fields or generation inputs.

For a fresh baseline, **Pin currently latest** must resolve to v1 before changes, then reselect the cleared checkbox. The recorded candidate is already promoted v2: v1 remains in the saved baseline run, and step 06 explicitly targets version 2 with the SDK. `gpt-4.1-mini` retires in Azure on **2027-04-14**; public **Deprecated** status may restrict fresh subscriptions.

**Optimizer filter, not missing evaluator support:** If Criteria says **No custom evaluators available**, switch **Custom only OFF** or click **View built-in evaluators**. Selecting each row opens **Configure...**; set Relevance **4** or TaskAdherence **1**, then **Apply**. This differs from the direct Evaluation wizard's Edit/Update controls and requires no custom evaluator.

## Discuss evidence, not a desired score {#evaluation-sharing}

Spend a few minutes after the baseline, after inspecting the Optimizer diff, and after direct reevaluation. These are discussions of existing results, not additional submissions.

| Discuss | Ask for |
|---|---|
| Baseline | Run ID; **n = 12**; each metric's scored/total, pass count, missing/errors; a failure or lowest-score case and a good case if one exists |
| Candidate | Actual job/candidate ID; original versus candidate per-evaluator results; changed instruction and plausible regression |
| Reevaluation | New direct run ID under the same definition; same dataset/version/hash and recorded evaluator/Judge configuration; actual before/after answers/reasons and rubric-version limits |

Use this unfilled discussion prompt:

> “In corrected run ___, metric ___ uses scale ___ and pass rule ___ (Relevance ≥4; TaskAdherence =1). It has ___ scored rows out of 12, ___ passes, and ___ missing/errors. Answer ___ conflicts/agrees with policy ___ because ___. Our next decision is ___.”

If no failure or no good case exists, report that observation. Do not manufacture one, weaken the baseline, copy a screenshot's values, or demand an improved candidate.

## Explain what the metrics do not prove {#interpret-results}

<a id="review"></a>

**Completed is not a quality pass.** Relevance's **1–5 score is not percent accuracy**. TaskAdherence is **binary 0/1**, not a five-point score: 1 means Pass, 0 means Fail. Missing/errors are not scored zeros. Report counts, coverage, reasons, and each metric's proper result type.

Relevance asks whether the response addresses the question. TaskAdherence assesses the agent's task instructions and constraints. Neither certifies every policy, citation, authority boundary, or safety property. Some evaluators do not use the reference columns; participants still compare the actual answer/reason with the original policy and reference answer.

The application values cases such as policy-date boundaries, necessary clarification, unsupported approval claims, and safe handling of restricted requests. Use an actual row to show why a generic public benchmark cannot substitute for those domain decisions.

**Canonical v1 baseline Relevance failures:** `atlas-dev-001` gave vague subscription-reduction guidance where the reference required explicit clarification; `atlas-dev-011` honestly called an undocumented feature unverified but was judged incomplete. TaskAdherence passed both. These are not candidate regression findings; do not change policy facts or remove justified uncertainty to chase Judge scores.

Screenshot 19 is **conversation_id → User view** for `atlas-dev-001`: question and actual JSON response, **not an inline Judge-reason panel**. Return to **Detailed metrics result** for **`Relevance.reason` / `TaskAdherence.reason`**, then read the reference policy. Do not invent quotations or reasons not present in the run.

Keep model/tools, language, 12 cases, dataset/version/hash, **Relevance 4 / TaskAdherence binary pass 1**, and Judge fixed. The SDK helper clones baseline `data_source` and reuses existing criteria, changes only target version, verifies model/tools, and submits a real Foundry run in the same evalID. Repeating the identical command and receipt path collects safely rather than resubmitting. No bespoke cloud scoring or new definition is involved.

The portal **Add run** attempt for Pin v2 / Individual turns required **Configure agents → Config required → Add custom prompt / User prompt**. Even `{{item.query}}` failed client-side with **`Unable to create data source configuration from item schema`**; **no remote candidate run was submitted by that attempt**. Use the SDK route, not a new evaluation definition or handcrafted score. Private service rubric versions remain unproven pinned.

**Recorded row changes:** Relevance row 1 improved **3→4**, rows 2 and 6 declined **5→4**, and row 11 stayed **3** while maintaining honest uncertainty. A threshold crossing can raise pass count even as the mean falls. Native **PairedTTest: Inconclusive** for Relevance and TaskAdherence does not prove improvement or equivalence. Reused dev12 is not statistical significance, independent generalization, or production approval.

## Recover without changing the experiment {#resume}

Inspect the existing run/job and its exact inputs before doing anything else. If submission status is uncertain, locate the request with the operator rather than creating another. Keep failures and missing rows visible.

| Symptom | Safe response |
|---|---|
| Wrong account/project, 401/403, network restriction | Operator checks identity and authorized access; do not broaden shared permissions or bypass restrictions |
| Catalog model is visible but runtime/evaluator fails | Record role, deployment, error, and request/run ID. Catalog visibility is not runtime proof |
| `gpt-6-luna` Responses/pinned agent v2 HTTP 500 | Keep that runtime unverified here and the agent on verified `gpt-4.1-mini`; do not undo the distinct native Relevance Judge capability result or claim model-wide lack of support |
| Upload preview has five rows | Confirm the unchanged local file has 12 and the correct registered dataset is selected |
| Wrong schema or input | Use the exact three-column file; `ground_truth` stays a JSON string and only `query` reaches the agent |
| Pinning leaves no selected target | The version change clears the row checkbox; reselect it and confirm 1 target before Next |
| UI mapping differs from submitted TaskAdherence mapping | Keep the generated `sample.output_items` binding; inspect Raw JSON, do not override it to `sample.output_text` |
| Compare runs is disabled | In the same definition's Evaluation runs table, select both baseline and candidate rows; wait for completion before interpreting results |
| Comparison direction looks reversed | Baseline defaults to the first selected row (`candidate-v2` here). Explicitly choose original `contoso-eval-en` in the Baseline dropdown before interpreting deltas/tests |
| Partial evaluation or missing score | Report n = 12 with scored/missing/error counts; do not remove rows or fabricate reasons |
| Optimizer Max candidates disabled | Clear Model and select Instruction only; Tool description off, Max candidates 1 |
| Optimizer Criteria: No custom evaluators available | Switch Custom only OFF or View built-in evaluators; select each row → Configure... → Relevance 4 / TaskAdherence 1 → Apply |
| Portal candidate Submit shows item-schema error | No remote run was created by that failed form. Use the single SDK command; never create another definition as a workaround |
| SDK receipt exists or run is still processing | Keep the same `.lab/foundry-evaluations/candidate-v2.json` and repeat the identical command to collect. Do not delete/change the receipt to force another submission |
| SDK identity/model/tool validation fails | Stop and check operator context; do not bypass validation, switch models, or substitute local Judge scores |
| First-run Optimizer shows a tax-agent benchmark | Label it product example, not Contoso results; use Optimize my agent → Agent |
| Optimization exceeds 60 minutes | Record the actual job status and stop waiting/submitting; operator owns follow-up and remaining costs |
| Candidate changes models/tools, or evaluator contract differs | Do not claim instruction-only improvement; record the mismatch and keep baseline |
| Optimizer or reevaluation is blocked | Record unrun work. Do not substitute a different feature, handwritten candidate, or repeated favorable run |

## Correct common misconceptions {#misconceptions}

| Claim | Correction |
|---|---|
| “Upload or Review succeeded, so evaluation completed.” | Preparation is not submission. Require real evaluation/run IDs and final results |
| “Relevance 4/5 means 80% accuracy.” | It is an ordinal Relevance score, not an accuracy estimate |
| “TaskAdherence 1 means a poor one-out-of-five answer.” | No: it is binary **Pass = 1**. Do not apply a five-point scale or threshold 4 |
| “The three roles must all use the same model.” | Runtime, Judge, and instruction generator have separate support constraints |
| “The candidate ranks higher, so promote to production.” | Never. Latest-active promotion affects all channels and is restricted here to the isolated unpublished lab; direct evaluation and production approval are separate |
| “No improvement means we should keep trying.” | Report no improvement and keep baseline. Do not rerun until favorable |
| “English screenshots prove the Korean path ran.” | They illustrate UI only; language-specific execution needs its own evidence |
| “These private-domain lessons used private customer data.” | Contoso is synthetic. Real company data requires separate authorization, privacy controls, and representative review |

## Finish with an honest result {#finish}

<a id="next-loop"></a>

Ask for the shared evaluation definition ID, distinct baseline/candidate run IDs, optimization job/candidate ID, pinned agent versions and model roles, dataset version/hash, recorded criteria/configuration and service-version limits, per-metric comparison, a case-level explanation, regressions, and the decision. In-progress, failed, or unrun work stays explicitly unfinished.

**Final workshop decision: HOLD adoption; keep pinned baseline v1.** Pass count rose, but mean Relevance fell, rows regressed, and latency/token usage increased; neither metric's PairedTTest is conclusive. Further review/new representative cases belong to a later authorized cycle, not an added required lab or reruns until favorable. No production approval or statistical significance is claimed.

**HOLD was executed:** after setting the original Baseline explicitly in Compare, the operator used **Details → Agent configuration → Active version → Edit → Version 1** to restore active v1. Keep candidate v2, both evaluation runs, and receipts; do not delete comparison evidence. No production Publish or production channels/traffic were configured. **RBAC-only Responses/preview endpoints still exist automatically without Publish**; do not teach “unpublished” as “no endpoints.”

Name the cost/cleanup owner and remaining blockers. Share only approved synthetic examples and redacted summaries. For a future company-owned evaluation, separately authorize data use and select representative tasks and known failures; do not claim this 12-case exercise certifies production.
