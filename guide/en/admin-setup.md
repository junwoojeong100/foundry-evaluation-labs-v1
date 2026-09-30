# Operator prerequisites · an isolated NCUS workshop {#operator-guide}

[Participant path](handbook.md#start) · [Facilitator](facilitator.md#prepare) · [Measured verification](verification.md)

Prepare the project and sample agent **before** participants begin. The participant path is dataset preparation, managed Evaluation, failure analysis, instruction-only Agent Optimizer, and matching reevaluation—not infrastructure deployment.

## Start with the prepared lab environment {#start}

The operator has provisioned a **new, isolated North Central US (NCUS) resource group** for this rehearsal. Confirm its actual identity, ownership, and readiness from the private preparation evidence. Do not recreate it merely because the documentation changed or use a shared production environment.

Keep three claims separate: **resources exist**, **the intended runtime works**, and **task quality is acceptable**. A successful deployment proves neither agent execution nor managed-evaluator support. Record measured preparation and run outcomes in [verification](verification.md), not by copying a screenshot's status.

<figure class="portal-shot" id="portal-resource-group">
<img src="../../web/assets/portal/en/00-resource-group.png" alt="Dedicated new English rehearsal resource group with lab resources and deployment status" width="1600" height="1000" loading="lazy">
<figcaption><strong>Prepared resource group.</strong> The visible Failed count includes a separate organization-policy deployment failure involving its logging target. Do not hide it, repair shared policy as part of this workshop, or confuse it with the lab deployment's status. <a href="../../web/assets/portal/en/00-resource-group.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

## Verify three separate model roles {#prepare}

Use the **actual deployment names below**, not model family names in deployment fields, after confirming the authorized project. The separate English baseline is now **`contoso-eval-en` version `1`**, verified working with its existing **read-only knowledge connection preserved**. Keep this role mapping unchanged through the comparison.

| Role | Required decision |
|---|---|
| Agent runtime | **`lab-agent-dea3cec5` → `gpt-4.1-mini` / `2025-04-14`**, verified on **`contoso-eval-en` v1**. Preserve its read-only knowledge connection; `gpt-6-luna` Responses/Agent verification failed here |
| Evaluation Judge | **`lab-judge-luna-dea3cec5` → `gpt-6-luna` / `2026-09-22`**, verified in the actual managed baseline and candidate evaluations |
| Optimizer instruction generator | **`lab-planner-dea3cec5` → `gpt-5.5` / `2026-04-24`**. The [official optimization-model list](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models) does **not** list `gpt-6-luna` |

**Observed capability evidence:** `gpt-6-luna` version `2026-09-22` is GA in NCUS with **GlobalStandard**. The new deployments are `lab-agent-luna-dea3cec5` and `lab-judge-luna-dea3cec5`; Chat Completions returned **READY**. An actual native Foundry **Relevance** evaluation completed with **passed 1 / total 1 / errors 0** on **one authored compatibility fixture**: evaluation `eval_589a069bfd8343cf980b4b88f57771e8`, run `evalrun_e662077a904543d6bd1420b202a1b078`.

That earlier record verifies Judge capability, **not agent quality**. It is separate from the configuration pilot below and from the clean corrected comparison; do not merge their counts or IDs.

**Runtime limit:** Direct Responses and a **pinned `gpt-6-luna` prompt-agent v2** both returned **HTTP 500 in this environment**. Do not claim model-wide lack of support; runtime verification failed here. Keep the verified `gpt-4.1-mini` agent until the provider issue is resolved, without silently selecting the experimental agent.

The `gpt-4.1-mini` / `2025-04-14` Azure retirement date is **2027-04-14**. A **Deprecated** label in public documentation can restrict fresh subscriptions; it does not erase the existing deployment's observed usability. Verify the actual account and existing deployment before handoff rather than promising access to every new subscription.

The user requested `gpt-6-luna` **where supported**, acknowledging that the three roles need not support it equally. Catalog visibility, deployment success, and a chat response do not verify every API/runtime. Do not silently switch a role after baseline or report a model change as an instruction-only gain.

The optimization model **writes candidate instructions**; it is separate from the agent model being optimized and the Judge that scores responses. Use the same verified Judge for direct Evaluation, Optimizer evaluation, and direct reevaluation.

<figure class="portal-shot" id="portal-models">
<img src="../../web/assets/portal/en/02-model-deployments.png" alt="Foundry model deployments showing distinct deployment names and model versions for the rehearsal" width="1271" height="820" loading="lazy">
<figcaption><strong>Deployments are role inputs, not runtime proof.</strong> Check model version and deployment name against the private handoff. A listed deployment alone does not establish Agent, Responses, evaluator, or Optimizer compatibility. <a href="../../web/assets/portal/en/02-model-deployments.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

## Prepare the project and sample agent {#bootstrap}

Use the official [direct agent-evaluation prerequisites](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent#prerequisites) and [prompt-agent Optimizer prerequisites](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent#prerequisites). They define the supported project, agent, model, and access requirements. Do not require participants to run a whole legacy bootstrap sequence.

| Preparation | Evidence required before handoff |
|---|---|
| Intended account and project | Actual signed-in tenant/account, subscription, resource group, and project match the authorized lab. Check portal and any operator CLI/SDK identity separately |
| Prepared Contoso agent | Existing **`contoso-eval-en` version `1`** on **`lab-agent-dea3cec5`**; read-only knowledge connection preserved. Check the English four-key response contract without changing the baseline configuration |
| Runtime | Actual response from that pinned agent through the intended runtime; a model chat smoke is not a substitute |
| Managed Evaluation | **`contoso-en-learning-loop`** is **Completed**: 12 rows, 10 passed / 2 failed / 0 errored; Relevance 10/12 and binary TaskAdherence 12/12. Keep the pilot separate |
| Agent Optimizer | Optimize Preview access, Instruction-only target, Max candidates 1, **`lab-planner-dea3cec5`**, and the same Judge **`lab-judge-luna-dea3cec5`** |
| Dataset | **`contoso-eval-en-dev12` version `1`**, registered through the native Evaluation wizard from unchanged `data/en/optimizer/dev.jsonl`, exactly 12 rows; retain the original file SHA-256 |

Configure policy access before class, then hold it constant. Participants neither build a separate knowledge system nor repair infrastructure to obtain a better score. If the prepared agent lacks needed evidence, report the setup blocker rather than appending reference answers to its input.

For a fresh baseline still at v1, select **Pin currently latest**, reselect the cleared checkbox, and confirm **1 target before Next**. The recorded agent retains candidate v2, but **active version is restored to 1**. Use explicit versions and saved evaluation IDs; do not equate “latest” with active. The failed `gpt-6-luna` v2 was another agent.

In the English pilot, **Existing dataset** with matching schema auto-resolved **Field mapping**, then proceeded to **Configure agents → custom prompt override unset → Criteria**. For the corrected run, remove extras from the 23 suggestions and retain exactly two evaluators: **Relevance Threshold 4**, **TaskAdherence binary pass 1** (**Threshold 1** if a generic control is shown).

The [official agent-evaluator definitions](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators) identify TaskAdherence as **Binary Pass/Fail, raw 0/1**, not 1–5. The pilot UI accepted TaskAdherence Threshold 4, but actual `score=1` returned `passed=true`; that generic setting was not meaningful. Preserve the pilot and start a clean corrected comparison instead of changing its historical definition.

Use the English dataset with `contoso-eval-en`. The Korean counterpart is operator-prepared **`contoso-eval-ko` v1**, using `data/optimizer/dev.jsonl`, `contoso-eval-ko-dev12`, and a Korean response contract. **Korean was not re-executed in this rehearsal; no new Korean measured results or registration are claimed.** Verify its preparation separately rather than relabeling English evidence.

**Retained CONFIGURATION PILOT — portal execution, not the corrected baseline:**

| Recorded item | Value |
|---|---|
| Pilot evaluation name | `contoso-en-baseline-luna-judge` |
| Pilot evaluation definition ID | `eval_06d9c6cb93df4c7bad2bc3a62da9bc90` |
| Pilot run ID | `evalrun_98ac1b10a98d4ebe9d72bed5c66ed0f2` |
| Inputs | `contoso-eval-en` pinned v1; `contoso-eval-en-dev12` version 1; all 12 cases |
| Pilot configuration issue | Relevance threshold 4; generic TaskAdherence threshold 4 was **not meaningful for its binary output**. Judge: `lab-judge-luna-dea3cec5` / `gpt-6-luna` |
| Reported status | **Completed; 12 output items** |
| Pilot Agent usage | **12 invocations**, `contoso-eval-en` pinned v1 on `gpt-4.1-mini` |
| Pilot service-reported Judge usage | **24 `gpt-6-luna-2026-09-22` invocations; 83,492 tokens**; not corrected-comparison usage |

**Completed canonical baseline — portal; SDK candidate execution verified below:**

| Recorded item | Value |
|---|---|
| Corrected Evaluation name | **`contoso-en-learning-loop`** |
| Corrected evaluation ID | `eval_94feef6f6f644fabb22a5680f5f24fb1` |
| Corrected baseline run ID | `evalrun_cde9948ac9d946929661bc3d9e60432a` |
| Inputs | `contoso-eval-en` pinned v1; `contoso-eval-en-dev12` version 1; the same 12 cases |
| Criteria / Judge | Relevance threshold 4; TaskAdherence binary threshold/pass 1; `lab-judge-luna-dea3cec5` / `gpt-6-luna` |
| Confirmed response bindings | Relevance `response={{sample.output_text}}`; TaskAdherence `response={{sample.output_items}}` |
| Execution / overall | **Completed; 12 rows; 10 passed / 2 failed / 0 errored** |
| Per-evaluator results | **Relevance 10/12**, threshold 4; **TaskAdherence 12/12**, binary 1 |
| Relevance failures | `atlas-dev-001`: vague subscription-reduction answer versus explicit clarification in the reference. `atlas-dev-011`: honest unverified-feature answer judged incomplete |
| Evidence boundary | HTTP 201 was the creation receipt; completion is now separately confirmed. These are baseline-only results; do not change policy facts to chase scores |

Baseline Review used **Evaluation name → Submit**. Candidate **Add run** under the same definition did not work end-to-end: Pin v2 / Individual turns led to **Configure agents: Config required → Add custom prompt / User prompt**. Even `{{item.query}}` failed client-side with **`Unable to create data source configuration from item schema`**. **No candidate remote run was submitted by that portal attempt.** Do not create another definition as a workaround.

**Optimizer succeeded with one candidate:** `opt_e44bcf5701a348deb62a1cd4f9cb3910`, instruction-only, same dataset, `gpt-5.5` generator, `gpt-6-luna` Judge, no model comparison. UI scores: **0.635 → 0.646**, **UI-reported +0.010**, **264,260 reported tokens**. Preserve the displayed delta rather than deriving a different one from rounded display fields. This is not the direct candidate evaluation.

**Portal Promote created lab-only `contoso-eval-en` v2.** The operator verified exact candidate instructions and unchanged model/knowledge tool. **Latest active version affects all channels**: only an **isolated, unpublished lab agent** may use this promotion; **never production**. V1 remains the explicit recorded baseline. Do not repeat promotion or treat v2 activation as production approval.

In Optimizer **Criteria**, **No custom evaluators available** is a filter state: switch **Custom only OFF** or choose **View built-in evaluators**. Select a Relevance or TaskAdherence row to open **Configure...**, set **Relevance 4 / TaskAdherence 1**, then **Apply**. Do not add custom evaluators as a workaround.

<a id="sdk-prerequisites"></a>

**Prerequisites for the single SDK step:** Supply Python 3.11+ (3.12 recommended), Azure CLI, the operator-owned `scripts/add_foundry_eval_run.py`, and the current `requirements.lock`. From the repository root, use the approved **project endpoint** and subscription, not an endpoint guessed from a model deployment:

```bash
export AZURE_AI_PROJECT_ENDPOINT="OPERATOR_PROJECT_ENDPOINT"
export AZURE_SUBSCRIPTION_ID="OPERATOR_SUBSCRIPTION_ID"
```

Only if `.venv` is absent, prepare it once with `python3 -m venv .venv`. Activate/install the locked environment and verify the actual account:

```bash
source .venv/bin/activate
python -m pip install -r requirements.lock
az login
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
az account show --query "{user:user.name,tenant:tenantId,subscription:id}" -o json
```

Check user, tenant, and subscription against the operator's approval and portal identity; do not proceed with another cached identity. Role assignment is not part of this check. Copy `FOUNDRY_EVALUATION_ID` and `FOUNDRY_BASELINE_RUN_ID` from the canonical baseline portal URL or **Raw JSON**, using the actual IDs above, never the pilot or Optimizer job ID.

The [single command in step 06](handbook.md#decision) uses Azure AI Projects/OpenAI Evals SDKs to clone baseline `data_source`, retain existing criteria, change only target version to 2, and verify identical model/tools. It submits **one real Foundry evaluation run under the same evalID**, not a local Judge or bespoke cloud scoring. Its `.lab/foundry-evaluations/candidate-v2.json` receipt is private; repeating the identical command collects the same run. Do not delete/change the receipt or create another definition to force a retry.

**Verified end-to-end SDK execution:** the helper actually submitted candidate run **`evalrun_f3b710fc835d444fb8aa0d2bb7797bdf`** under the **same `eval_94feef6f6f644fabb22a5680f5f24fb1`**, targeting **`contoso-eval-en` v2**. It is **Completed: 12 rows, 11 passed / 1 failed / 0 errored**, versus baseline **10 passed / 2 failed / 0 errored**. The helper confirmed identical dataset/evaluators/Judge/model/tools; only instructions/version changed.

Reuse the receipt and open **`contoso-en-learning-loop` → Evaluation runs → baseline/candidate checkboxes → Compare runs**. **Set the Baseline dropdown to the original `contoso-eval-en`.** It defaults to the first selected row, which was `candidate-v2` here; confirm direction before interpreting results. The portal item-schema failure remains real; the completed candidate came from the SDK.

| Final observed comparison, n = 12 | Baseline v1 | Candidate v2 |
|---|---|---|
| All-criteria passes; errors | 10/12; 0 | 11/12; 0 |
| Relevance passes; mean (1–5) | 10/12; 4.4167 | 11/12; 4.3333 |
| TaskAdherence passes; binary mean | 12/12; 1.0 | 12/12; 1.0 |
| Relevance rows 1 / 2 / 6 / 11 | 3 / 5 / 5 / 3 | 4 / 4 / 4 / 3 |
| Latency p50 (ms) | 5,891.09 | 7,287.52 |
| Latency p95 (ms) | 8,817.33 | 16,038.35 |
| Agent tokens | 35,187 | 43,751 |

Native **PairedTTest: Inconclusive** for **both Relevance and TaskAdherence**. Row 1 crossed the pass threshold, but rows 2/6 declined and row 11 stayed at 3 for honest uncertainty rather than an unsupported definitive answer. Do not change policy facts to chase scores. **HOLD adoption; keep pinned v1 pending further review/new representative cases.** Higher pass count does not offset the lower mean and observed latency/token tradeoffs or prove overall improvement. No production approval is granted.

## Bound the actual workshop {#scope}

<a id="approval"></a>

Agree current authorization for the **actual account, project, data, processing locations, and costs**. Another rehearsal's approval is not transferable. GlobalStandard describes a processing arrangement, not a promise that every request is processed only in NCUS.

| Work | Bound |
|---|---|
| Baseline | One correctly configured direct managed evaluation of all 12 cases; the retained pilot is not this baseline |
| Optimization | One instruction-only job, **Max candidates 1**, wait **at most 60 minutes** |
| Candidate check | One SDK-submitted real Foundry run in the **same evalID**, same data/version/hash, Relevance 4 / TaskAdherence binary pass 1 / Judge; receipt-based collection, portal comparison |
| Agent changes | Lab v2 only; latest-active changes affect all channels. Promotion is restricted to the isolated unpublished agent, never production |
| Extra features | Unverified features are not run; no alternate exercise is used to claim completion |

Setup checks have their own authorized usage; one Optimizer job can include many internal calls. An error is not permission to repeat jobs, widen scope, change regions, or rerun until a preferred result appears.

## Verify identities and least-privilege access {#rbac}

Check the current [Foundry RBAC guidance](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) against the operations actually needed. Role-assignment authority is separate from permission to run an agent.

| Identity | Access to verify at the narrowest appropriate lab scope |
|---|---|
| Participant/operator | Open the project, read the pinned agent, upload/select a dataset, create/read evaluations, and use Agent Optimizer |
| Project managed identity | Required model and existing tool/connection access |
| Supporting service identities | Only the access required by the prepared agent's actual connections |
| Operator maintaining the lab | Authorized version creation, resource/cost inspection, and any separately approved lifecycle actions |

Do not give participants subscription-wide Owner access as a shortcut, expose credentials, change organization policy, or bypass network restrictions. An account shown in a portal tab is not proof that a different client uses the same identity.

## Cost and end-of-session ownership {#cost}

Costs include agent responses, Judge evaluation, instruction generation, internal Optimizer calls, policy tools, and any continuously running supporting resources or logs. **Unknown cost is not zero**, quota is not a free allowance, and closing a browser does not stop hosting charges.

Name the operator responsible for remaining jobs, cost inspection, and authorized cleanup of workshop resources. Do not turn resource deletion or broad account changes into participant exercises. Keep credentials, private configuration, and raw account identifiers out of shared guides and packages.

## Hand off a usable participant contract {#handoff}

| Give participants | Required specificity |
|---|---|
| Portal target | The correct project and **`contoso-eval-en`**; separately prepared Korean target **`contoso-eval-ko`** |
| Agent versions | **Active v1 restored**, recorded baseline v1 and retained candidate v2; **`lab-agent-dea3cec5`**, `gpt-4.1-mini` / `2025-04-14`. Keep explicit versions and all evidence |
| Model roles | Agent **`lab-agent-dea3cec5`**, Judge **`lab-judge-luna-dea3cec5`**, Optimizer **`lab-planner-dea3cec5`**, with recorded versions and support limits |
| Dataset | Registered English **`contoso-eval-en-dev12` version `1`**, original file, n = 12 and SHA-256; Korean registration requires its own confirmation |
| Evaluation contract | Same corrected definition; **Relevance 1–5 / threshold 4; TaskAdherence binary 0/1 / pass 1**, generic TaskAdherence Threshold 1 if shown; query-only input, no custom override |
| Bounds and ownership | Authorized scope, one candidate, 60-minute optimization wait, cost/cleanup owner, and escalation contact |
| SDK context | Verified venv/dependencies and `az login` account; operator project endpoint/subscription; baseline URL/Raw JSON IDs; helper and persistent receipt path |
| Evidence | Completed baseline/SDK candidate, matched inputs, final metrics/row regressions and PairedTTest Inconclusive; HOLD adoption pending further review/new representative cases. Pilot excluded |

**Record generated mappings, do not override them.** The corrected submission confirmed **Relevance `response={{sample.output_text}}`** and **TaskAdherence `response={{sample.output_items}}`**. UI defaults also showed `query={{item.query}}` and TaskAdherence's `tool_definitions={{sample.tool_definitions}}`. Inspect **Raw JSON**; do not replace the submitted TaskAdherence binding with the earlier UI output-text value. These are sample bindings, not extra dataset columns.

**Version limit:** Catalog links showed `relevance` **v14** and `task_adherence` **v17**; actual service criteria had **`evaluator_version` empty/default**. Record names/configuration, Judge and dataset versions, and this limitation. Reusing one definition does not prove private service rubric versions are fully pinned.

**Execution worked; adoption remains HOLD.** Preserve both runs, receipt, and the measured tradeoffs. Keep pinned baseline v1 for selection; lab v2 activation remains a separate all-channel operator concern. The Optimizer's +0.010 and native pass-count increase are not proven overall improvement, statistical significance, production approval, a repaired portal path, or new Korean results.

**Executed final lab state:** `contoso-eval-en` active version was restored to **1** through **Details → Agent configuration → Active version → Edit → Version 1**. Candidate v2 and all evaluation/receipt evidence remain; do not delete them. **No production Publish was performed; no production channels/traffic are configured.** Foundry nevertheless automatically provides **RBAC-only Responses/preview endpoints without Publish**. Endpoint existence is not production publication.
