# Environment setup reference · access, authorization, and cleanup {#operator-guide}

[Ten steps from the beginning](handbook.md#setup) · [Lab checklist](facilitator.md#prepare) · [Troubleshooting](troubleshooting.md)

Use this reference for **your own steps 02 provisioning, 03 Agent setup, and 10 cleanup**. Follow the [hands-on guide](handbook.md#setup) in order and open only the linked sections you need. Record actual values and completion evidence in your `.lab/lab-en/notes.md`.

**Command shortcuts:** [CLI sign-in](handbook.md#setup-login) · [Language/records](handbook.md#setup-language) · [Provisioning](handbook.md#resources-create) · [Policies/Agent](handbook.md#agent-knowledge) · [Evaluation IDs](handbook.md#baseline-identifiers) · [Reevaluation](handbook.md#decision-run) · [Group deletion/verification](handbook.md#cleanup-delete). Run commands from the lab folder's terminal; do not repeat completed work.
{: .execution-guide}

To read inside unchanged commands, open [02 creation code/portal](handbook.md#resources-code-portal), [03 retrieval code/portal](handbook.md#knowledge-code-portal), [Agent configuration](handbook.md#agent-code-portal), [09 submission/lookup](handbook.md#decision-code-portal), and [10 cleanup scope](handbook.md#cleanup-code-portal). Source panels are read-only, not instructions to run another program or duplicate creation in the portal.

## Prepare your dedicated lab environment {#start}

| Situation | Action |
|---|---|
| Starting for the first time | Begin at [01 account setup](handbook.md#setup) and perform the authorized `bootstrap plan → preflight → apply → status` path yourself. |
| Resuming your same lab | Compare original config, manifest, receipts, and actual state with the [worksheet](#handoff). Do not repeat completed creation or submission. |
| Only another workload's shared project is available | This lab does not adopt existing groups. Obtain subscription access and authorization to create your own dedicated environment before continuing. |

Verify CLI, SDK, and portal identities separately and use the same personal identity throughout. Never use another person's tokens, sign-in session, configuration, or ownership records. Run creation, ID lookup, v2 creation, reevaluation, and cleanup yourself.

**Every participant uses their own dedicated environment and Agent.** Do not have several people create the same Agent's v2 or submit the same paid job. The same example environment name on separate computers still produces Azure resource names with unique suffixes.

Access and spending authorization are required starting conditions. Obtain an approved scope through organizational procedures if needed. This is not an alternative path where someone else performs the remaining exercises.

Default Agent names are **`lab-en-iq`** for English and **`lab-ko-iq`** for Korean. If the environment name changes, use the actual name returned by the CLI and record it in the worksheet.

<figure class="portal-shot" id="portal-resource-group">
<img src="../../web/assets/portal/en/00-resource-group.png" alt="Azure Portal resource-group Overview for checking the lab subscription, region, and resource inventory." width="1600" height="1000" loading="lazy">
<figcaption><strong>Check the isolated resource group.</strong> Open the group named in your provisioning records and confirm its subscription, region, and resource inventory. Verify that the Foundry project and supporting resources belong to your lab. <a href="../../web/assets/portal/en/00-resource-group.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

## Verify model roles and actual deployments {#prepare}

| Role | Configuration key | Default model/version |
|---|---|---|
| Agent | `MODEL_DEPLOYMENT` | **`gpt-6-sol` / `2026-09-22`**, GlobalStandard 100 |
| Managed Evaluation Judge | `JUDGE_DEPLOYMENT` | **`gpt-6-luna` / `2026-09-22`**, GlobalStandard 100 |
| Optimizer/search planner | `OPTIMIZER_DEPLOYMENT` / `IQ_PLANNER_DEPLOYMENT` | **`gpt-5.5` / `2026-04-24`**, one shared GlobalStandard 100 deployment |
| Policy embeddings | `EMBEDDING_DEPLOYMENT` | **`text-embedding-3-small` / `1`**, GlobalStandard 10 |

Numbers are requested ARM capacity units, not a universal TPM conversion. These defaults require availability checks; they are not a deployment guarantee for every subscription. Inspect deployment names, model names, versions, and readiness in Foundry **Models + endpoints/Build → Models**. `.env` contains actual deployment names rather than product names.

**Distinguish additional monitoring resources.** Application Insights can automatically add a [default Failure Anomalies alert and Smart Detection action group](https://learn.microsoft.com/azure/azure-monitor/alerts/proactive-failure-diagnostics#alert-rule-creation). Bootstrap checks read-only that the alert targets only the owned Application Insights component and that the linked action group uses only the default role receivers. It does not adopt resources by name or modify/delete a shared action group in another resource group. If those links are not yet observable during provisioning, inspect the same `bootstrap status` again; do not edit the manifest or delete the alert to bypass the check.

### Set TPM before starting model calls {#throughput}

The [step-02 recommendations](handbook.md#resources-tpm) require **100,000 TPM** per Agent, Judge, and shared Optimizer/planner deployment, and **10,000 TPM** for embeddings. This assumes sequential jobs in one environment; quota pools remain model/SKU/region-specific. Sum per-model allocations across simultaneous dedicated environments. Count the Optimizer/planner deployment shared within one environment only once.

1. **New dedicated environment:** Check generative capacity 100 and embedding capacity 10 in the updated `bootstrap plan`, then authorize and provision that exact plan. Existing plans do not change automatically. For an unprovisioned lower-capacity plan, prepare a new environment name and authorization rather than editing the hashed plan.
2. **Inspect actual deployments:** Read **Tokens per Minute Rate Limit** under Foundry **Build → Models → Deployments → deployment name → Details**. Distinguish capacity displayed in thousands of tokens from the final TPM value. **Changing only the portal's Edit setting for this bootstrap environment causes plan drift.** If insufficient, inspect the plan, actual limit, and authorization; prepare a newly authorized dedicated environment with sufficient capacity when needed. Never edit hashes or approvals to bypass checks.
3. **Verify the setting:** With that environment's `.env` and language-specific artifacts path, run the read-only check below. Inspect each `*_tpm` entry's `observed`, `expected`, and `reason`.

```sh
python -m lab --config .lab/lab-en/.env preflight
```

Continue to step-03 smoke/retrieval and later evaluation/Optimizer only after overall `status: PASS` and all five TPM checks pass. The checker reads the actual deployment's `rateLimits` entry with `key: token`. If the CLI omits labels, it reads raw ARM metadata for that same deployment instead of guessing TPM from request counts or `sku.capacity`. Unverifiable limits are `BLOCKED`.

TPM accounting uses estimates rather than average billed tokens; **RPM and short-window burst limits** also apply. Allow more headroom for longer inputs/maximum outputs, shared users, and overlapping evaluation/optimization. These recommended minimums do not guarantee a 429-free run. See [official rate-limit guidance](https://learn.microsoft.com/azure/foundry/openai/how-to/quota#understanding-rate-limits).

Use the [real response check in 03](handbook.md#agent) to verify Agent and `knowledge_base_retrieve` calls. Optimizer has a separate [supported-model list](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models); Agent/Judge availability does not establish generator support.

<figure class="portal-shot" id="portal-models">
<img src="../../web/assets/portal/en/02-model-deployments.png" alt="Foundry model deployment list showing deployment names, models, versions, and readiness." width="1271" height="820" loading="lazy">
<figcaption><strong>Check model, version, and status.</strong> Map each deployment to the Agent, Judge, Optimizer, and embedding roles. Deployment names must match <code>.env</code>; verify actual calls to the prepared deployments as well. <a href="../../web/assets/portal/en/02-model-deployments.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

## Prepare an executable Agent {#bootstrap}

Prepare **Python 3.11–3.14, Git, and Azure CLI** using the [OS-specific installation instructions in 01](handbook.md#setup-local), then [verify all three versions in a new terminal](handbook.md#setup-verify). Do not reinstall working tools; resolve installation restrictions, permissions, and proxy issues first. Then create the virtual environment with the verified Python, sign in, and set the language variables. Do not activate a nonexistent `.venv` or treat fake IDs in `.env.example` as a live environment.

Use `prompts/en/baseline.txt` for English and `prompts/baseline.txt` for Korean. Never weaken the baseline to manufacture improvement. After [policy upload](handbook.md#agent-search-prepare) and [retrieval verification](handbook.md#agent-search-probe) succeed, create a policy-connected v1:

```sh
python -m lab --config .lab/lab-en/.env native-agent --version 1 --confirm
```

`native-agent` uses `ensure_fixed_release` to allow only **1 and 2**, comparing local workspace ownership with remote metadata. It reuses matching configurations, rejects a different v2, and never creates v3. It also retains a model-deployment snapshot and rejects drift. Receipts `agents/native-v1.json`, `agents/native-v2.json`, and `agents/native-model.json` belong to that environment's artifacts folder.

`native_response_format()` projects the common schema into the supported strict-generation subset. Citation uniqueness and `needs_human`/route consistency still require post-generation checks. Valid JSON does not establish policy correctness.

<a id="sdk-prerequisites"></a>

**Creating v2 is not completing evaluation.** Create one v2 from the [complete instructions reviewed in 08](handbook.md#optimize), run [the same managed evaluation in 09](handbook.md#decision), then decide whether to accept it. Use only released v1/v2; separate `draft-…` experiments are outside this lab. Do not publish the created v2 to production.

```sh
python -m lab --config .lab/lab-en/.env native-agent --version 2 --prompt .lab/lab-en/candidate.txt --confirm
```

Do not use portal Promote in this lab; create v2 with 09's CLI. Promoting first can conflict with the CLI's local/remote ownership checks. V1/v2 are complete Agent versions; the same Agent, model, tools, and output settings must differ only in instructions.

Retrieve IDs with [06's complete lookup command](handbook.md#baseline-identifiers), including the `.env` path and exact evaluation name. The reevaluation helper copies the baseline data source and checks the **remote** contract. Do not replace the remote definition with a stale local `JUDGE_DEPLOYMENT`.

## Freeze the comparison conditions {#scope}

| Item | Fixed requirement |
|---|---|
| Data | Same selected-language dev12 bytes, registration/version, questions and references |
| Relevance | Managed `builtin.relevance`, scale 1–5, threshold **4** |
| TaskAdherence | Managed `builtin.task_adherence`, binary 0/1, pass **1** |
| Judge | Same explicit Luna deployment in both evaluator definitions |
| Agent | Same Sol model/version, tools, reasoning and strict output schema |
| Change | Instructions only; releases remain v1/v2 |
| Optimizer | Instruction target only, model/tool-description changes off, bounded candidate count |
| Lab records | Keep same-condition v1/candidate results for all twelve cases in private run folders, separate from reusable guides |

Catalog evaluator versions are not proof that the private service rubric is fully pinned. Preserve the actual definition, settings and this limitation. A passing gate on reused dev12 does not guarantee future scores, independent generalization or production approval.

**The required comparison uses [Foundry Compare runs in 09](handbook.md#decision-compare).** `scripts/compare_foundry_eval.py` is an optional standalone tool, not another command required in this path. When using it separately, `LAB_LANGUAGE` or `--language ko`/`--language en` selects report language and default dev12; match any explicit dataset to that language.

### Check evaluation response mappings {#evaluation-mapping}

Select the [two evaluators and Judge in 05](handbook.md#prepare) and preserve automatic mappings. The following table supports missing-field or mismatch checks; a normal wizard flow does not require guessing SDK fields and entering them manually.

| Setting | Required value |
|---|---|
| Agent user input | Only `{{item.query}}`; leave the instruction override unset |
| Relevance response | `response={{sample.output_text}}` |
| TaskAdherence response | `response={{sample.output_items}}` |
| Judge/thresholds | Actual `JUDGE_DEPLOYMENT`; Relevance 4, TaskAdherence binary pass 1 |

If a required field is **Unassigned**, confirm the target is **Agent**, not Dataset, and inspect the query column and actual generated response mapping. Before submission, inspect the wizard; afterward, inspect the saved remote definition. Never map the reference answer as the response or copy old UI bindings. Use the [official portal guide](https://learn.microsoft.com/azure/foundry/how-to/evaluate-generative-ai-app) and [response-mapping explanation](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators#using-agent-evaluators). Do not submit until resolved. The helper in 09 checks the remote contract too.

## Complete the actual authorization file {#approval}

Open `.lab/lab-en/approval.example.json` and **Save As approval.json in the same folder**. Set limits yourself only if you can authorize spending and changes; otherwise follow the organizational approval procedure. Keep actual authorization evidence private. Neither this worksheet nor the JSON file independently proves approval or a signature. Use double quotes for JSON strings, but not for numbers, true, false, or null.

| Field | How to complete it |
|---|---|
| `schema_version`, `scope_sha256`, `models`, `retention_days` | Preserve generated values. Editing the model array or plan invalidates existing authorization. |
| `approved` | Set `true` only after actual approval. |
| `approved_by` | Your sign-in name matching `expected_user` in `config.json`. This binds the execution identity, not an organizational approver's digital signature. |
| `approved_at`, `expires_at` | Actual authorization start/end in timezone-aware ISO 8601, such as `2026-10-03T09:00:00+09:00`. Do not reuse the example date. The current time must fall within the interval. |
| `currency`, `budget_amount`, `budget_policy` | Approved three-letter currency and positive numeric budget. Keep policy `BOUNDED` and enter the actually authorized amount. |
| `acknowledge_no_monetary_cap` | Keep `false`. Unlimited spending is not the default lab policy. |
| `max_hosting_hours` | Approved positive integer hours. If 8, the approval interval must also be no longer than 8 hours. |
| `max_wait_seconds` | Positive integer wait limit, for example 3600. Ending the wait does not cancel a remote job. |
| `max_calls`, `max_candidates` | Approved call/candidate limits; 08 requests 2 candidates. Account for internal Agent, Judge, and search calls. These fields do not automatically cap every portal call or charge. |
| `allow_global_inference` | `true` only when GlobalStandard processing is authorized; it is not NCUS-only processing. |
| `allow_resource_creation`, `allow_rbac_assignments` | Each is `true` only when this plan's resources and resource-scoped role assignments are authorized. |
| `acknowledge_continuous_hosting`, `acknowledge_unknown_cost` | Each is `true` only after acknowledging continuing hosting charges and an unconfirmed final cost. |
| `allow_training`, `allow_global_training` | `false` for this path. |
| `max_epochs`, `max_training_jobs` | `0` for this path. |
| `accept_deprecated_models` | Default `false`; do not change it without reviewing a service deprecation notice. |

Validate with [02's `bootstrap preflight --config ... --approval ...`](handbook.md#resources-approval) and read `approval_reason` on failure. Authorization covers only the exact plan hash, models, and retention scope. It does not authorize another lab, an automatic retry, or deletion.

**Enforcement boundary:** Bootstrap checks authorization validity, provisioning scope, and its wait bound. JSON budget and call limits do not automatically cap all Azure Portal or Optimizer spending. Budget alerts are not cutoffs. Monitor actual usage yourself and cancel jobs or clean up within the authorized scope.

## Verify permissions and provider registration {#rbac}

Follow the [current Foundry RBAC guidance](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry). **Foundry User/Owner/Account Owner/Project Manager** may still appear under their former **Azure AI User/Owner/Account Owner/Project Manager** names.

Use **Access control (IAM) → Check access** to inspect active assignments and Scope. Older UI versions may use View my access. The [actual subscription/access illustration in 01](handbook.md#portal-check-access) demonstrates inspection of existing access, not adding roles.

| Task or connection | Required permissions and scope |
|---|---|
| Your environment creation | Bootstrap checks effective subscription-scoped group/deployment/resource writes and `Microsoft.Authorization/roleAssignments/write`. Contributor alone cannot assign roles. Subscription quota-read access is also required. |
| Your Agent/evaluation operations | Foundry User or the required data-plane permissions on your project. Azure Contributor/Owner alone does not grant these data actions. |
| Your policy preparation | Search schema/upload permissions, such as Search Service Contributor and Search Index Data Contributor, on your Search service. |
| Project managed identity | Search Index Data Reader on this Search service, model invocation, and telemetry submission to the assigned monitoring resource. |
| Search managed identity | Model invocation on the assigned Foundry resource. |
| Your log inspection | Read access to your Application Insights/Log Analytics resources, not subscription-wide log access by default. |

**Authorized bootstrap assigns runtime roles at the new resources' scopes.** It does not add subscription-wide roles. After creation, distinguish your user identity from service managed identities and use 03's actual tool call to verify propagation and data-plane access.

A provider registration enables a service type in your subscription. Follow the [official provider-registration instructions](https://learn.microsoft.com/azure/azure-resource-manager/management/resource-providers-and-types#azure-portal):

1. Open Azure Portal → **Subscriptions → your subscription → Resource providers**.
2. Search for `Microsoft.CognitiveServices`, `Microsoft.Search`, `Microsoft.OperationalInsights`, and `Microsoft.Insights`; confirm **Registered** for each.
3. Select a missing provider and **Register** only with your own `/register/action` permission and authorization. Do not register unrelated providers in bulk.
4. After registration/propagation, rerun the same preflight. If access is missing, obtain an approved execution scope before resuming. Bootstrap never auto-registers providers or expands permissions.

Allow registration/role propagation, then rerun the same preflight. For continuing `403`, compare identity, role scope, and network access. Do not grant new subscription-wide Owner, disable network or organizational policies, or transfer tokens as a shortcut.

## Costs and operational boundaries {#cost}

Evaluation invokes the Agent and Judge; optimization makes additional internal calls. Search and monitoring can continue to incur charges after the lab page closes. Distinguish measured tokens, cost estimates, and actual billing; unknown billing is not zero.

In Azure Portal → **Cost Management → Cost analysis**, select the subscription, resource group, and date range. Configure authorized budget alerts where needed, but do not treat them as enforced caps. Record the actual budget, end time, and deletion/retention plan in the worksheet.

## Record actual values and completion evidence {#handoff}

After creating the plan in 02, copy this table into your **`.lab/lab-en/notes.md`**. Mark unexecuted items **not run**, then fill actual values as each step completes. “The environment is ready” is not sufficient evidence.

| Required item | Actual values or evidence |
|---|---|
| Identity | User, tenant ID, and subscription ID; never passwords or tokens |
| Local paths | Your environment name, bootstrap config, runtime `.env`, `LAB_LANGUAGE`, and `LAB_ARTIFACTS_DIR`; record `.env` only after successful creation |
| Azure environment | Resource group, Foundry account/project, project endpoint, and Search service |
| Models | Actual names, product/version, SKU, and capacity for all four deployments |
| Policy search | Source/language, eight uploaded documents, knowledge-base/connection names, and `retrieval_verified` |
| Agent | Actual name, pinned v1, strict output, and a successful real Agent tool call |
| Dataset | JSONL path, 12 rows, SHA-256, registration name, and version |
| Evaluation | Relevance 4, TaskAdherence 1, Judge deployment, and query-only input; add actual evaluation/v1-run IDs after the first run |
| Authorization | Scope hash, expiry, budget, candidate limit, and retention |
| Finish | Exact authorized deletion group/objects and planned time, or retention reason, cost responsibility, review date, and subsequent deletion plan; distinguish shared/external dependencies |

Keep English and Korean source data and private lab records separate; do not relabel another language's results as a new execution.

Raw service files can contain account metadata, tokens or signed URLs. Keep those local; **the synthetic evaluation results themselves are not secret**. Publish only allowlisted fields, including failures, and exclude credentials—not inconvenient outcomes. Historical attempts stay in the private audit, not as additional current-version reports.

## Verify deletion and retention {#cleanup}

Use [step 10](handbook.md#cleanup) as the exit checklist. Provisioning approval is not deletion approval, and workshop documentation does not authorize deleting another person's resources.
{: .print-with-table}

| Target | Deletion or retention check |
|---|---|
| Active evaluation/Optimizer jobs | Cancellation availability, actual terminal state, and unresolved job IDs |
| Locally owned objects | Exact `cleanup` plan and verified absence afterward |
| Portal-created objects | Individually inspect datasets, evaluations, conversations, Optimizer records, and empty Agent entries |
| Dedicated resource group | Default path: verify inventory and authorization, delete, and record a successful `az group exists` result of `false` |
| Retained/shared/external resources | Remaining item, reason, cost responsibility, retention review date, and follow-up plan |
| Billing/soft delete | Delayed charges, prior usage, and separate service retention/purge policy |
| Evidence | Keep outcomes and failures privately for the required period; do not delete `.lab` first |
