# Operator guide · a dedicated NCUS environment and safe resumption {#운영자-안내-새-ncus-환경과-안전한-재개}

[Back to the participant path](handbook.md#environment) · [Infrastructure contract (Korean)](../../infra/README.md) · [Verification status](verification.md)

**This is a one-time preparation guide for operators, before the participant session.** Reuse the dedicated North Central US (NCUS) environment already created for this lab after checking its original ownership manifest and current authorization. A six-step guide does not require redeployment. Run the new-environment procedure below **only when no lab environment exists**. Do not adopt unrelated existing/shared accounts or resources. Put identifying values only in private plan files.

**What you will explore and why:** Connect Azure identity, resource scope, declarative deployment, and ownership records. The ability to click Create is not the same as authorization to use that environment. Keeping these separate makes results and costs traceable. A1–A4 establish identity and the plan; only A5 applies approved infrastructure. A6 connects the result to the participant's runtime.

| Term | Meaning and role in this lab |
|---|---|
| Tenant / Subscription / Resource group | Identity directory / billing and management scope / container for lab resources. They are not interchangeable identifiers. |
| Foundry resource / Project / Deployment | Shared resource providing capabilities such as models / workspace for agents, evaluations, and connections / callable model-version-SKU target. |
| ARM template / Manifest | Declaration of infrastructure to create / record of actual ownership and execution state. A plan file does not mean Azure resources exist. |
| Managed identity / RBAC | Identity used by an Azure service / operations allowed for that identity. Check user, project MI, and Search MI permissions separately. |

See [participant step 02](handbook.md#cli-basics) for CLI notation and virtual environments, and [the model-deployment screenshot](handbook.md#portal-models) for portal locations. Screenshots are read-only references from the existing environment, not instructions to repeat setup.

> **Observed state and recovery sequence**
>
> Following draft validation, actual responses exposed a retired-model rejection, concurrent project/model creation conflict, and missing monitoring-connection metadata. These were resolved. ARM `Succeeded` and 25 ownership records were confirmed in the same new NCUS resource group. Before generating model responses, gpt-4.1-mini / 2025-04-14 / Standard was explicitly selected, without switching regions or reusing existing resources. The [verification record](verification.md) distinguishes resource creation, data-plane execution, and quality outcomes.

## Approval, ownership, and readiness are different states {#scope}

| Check | Scope of the recorded setup run |
|---|---|
| Region and target | Only a new resource group and new resources in `northcentralus` |
| Monetary limit | The user **explicitly approved no monetary cap**. The earlier USD 50 proposal was not a blocking condition |
| Work limits | At most 300 model/Judge/planner calls combined; one job and at most two candidates per Optimizer; one SFT job with 56 train / 12 validation cases and one epoch; fresh12; at most 60 minutes waiting per job |
| Data and processing | Approved synthetic data with GlobalStandard/Global/Developer processing. No expansion to actual customer data |
| Permissions | Only minimum required RBAC on new resources. No permission/policy changes on existing/shared scopes |
| Retention | Preserve the new resource group and evidence for user review. Deletion was not authorized |

That authorization applies **only to the recorded operational scope**. It does not authorize spending or tenant access for another customer or participant who downloads the package. Keep original approval evidence and signed/approval files private; exclude them from HTML, PDF, and ZIP deliverables.

Do not overwrite an infrastructure failure with a later success, or misdescribe a real service error as missing cost approval. However, `BLOCKED_AWAITING_APPROVAL` is a legitimate tool state if a particular new plan lacks a valid approval file. Actual consent and the machine-readable record binding that consent to a plan are separate.

## A1–A6. Prepare once, then continue in the same environment {#bootstrap}

### A1. Check the intended account and subscription {#a1-의도한-계정과-구독-확인}

**Purpose:** Prevent CLI, SDK, and browser operations from silently using different accounts.

**Your task:** Have Python 3.11+ and Azure CLI installed locally. Values below are placeholders; use actual values only in your terminal/private files.

**Run:**

```bash
export AZURE_SUBSCRIPTION_ID="YOUR_SUBSCRIPTION_ID"
export AZURE_TENANT_ID="YOUR_TENANT_ID"
export EXPECTED_AZURE_USER="operator@example.invalid"
az login --tenant "$AZURE_TENANT_ID"
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
az account show --query "{user:user.name,tenant:tenantId,subscription:id}" -o json
```

**Commands explained:**

| Command | What it does and what to watch |
|---|---|
| `export AZURE_SUBSCRIPTION_ID=...` | Sets the approved subscription ID in this shell. It neither selects nor creates a subscription. |
| `export AZURE_TENANT_ID=...` | Sets the directory ID for sign-in, avoiding a similarly named account in another directory. |
| `export EXPECTED_AZURE_USER=...` | Identifies the expected actual user. Replace the example email; this is not a password/token field. |
| `az login --tenant ...` | Performs normal sign-in/MFA for that tenant. CLI authentication is separate from portal sign-in. |
| `az account set --subscription ...` | Selects the active subscription for later CLI calls. Grants no permissions and deploys no resources. |
| `az account show --query ... -o json` | Queries only the actual CLI user, tenant, and subscription as JSON. Its identifying values must not be published in guides or classroom screenshots. |

**Completion signal:** The actual signed-in user, tenant, and subscription match the authorized scope. Check the browser account too. Bootstrap separately verifies the user's actual object ID.

**Errors/recovery:** Do not work around a wrong account, service principal, or missing permission by using another cached credential. Never copy tokens, keys, or passwords into documentation.

**Resume:** Authenticate again only when needed, such as after expiry. In the recorded checks, Azure MCP's subscription lookup was correct, but **Foundry MCP's data-plane token belonged to another tenant**, so the request was rejected. No changes were made through that path. The verified CLI/SDK identity and browser were used instead. An MCP subscription list alone does not establish the principal or data-plane identity.

**Next:** A2. If a private plan already exists, reuse its path rather than creating another.

### A2. Create a new plan locally {#a2-신규-계획을-로컬에-생성}

**Purpose:** Fix resource names, models, capacity, processing scope, and ownership markers before remote changes.

**Your task:** Run this only for an environment being prepared for the first time. This standard-library path does not contact Azure.

**Run:**

```bash
python3 -S -m lab.bootstrap plan --subscription "$AZURE_SUBSCRIPTION_ID" --tenant "$AZURE_TENANT_ID" --expected-user "$EXPECTED_AZURE_USER" --environment lab-training --agent-sku Standard --root .lab --location northcentralus
```

**Command explained:** `plan` **creates local files**. `--subscription`, `--tenant`, and `--expected-user` fix the identity to verify; `--environment` and `--root` locate the private plan; `--location` fixes the allowed region. `--agent-sku Standard` selects the base agent deployment type, not the Judge/planner/embedding SKUs. The `-S` path needs no SDK and performs no remote creation or billable model call.

Use an environment name such as `lab-training` that **starts with a lowercase letter**. A name starting only with date digits fails current validation. Environment and resource-group names are different fields. Do not arbitrarily rename an existing resource group or plan to silence an error.

**Completion signal:** `plan_status: CREATED_LOCAL_ONLY`, `mutations_performed: false`. By default, `.lab/lab-training/` contains the following.

The documented candidate for a new agent/SFT base is **gpt-4.1-mini / 2025-04-14 / Standard**. Inspect the actual model/version in the output. Do not apply an older plan containing gpt-4o-mini; prepare a new plan instead. `--agent-sku` selects the SKU, not a workaround for changing model name/version.

| File or directory | Purpose |
|---|---|
| `config.json`, `template.json` | Exact new resources, deployments, and template hashes |
| `manifest.json` | Target IDs, creation intent, ownership, and stage records |
| `approval.example.json` | **Unapproved** format example |
| `group-authorization.example.json` | Unapproved example for separate resource-group creation |
| `cost-ledger.json` | Distinguishes SKUs, owned targets, and unknown costs |
| `artifacts/`, `evidence/` | Private execution/observation records for this environment only |
| `.gitignore` | Excludes this environment directory's records from Git |

Planning does not create `.env`. It is generated only after full deployment and ownership verification. Do not copy the private directory into a customer ZIP.

**Errors/recovery:** If the directory already exists, find the original plan rather than overwriting it. Do not resolve resource collisions by deleting an existing group or copying tags.

**Resume:** Use the same `config.json` for all later commands. Changes to model defaults, names, capacity, or retention need a separately approved plan that preserves the original state.

**Next:** A3.

#### Optional: plan a base deployment compatible with later SFT {#sft-base}

The new bootstrap agent candidate is **gpt-4.1-mini / 2025-04-14 / Standard**, and SFT uses the same base family/version. Explicit `--agent-sku Standard` fixes that SKU; the default requested ARM capacity is 20. Keep the approved role models for Judge, planner, and embeddings.

If you do not have a plan, check this candidate in A2. **If an older gpt-4o-mini or GlobalStandard-agent plan exists and the intended new resource group is still empty**, create a new plan in a separate local environment without editing the failed/previous plan. Replace the resource-group value below with the **same new group's name** from the original private record.

```bash
export NEW_RESOURCE_GROUP="YOUR_EXISTING_EMPTY_NEW_LAB_RESOURCE_GROUP"
python3 -S -m lab.bootstrap plan --subscription "$AZURE_SUBSCRIPTION_ID" --tenant "$AZURE_TENANT_ID" --expected-user "$EXPECTED_AZURE_USER" --environment lab-training-sft --root .lab --resource-group "$NEW_RESOURCE_GROUP" --agent-sku Standard
```

**Commands explained:** `export NEW_RESOURCE_GROUP` identifies only the **still-empty lab group created under the original intent**. The following `plan` creates a **separate local plan** with that explicit target. Knowing a group name neither proves ownership nor deploys to it. Binding to the original receipt and validating fresh approval still follow.

In A3, select the actual new `lab-training-sft` directory and prepare complete approval for that scope. In A5, bind the original intent/creation receipt with read-only checks, then apply **only the selected new plan**. Do not automatically convert or apply the failed gpt-4o-mini or previous GlobalStandard plans as well. If the local directory exists, choose another new name instead of overwriting it. Do not force the empty-group procedure onto a group that already contains resources.

The exact base Standard quota name is **`OpenAI.Standard.gpt4.1-mini`**; the separate tuned quota is **`OpenAI.Standard.gpt4.1-mini-finetune`**. Unlike model name `gpt-4.1-mini`, the usageName has no hyphen after `gpt`. Do not infer these by modifying a GlobalStandard quota or an older model name. Observed headroom was 5000 base and 500 fine-tuned, in the ARM/quota units at observation time—not free usage or a guarantee of success. A tuned Standard deployment is a separate step after a successful SFT job.

### A3. Run read-only preflight checks {#a3-읽기-전용-사전-점검}

**Purpose:** Check identity, region, providers, permissions, model versions, and quotas without deployment.

**Your task:** Set the first line to your actual directory. Use the original path if your plan is elsewhere.

**SDK-free does not mean offline.** `plan`, help, and local schema inspection do not call Azure. `preflight` and `status` are **read-only Azure queries** requiring CLI sign-in and network access. `-S` does not make every bootstrap command offline or eliminate existing resource costs.

**Run:**

```bash
export LAB_ENV_DIR="$PWD/.lab/lab-training"
export LAB_BOOTSTRAP_CONFIG="$LAB_ENV_DIR/config.json"
export LAB_COST_APPROVAL_FILE="$LAB_ENV_DIR/approval.json"
python3 -S -m lab.bootstrap preflight --config "$LAB_BOOTSTRAP_CONFIG"
python3 -S -m lab.bootstrap status --config "$LAB_BOOTSTRAP_CONFIG"
```

**Commands explained:**

| Line | What it does and records |
|---|---|
| The three `export` lines | Pass the same environment directory, plan JSON, and approval path to later commands. They do not create a missing approval file or change approval state. |
| `preflight --config ...` | Makes **read-only Azure checks** of identity, region, model/SKU, quota, permissions, and available provider validation. Records readiness/blocker evidence privately. |
| `status --config ...` | Queries actual resources, deployments, and ownership connected to the existing plan. Does not replace full preflight or model inference. Both commands take plan JSON—not `.env`—as `--config`. |

**Completion signal:** The read-only report identifies the identity, NCUS, exact model/version/SKU, quota family, and regional capacity. If you have not supplied approval yet, read the top-level approval blocker separately from `readiness_status`. `READY` or `OBSERVED` does not verify inference.

| Output | Exact interpretation |
|---|---|
| `CREATED_LOCAL_ONLY` | Plan files created; the default approval example is unapproved |
| `BLOCKED_AWAITING_APPROVAL` with readiness `READY` | Technical readiness is separate from **a valid approval file for this plan** |
| `READY_FOR_APPROVED_APPLY` / `APPROVED` / `PENDING_EXECUTION` | Approval/read-only readiness checked, not proof of apply or actual service execution |
| `OBSERVED` / `NOT_CHECKED_BY_STATUS` | Remote state observed; status did not repeat full readiness checks |
| `BLOCKED` | Technical/scope error. Do not automatically bypass with another region, account, or permission scope |

The [infrastructure document](../../infra/README.md) and plan define model deployment candidates. These recorded role examples do not guarantee current availability or success.

| Role | Model and version | Caveat |
|---|---|---|
| Agent / same-base SFT | gpt-4.1-mini / 2025-04-14 / Standard | Explicit new candidate; catalog `Legacy` and fineTune markers were observed. Verify actual creation/training support |
| Judge | gpt-5.4-mini / 2026-03-17 | Actual evaluation-request support and permissions are separate |
| Planner / Optimizer | gpt-5.5 / 2026-04-24 | Roles can share a model; do not automatically substitute another |
| Embedding | text-embedding-3-small / 1 | Later verify index dimensions against actual responses |

ARM `capacity` units depend on the model/SKU. Do not multiply every value by 1,000 TPM. If catalog minimum/step is `null`, do not invent a value. Distinguish the base model's exact `usageName` from `-finetune` quota.

**Errors/recovery:** If the current identity cannot query providers, create resources, or assign roles, the operator must follow the approved permission path. The tool does not automatically register providers, modify shared permissions, or change regions.

**The first observed failure:** Despite catalog `Deprecating`/fineTune markers and quota, Azure validation rejected gpt-4o-mini / 2024-07-18 with `ServiceModelDeprecated`, citing **retirement from 2026-03-31**. Preserve the first rejected creation request, zero child resources, and original ARM deployment 404. Selecting a new candidate before generating responses was environment recovery—not an experiment showing model-quality improvement. Metadata alone does not establish success for the replacement either.

**Resume:** Repeat only read-only preflight/status for the same plan. Quota headroom is neither free calls nor deployment success.

**Next:** A4.

### A4. Bind actual approval to the plan {#approval}

**Purpose:** Prevent billable changes based on a different scope's approval or a mere example file.

**Your task:** An authorized operator prepares this plan's private approval file using actual consent. Inspect the [approval schema](../../infra/approval.schema.json) and the plan-generated example. Neither a participant nor AI should invent approval on someone's behalf.

To inspect the public format without exposing identities or approval contents:

```bash
python3 -S -m json.tool infra/plan.schema.json
python3 -S -m json.tool infra/approval.schema.json
```

**Commands explained:** The first line displays the plan's field contract; the second displays the approval-record contract locally. They read public **schemas**, without filling in or signing approval values. A file hash checks content consistency; it is not itself a signature proving human consent.

**Run · validate an already prepared approval record only:**

```bash
python3 -S -m lab.bootstrap preflight --config "$LAB_BOOTSTRAP_CONFIG" --approval "$LAB_COST_APPROVAL_FILE"
```

**Command explained:** Adds `--approval` to A3's checks to verify that the current approval file matches **this plan's scope, hashes, validity period, and limits**. It combines Azure state queries with local approval validation—not apply or paid model inference. Do not continue if the file is missing or invalid.

Check plan/template hashes, models, scope, approver, validity, actual retention, Global processing, call/candidate/epoch/job/wait limits, and separate resource-creation/RBAC approvals. Review lifecycle conditions, ongoing hosting, and uncertain costs too. A checkbox acknowledging retirement does not re-enable a model the provider refuses.

**A scope summary is not a complete approval file.** Do not pass a private summary's `budget_cap: null` directly to bootstrap. Using `approval_template(config)` or the plan's example, the authorized operator records real consent in the complete schema.

For the recorded no-cap authorization, bootstrap fields were `budget_policy: NO_MONETARY_CAP_EXPLICITLY_APPROVED`, `budget_amount: null`, `acknowledge_no_monetary_cap: true`, and **nonempty private `request_evidence`**. Actual approver/time/validity, USD currency, exact scope/models, creation/RBAC/Global-processing approval, retention, and finite work limits must also validate. Describing these fields is neither an approval file nor authorization for another user's spending.

`null` does not mean missing approval, zero cost, or free service. Do not block the recorded authorization with the obsolete USD 50 proposal or fabricate a numeric cap for convenience. A finite-budget policy may be chosen for a separately authorized scope, but must not be silently substituted here.

Technical minimum log retention and user-authorized retention are different. Do not turn an example's 30 days into an approval fact. Other workshops must use their own customer's actual cost, processing, and retention authorization.

**Completion signal:** Approval validation passes for the exact scope, and separate readiness is healthy. This alone creates no resources and runs no model.

**Errors/recovery:** If real approval and schema/code disagree, fix and verify the integration contract rather than distorting consent. Do not turn no-cap approval into a finite budget or reuse the file for another plan.

**Resume:** Preserve the original approval record. Explicitly supply the current approval rather than silently overwriting the initial path recorded in `.env`.

**Next:** A5, only after checking valid approval, current readiness, and provider validation for the new plan.

### A5. Apply the same new environment once {#a5-같은-신규-환경을-한-번만-적용}

**Purpose:** Create only approved resources in the ownership-verified new group, and safely resume partial execution.

**Your task:** Ensure no other operator/process is applying the same environment. **This step changes Azure and creates billable resources. The recorded integration reached actual `APPLIED` after recovery that preserved the failure history.**

**If only the resource group has already been created, bind it first:** An integration operator with the **original precreation intent and actual creation receipt** can perform the following read-only binding. Replace paths with original private records. Do not fabricate example JSON to claim past creation. For an ordinary new plan with no group yet, skip this binding; apply records ownership intent before creation.

```bash
export RG_INTENT_FILE="YOUR_PRIVATE_PRECREATION_INTENT_JSON"
export RG_CREATED_FILE="YOUR_PRIVATE_CREATION_RECEIPT_JSON"
python3 -S -m lab.bootstrap bind-group --config "$LAB_BOOTSTRAP_CONFIG" --intent "$RG_INTENT_FILE" --created "$RG_CREATED_FILE"
```

**Commands explained:** The exports point to existing private **precreation intent** and **creation receipt** files. `bind-group` checks those records against the current plan and the empty group in Azure, then binds the local ownership ledger. It does not manufacture ownership by changing names/tags, create Azure resources, or modify permissions.

The actual new group's scope, original tags, and creation evidence must match. A matching group name is not enough. `prepare-group` is used **before** external group creation; `confirm-group` is the read-only confirmation of that original intent. `bind-group` likewise does not retroactively fix tags/permissions or modify existing resources.

**Run · operator only, after approval and ownership checks:**

```bash
python3 -S -m lab.bootstrap apply --config "$LAB_BOOTSTRAP_CONFIG" --approval "$LAB_COST_APPROVAL_FILE"
python3 -S -m lab.bootstrap status --config "$LAB_BOOTSTRAP_CONFIG" --approval "$LAB_COST_APPROVAL_FILE"
```

**Commands explained:**

| Command | What it does and its cost boundary |
|---|---|
| `apply --config ... --approval ...` | After checking plan, approval, identity, ownership, and provider validation, applies **real ARM resources and approved RBAC**. Ongoing billable resources may result. Deployment IDs, partial successes, and errors are preserved. This is not an ordinary participant connection command. |
| `status --config ... --approval ...` | Queries remote state/ownership for **the same plan** just applied. Does not submit another apply or generate a model response. After completion, use status and participant preflight to connect. |

Bootstrap saves the intent ID, checks target ownership, then uses a group-scoped Incremental deployment. It does not adopt existing groups/resources or another environment by name alone. Unknown targets, model changes, or permission-scope changes are stop conditions.

**Completion signal:** Actual ARM deployment completes, manifest/inventory agree, and `.env` is generated. Bootstrap reports `APPLIED` alongside `data_plane_verified: false` / `live_status: NOT_VERIFIED`. Infrastructure verification does not prove inference, MCP, calibration, or trace ingestion succeeded.

**Errors/recovery:** A timeout does not prove resources are absent. Check saved deployment IDs, ledgers, and remote state. Do not change shared environments through automatic rollback, deletion, or permission repair.

**Resume:** First inspect `status`, then continue `apply` with the same config and valid approval. Remove a stale lock only after confirming the recorded PID has exited and no other operation is active. Do not arbitrarily defeat locking.

Do not add `--confirm`, `--resume`, `--force`, `--adopt`, or `--delete` to bootstrap apply. Those differ from batch `run --resume`. `apply --what-if` is a read-only comparison only for an already ownership-verified group, yielding `WHAT_IF_ONLY`. Do not create a group just to run what-if, or interpret it as cost authorization or deployment success.

**Next:** A6.

### A6. Check the runtime and hand it to participants {#a6-런타임-환경-확인-후-참가자에게-전달}

**SDKs are required from this step onward.** Unlike SDK-free bootstrap in A1–A5, runtime preflight uses the `.venv` prepared in [participant step 02](handbook.md#prepare). Activate an existing environment instead of restarting with installation/deployment.

**Purpose:** Use the exact newly created deployment, Search, and monitoring endpoints, and keep evidence separate by environment.

**Your task:** Read the private `.env` and compare deployment names/endpoints with the actual manifest. Do not substitute `.env.example` placeholders or old workshop values. Do not execute `.env` as shell code.

**Run:**

```bash
export LAB_ENV_FILE="$LAB_ENV_DIR/.env"
export LAB_ARTIFACTS_DIR="$LAB_ENV_DIR/artifacts"
python -m lab --config "$LAB_ENV_FILE" preflight
python -m lab validate
```

**Commands explained:** `LAB_ENV_FILE` points to the generated `.env`; `LAB_ARTIFACTS_DIR` selects the same environment's results directory. Runtime `preflight` queries the identity/deployments the SDK will use and records `preflight.json`; `lab validate` locally checks the 100 source cases and generated data. Neither evaluates quality nor tests the first model response.

Set `LAB_ARTIFACTS_DIR` in each Python process's environment **before it starts**. Restore exports in new terminals/processes. Do not change the path after importing modules and mix evidence across environments.

**Completion signal:** `preflight: PASS`, all 100 cases intact, and the correct actual environment. `.env` records `EMBEDDING_DEPLOYMENT`, `LAB_ARTIFACTS_DIR`, `LAB_BOOTSTRAP_CONFIG` and `BOOTSTRAP_CONFIG` pointing to the same plan, the initial `LAB_COST_APPROVAL_FILE`, and new monitoring resource IDs. No keys/passwords are required.

After bootstrap, main-CLI `--confirm` operations and SFT deployment use `BOOTSTRAP_CONFIG` to verify completed bootstrap ownership and the actual new group/account. Ownership does not grant current task authorization; validate private approval and call/job limits separately. Do not bypass with old environment values or fabricated hashes/receipts.

**Errors/recovery:** If code forces out-of-repository artifact paths through `.relative_to(ROOT)`, use the `artifact_reference` contract instead. Do not hide the problem by copying private files into the repository.

**Resume:** Restore the same `.venv` and variables after reopening a terminal. Do not restart from package installation, redeployment, or resource-group creation.

**Participant handoff:** Supply the actual account/tenant/subscription, private `LAB_ENV_DIR` and current `LAB_COST_APPROVAL_FILE` paths, current authorization scope, new `APPLICATIONINSIGHTS_RESOURCE_ID`, and retention/cost-check responsibilities. Never publish `.env`, manifests, or approval files in public channels/packages. Give participants accessible actual paths, not example directory names.

**Next:** Participants set these values once in [step 02](handbook.md#prepare), then continue through 03–06 in the same environment. The operator checks prompt-agent **Agent Optimizer** access, actual optimizer/judge deployments, and the one-candidate setting beforehand. Do not make Prompt Optimizer, separate managed evaluations, or SFT extra prerequisites. Do not precreate participant responses/evaluation results or count connectivity checks as quality evaluation.

## Which identity needs which permissions? {#rbac}

This is a **plan for new resources only**. Check actual role definitions and API operations first. Reading the table is not evidence that roles were assigned.

| Identity | Operation | Roles to review at minimum scope |
|---|---|---|
| Operator / participant | Foundry account data operations and model calls | Task-appropriate Azure AI Developer / Cognitive Services OpenAI User on the new account |
| Operator / participant | Current Agent Service project operations | Foundry User on the new project. Do not assume Azure AI Developer alone covers agent CRUD |
| Operator / participant | Prepare Search schema/content | Search Service Contributor + Search Index Data Contributor on the new Search service |
| Project MI | Read IQ search content | Search Index Data Reader on the new Search service |
| Project MI | Model/monitoring access | Appropriate model role on the new account and publishing permissions on new monitoring resources |
| Search MI | LLM query planning and vectorizer model access | Check Cognitive Services User on the new Foundry account against current official documentation |
| Observability user | Read traces | Task-appropriate read roles on new Application Insights / Log Analytics resources |

Permission to assign roles is a separate administrative capability. Do not simplify setup by newly granting participants subscription Owner/Contributor. Do not confuse the Search MI with the project MI.

Cognitive Services User may include key-list operations. That is not an instruction to use key authentication. Preserve bootstrap's Entra-authentication and disabled-local-auth boundaries; do not retrieve or distribute keys.

References: [Foundry RBAC](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) · [Search RBAC](https://learn.microsoft.com/en-us/azure/search/search-security-rbac) · [Search MI access for model-backed knowledge bases](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-create-knowledge-base#configure-access)

### Official implementation contracts {#references}

These official contracts informed infrastructure preparation. They are **planning references**, not proof of completed role assignment, deployment, or execution.

| Contract to check | Official reference |
|---|---|
| Foundry account/project system identities and project properties | [accounts/projects · 2025-06-01](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2025-06-01/accounts/projects) |
| Pinned model versions, NoAutoUpgrade, SKUs, and tags | [accounts/deployments · 2025-06-01](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2025-06-01/accounts/deployments) |
| Search MI, Basic, and disableLocalAuth | [searchServices · 2025-05-01](https://learn.microsoft.com/en-us/azure/templates/microsoft.search/2025-05-01/searchservices) |
| Extension-role scope limited to new resources | [ARM extension resource scope](https://learn.microsoft.com/en-us/azure/azure-resource-manager/templates/scope-extension-resources) |
| AAD authentication for project connections | [accounts/projects/connections · 2025-06-01](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2025-06-01/accounts/projects/connections) |
| Log Analytics pricing plan and retention | [workspaces · 2023-09-01](https://learn.microsoft.com/en-us/azure/templates/microsoft.operationalinsights/2023-09-01/workspaces) |
| Workspace-based Application Insights | [components · 2020-02-02](https://learn.microsoft.com/en-us/azure/templates/microsoft.insights/2020-02-02/components) |

Do not combine Search `disableLocalAuth: true` with incompatible `authOptions`. This is a check against the new template/API contract, not an instruction to read keys or change an existing Search service.

## Costs, retention, and access to newer features {#cost}

| Cost category | How to interpret it |
|---|---|
| Search Basic | Read-only NCUS price reference: USD 0.101/hour, approximately USD 2.424 per 24 hours or USD 73.73 per 730 hours. Not an actual bill or total lab cost |
| Model / Judge / planner / embedding | Actual requests/tokens for each. Quota headroom is not a free allowance |
| Optimizer | Candidate, agent, tool, and evaluation usage. Do not reduce hidden internal calls to “one API call” |
| SFT | Separate training, base/tuned inference, and continuous tuned-model hosting |
| Logs / retention | Ingestion and retention costs. An ingestion cap is not a strict monetary cutoff |
| Unaggregated / unknown | `UNKNOWN_NOT_ZERO` or awaiting observation—not zero |

No monetary cap does not justify redundant or duplicate requests. Expanding beyond agreed call/candidate/job/wait limits requires separate judgment. **Retention** is the current boundary; do not use deletion as automatic cost control.

Check Prompt Optimizer, prompt-agent Agent Optimizer, SFT, Frontier, and trace ingestion separately. A directly matching official Frontier API/support route remains `NOT_VERIFIED`; that is not proof it does not exist. The prompt-agent portal wizard is the documented Agent Optimizer path; no hosted-agent conversion is required.

## Handoff checklist {#handoff}

- [ ] Actual identity, subscription, tenant, NCUS, and new-resource scope are verified.
- [ ] The original intent and ownership manifest allow the same group/environment to be resumed.
- [ ] Approval examples and real authorization records are distinguished and stored privately.
- [ ] The recorded no-monetary-cap authorization is interpreted together with finite work limits; other participants use their own approval.
- [ ] Model lifecycle, exact usageName, capacity units, and role-propagation limits are explained.
- [ ] `.env` and run records are excluded from source/distribution ZIPs.
- [ ] Deployment, actual inference, quality, and observability states are recorded separately.
- [ ] The resource group is preserved; no deletion command is run.
- [ ] Actual environment/approval paths and the monitoring ID are supplied, with a link to participant step 02.
- [ ] Existing lab environments are not recreated/redeployed, and access to the core Agent Optimizer path is checked.
