# Isolated, approval-bound bootstrap

`lab.bootstrap` implements migration requirements R08/R10/R12 without reusing v1
resources or changing existing permissions. It uses only Python's standard
library and an already authenticated Azure CLI. No SDK installation, model call,
provider registration, resource deletion, or subscription switch is performed.

**Coordinated LIVE workflow: `PENDING_EXECUTION` (2026-09-30).**

The coordinator reports explicit approval **by reference**, followed by explicit
removal of the monetary ceiling. **No monetary cap applies to this approved
run**; its operational scale remains bounded: at most 300 combined
model/judge/planner requests, one job per
optimizer with at most two candidates, one SFT job using 56 train / 12 validation
rows and one epoch, 12 fresh-holdout rows, and at most 60 minutes waiting per job.
Only synthetic-data GlobalStandard / Global-or-Developer processing and minimum
RBAC on the new resources are authorized. Preserve the new RG for review:
**deletion is not authorized**. No existing/shared resources, other regions, or
expanded spend are covered. Original approval messages/records remain private.

The coordinator, not this implementation agent, performs cloud changes. These
documented limits do not automatically authorize a local plan: the exact-scope
private approval record must still validate before `apply`, and ownership must
still be proven. A name reported unused is not an ownership proof. Passing
read-only quota/identity checks is not ARM provisioning evidence or LIVE
model/evaluation/training success. Feature access checks remain separate gates.

## Local planning and read-only verification

Supply the intended subscription, tenant, and user explicitly; never put personal
identifiers into `bootstrap.json`. Run these commands from the repository:

```sh
python -m lab.bootstrap plan \
  --subscription "$AZURE_SUBSCRIPTION_ID" \
  --tenant "$AZURE_TENANT_ID" \
  --expected-user "$EXPECTED_AZURE_USER" \
  --environment lab-training
python -m lab.bootstrap preflight --config .lab/lab-training/config.json
python -m lab.bootstrap status --config .lab/lab-training/config.json
```

The new group is `rg-foundry-eval-v11-<UTC date>-<random suffix>`, always in
`northcentralus`. A private, ignored directory contains `config.json`, the exact
resource manifest, a hash-pinned `template.json`, an **unapproved** `approval.example.json`, the cost ledger,
and separate `artifacts/` and `evidence/` directories. Existing directories and
`.env` files are never adopted or overwritten. `.env` is produced only after
successful provisioning. Set `LAB_ARTIFACTS_DIR` from that file before importing
runtime modules; it must not point at another environment's artifacts.
The planned 30-day retention is a technical minimum, **not retention approval**.
Generated `LAB_ARTIFACTS_DIR` and bootstrap paths are absolute, including for
environments outside the repository. Bootstrap does not use `.relative_to(ROOT)`
or import `lab.files`; it remains SDK/dotenv-free. Runtime modules should use
`lab.files.artifact_reference(path)` for stored artifact references rather than
assuming every environment is under the repository.
`LAB_BOOTSTRAP_CONFIG` points to the local plan. `LAB_COST_APPROVAL_FILE` records
the approval used when `.env` was first created; subsequent approvals must be
passed explicitly to the runtime instead of modifying or silently overwriting
the existing environment file.
`BOOTSTRAP_CONFIG` is an equivalent generated alias for the parent's
`Config.bootstrap_config` integration; it is not an arbitrary existing-account
configuration.

Default choices are **candidates, not approval or availability guarantees**:

| Use | Model | Pinned version | SKU | Requested ARM capacity |
|---|---|---|---|---|
| Agent / same-family SFT base | gpt-4.1-mini | 2025-04-14 | Standard | 20 |
| Judge | gpt-5.4-mini | 2026-03-17 | GlobalStandard | 20 |
| IQ planner + optimizer | gpt-5.5 | 2026-04-24 | GlobalStandard | 20 |
| Embeddings | text-embedding-3-small | 1 | GlobalStandard | 10 |

The 2026-09-30 regional catalog marked gpt-4o-mini **Deprecating**, but actual
Provider validation subsequently returned **`ServiceModelDeprecated`**, reporting
deprecation since **03/31/2026**. This overrides catalog flags and available
quota: the original gpt-4o-mini draft is **not a deployable selection**.
`accept_deprecated_models` acknowledges a catalog warning; it cannot override
service rejection. The coordinator subsequently **explicitly selected**
`gpt-4.1-mini` version `2025-04-14` on `Standard`, and that is now the default
draft agent/base choice. Its observed catalog lifecycle is **Legacy** with
fine-tuning capabilities; Provider validation is still mandatory. Preserve the
older failed plan/approval/attempt evidence. Pass `--models-json <file>` with
`{"models": [...]}` to pin an explicit selection; no automatic family/region
replacement is performed.
Each entry has `name`, `version`, `sku`, `capacity`, `deployment`, and `roles`;
optional `usage_name` pins the exact live base-SKU quota identifier.
Exactly one mapping is required for each of `agent`, `judge`, `planner`,
`optimizer`, and `embedding`; planner and optimizer may share a deployment.
Floating versions and provisioned-throughput SKUs are intentionally unsupported.

For the selected same-family SFT comparator, explicitly select
`plan --agent-sku Standard` (or `sku: "Standard"` in the agent entry of
`--models-json`). The selected base is **gpt-4.1-mini 2025-04-14**;
judge/planner/optimizer/embedding stay unchanged. Preflight checks the catalog's
**`OpenAI.Standard.gpt4.1-mini`** (no hyphen after `gpt`), not a guessed
`OpenAI.Standard.gpt-4.1-mini`, GlobalStandard, or `-finetune` quota.
The later tuned Standard deployment separately requires
`OpenAI.Standard.gpt4.1-mini-finetune` quota. Neither training mode nor deployment
SKU is automatically switched. The main bootstrap does not create tuned hosting.

An already generated plan is immutable: create a **new local
environment** with the explicit new model/version/SKU and the same named,
coordinator-created **empty** RG, then `bind-group` with its original receipts.
Obtain a new exact-scope approval for that plan; do not edit an existing config
or assume its old approval covers a new SKU/hash. Do not run both old and new
plans. If child provisioning has started, stop rather than repointing the plan.
The SFT adapter must pin the same selected model/version and verify base/tuned
Standard deployments at execution time; changing bootstrap alone does not prove
that adapter readiness or training access.

Preflight verifies the active CLI subscription/tenant/UPN and independently checks
the signed-in user's object ID. It never infers the MCP principal from tenant or
subscription agreement. Providers and existing provisioning/role-assignment
permissions must already be available.

Model/version/SKU discovery and quota checks use **subscription + region**,
not an existing account. The exact catalog `usageName` distinguishes base-model
quota from similarly named fine-tuning quota. Available quota is `limit -
currentValue`, aggregated across requested deployments sharing the same quota
family. A resume credits only verified owned deployments, never unrelated usage.
Regional model capacity is checked separately. ARM capacity is not universally
1,000 TPM: live per-model constraints and rate limits are retained without
inventing a conversion. Available quota means unallocated capacity, **not free
inference**. No alternate-region retry occurs.
Quota identifiers are read from the matching live SKU, never built by
concatenating the display model name. If multiple base-SKU records are
ambiguous, preflight stops; an explicit `usage_name` must match a real catalog
record and cannot point at fine-tuning quota.

When the owned RG exists, `preflight` additionally calls
`az deployment group validate --validation-level Provider` with the pinned
template and exact private parameters. `apply` must pass the same Provider
validation before every child-resource create/retry and uses that **same
parameter file** for creation. A catalog/quota pass is not deployability proof.
If the new RG is still absent, read-only preflight explicitly reports
`DEFERRED_RESOURCE_GROUP_ABSENT`; apply may create only the approved empty RG
before Provider validation, not any child resource. Failed validation is
`BLOCKED` / `BLOCKED_PROVIDER_VALIDATION`, never a success fallback.

Validation requests/results and Azure failure stdout/stderr/nested error bodies
are preserved in private `evidence/*.local.json` files. Public errors select the
actionable nested code (for example `ServiceModelDeprecated`, not merely
`InvalidTemplateDeployment`) and redact identities, resource scopes, URLs, and
credential-like values from messages. Authorization failures are not reclassified
as resource absence. Do not publish raw diagnostics.

`*.local.json` contains original identities/resource IDs and remains local.
`*.redacted.json` and the preflight/status return values use allowlisted derived
fields and a scope fingerprint; these do not establish a cryptographic signature,
independent approval, data-plane readiness, or a successful paid experiment.
The top-level status stays `BLOCKED_AWAITING_APPROVAL` when authorization is
missing/invalid, even if `readiness_status` is `READY`. Read-only resource status
uses `observation_status: OBSERVED`; it is not a readiness test. An optional
explicit `--approval` is validated without triggering any paid or mutating
operation. `live_status` remains `NOT_VERIFIED`. Unapproved preflight/status
returns exit code 2; local plan creation returns exit code 0 and a blocked
authorization status because the local planning action itself completed.

## Approval and later apply

### A separately authorized empty group

If the user authorizes the **empty resource group only**, the coordinator can
prepare a group-specific intent **before** its external creation:

1. `plan --resource-group <unused lab RG name>` creates an explicit local scope.
   A supplied name still requires the `rg-foundry-eval-v11-<date>-<6–12 hex>`
   shape and never authorizes adopting an existing group.
2. Record the actual user request in a separate local file derived from
   `group-authorization.example.json`. It permits exactly
   `resource_group.create`; paid resources, RBAC, and deletion remain explicitly
   false, and `preserve_group` remains true.
3. `prepare-group --config <config.json> --authorization <group-auth.json>`
   verifies CLI identity and group absence read-only, durably writes **only
   the group's pending ID**, and creates `group-create-contract.local.json`.
   The contract contains the exact subscription, location, ownership tags,
   conditional PUT headers/body, and local config path. It is local evidence,
   not a public/commit-safe report. This command does not send the PUT.
4. The separately authorized coordinator must recheck absence and use the
   contract without changing its tags or scope. Only that coordinator creates
   the group. `confirm-group --config <config.json>` then checks the same
   pre-recorded ownership and empty resource inventory read-only.

Both commands leave top-level paid-resource status `BLOCKED_AWAITING_APPROVAL`;
their own successful local/observation steps return exit code 0. Group-only
authorization cannot be supplied as full bootstrap approval. Later approved
`apply` resumes the exact preserved group rather than creating another.

**Do not create first and copy tags later.** If the group already exists when
preparing the intent, bootstrap refuses to adopt it—even with identical-looking
tags. For a coordinator-created new group with the original
`INTENT_RECORDED_BEFORE_CREATE` journal **and** successful creation response,
`bind-group --config <config> --intent <journal> --created <response>` verifies
exact subscription/tenant/group/location, ownership/retention tags, signed-in
identity, and the live group's **empty** resource inventory. It copies and hashes
both receipts privately and binds only that group in the local manifest.
It neither changes the plan hash nor writes Azure tags/roles/resources. Later
`apply` preserves those original group tags and uses the planned ownership tags
on its new child resources. Changed receipts or any existing child resource
block reconciliation. This local receipt/hash check is not independent proof
of who authored the journal.

### Full bounded approval

The machine-readable syntax is [`approval.schema.json`](approval.schema.json).
The generated local config follows [`plan.schema.json`](plan.schema.json);
register both schema IDs if validating references with a JSON Schema validator.
Generate the exact local scaffold with `approval_template(config)`; copy
`scope_sha256` and `models` unchanged from that plan. Record approval-by-reference
evidence privately, not in the committed template/schema. Do not substitute a
proposal document for an actual authorization record. `runtime_bounds` supports
the coordinator's optimizer/job/data-row limits, but the parent runtime must
enforce consumption counters; bootstrap validates bound types and consistency
but never submits those operations. Valid read-only approval reports
`live_status: PENDING_EXECUTION`, not execution success.

No approval is created on the user's behalf. After an authorized person reviews
the pinned scope and costs, they must create a separate local approval JSON from
the example and explicitly set:

- `approved`, `approved_by`, timezone-aware `approved_at` and `expires_at`;
- `currency`, finite positive `budget_amount`, `retention_days`,
  `max_hosting_hours`, and `max_wait_seconds`;
- `allow_global_inference`, separate `allow_training` /
  `allow_global_training`, and `max_calls`, `max_candidates`, `max_epochs`,
  `max_training_jobs`;
- separate `allow_resource_creation` and `allow_rbac_assignments`;
- `accept_deprecated_models`, `acknowledge_continuous_hosting`,
  `acknowledge_unknown_cost`.

The default `budget_policy` is `BOUNDED`. A null amount is never inferred as
permission. If the coordinator holds a **subsequent explicit user authorization
waiving a monetary ceiling**, record
`budget_policy: NO_MONETARY_CAP_EXPLICITLY_APPROVED`, `budget_amount: null`,
`acknowledge_no_monetary_cap: true`, and the original private `request_evidence`.
All finite call/candidate/job/epoch/wait bounds, expiry, processing consent,
new-resource-only RBAC, synthetic data, preservation, and no-deletion rules
remain unchanged. The current run has that explicit later authorization; a
missing or ambiguous amount in another environment must never be interpreted
as unlimited permission.

Disabled training requires zero training limits and no global-training consent.
Zero call/candidate bounds do not authorize inference/optimization. Runtime code
must enforce those bounds separately: bootstrap **does not** submit training or
inference and is **not an Azure monetary spending cap**. The approval binds the
entire local configuration and template hash, including every name/model/capacity,
so edited scope requires a new plan and new authorization.

Only after approval:

```sh
python -m lab.bootstrap apply \
  --config .lab/lab-training/config.json \
  --approval .lab/lab-training/approval.json
```

Apply rechecks identity, quota, approval, and ownership. Pending target IDs are
flushed before each remote mutation. Group creation uses a last-moment collision
check and conditional PUT, followed by a tag/region check. ARM runs only at that
owned group with **Incremental** mode. Resource-scope assignments use deterministic
names, managed-identity principal types, and ownership descriptions. A new group
with no creation receipt is never adopted, even if its tags happen to match.
Provider errors and authorization failures are not treated as “resource absent.”

Interrupted deployments retain the local manifest and ledger. Reuse the same
config and valid approval to reconcile/poll a running or succeeded deployment.
A verified terminal failed/cancelled **owned** ARM deployment can be resubmitted
only with **both** explicit `apply --retry` and a current approval containing an
unconsumed, nonnegative `max_provisioning_retries`. That optional allowance
defaults to **zero**; removing a monetary ceiling does not permit unlimited
retries. Every recorded ARM create beyond the first consumes one allowance.
Provider validation still runs before an approved retry.

If a creation attempt was recorded but the corresponding deployment is absent,
its outcome is **`UNKNOWN_SUBMISSION`**: even `--retry` with budget cannot
blindly resubmit. An unresolved pending RG create is similarly blocked as
`UNKNOWN_GROUP_SUBMISSION`. Inspect original request/error/activity evidence;
do not forge journal state, delete resources, or treat “not found” as proof no
submission occurred. If the original deployment becomes observable as running
or succeeded, ordinary apply reconciles it without another create.

An unknown resource, changed
role scope, changed model, or missing previously owned group blocks mutation.
There is no automatic restore, rollback, delete, or “repair permissions” operation.
After a process crash, a stale `.bootstrap.lock` must be investigated against its
recorded PID before removing that **local** lock and resuming.

### Explicit dependency-only recovery

Cognitive Services can reject concurrent account/project/model writes with
`RequestConflict`. The template orders **project → serial model loop → Search
connection → App Insights connection**. It does not change any resource setting,
SKU, name, identity, role binding, or model to recover from that conflict.

For a failed initial bootstrap pinned to the earlier graph, the coordinator can
perform a narrowly verified **local revision**, rather than hand-editing hashes:

```sh
python3 -S -m lab.bootstrap repair-dependencies \
  --config .lab/lab-20260930-live/config.json \
  --approval .lab/lab-20260930-live/approval.execution.local.json \
  --max-provisioning-retries 2
```

By default this reads the original
`evidence/first-apply-failed-deployment.local.json` and
`evidence/first-apply-operations.local.json`. Alternate exact proof paths can be
supplied with `--failed-deployment` and `--failed-operations`. The recorded and
live deployment must be the **same terminal Failed correlation**, with unchanged
parameters, verified owned resources, and a project `RequestConflict` operation.
An absent or running deployment is not repairable through this command.

The command accepts only additive **resource `dependsOn` changes** to the current
checked-in template; every other JSON value must match the pinned template.
Before replacing owned local state, it archives the original config, template,
manifest, approval, cost ledger, and all failure evidence **byte-for-byte** under
`.repairs/<repair-id>/original/`. It Provider-validates the proposed graph
read-only, preserves the same instance/resource IDs and prior attempt history,
then rebinds only the template/scope hashes and creates a **new private approval
file**, whose path is returned. The old approval remains unchanged. Retry
allowance is explicitly limited to one or two total retries; it is not reset
per repair and does not waive call/job/processing/no-deletion restrictions.

Local write interruption rolls back from verified archived bytes. A pending
transaction blocks ordinary bootstrap commands; rerunning this same repair
command recovers its local transaction before rechecking the original failure.
It never deletes or writes an Azure resource.

The coordinator then explicitly invokes `apply --retry` with the **returned
approval path**, not the old approval. This is not automatic submission, proof
of successful provisioning, or general permission to edit/reuse arbitrary
existing resources.

For an already-owned group, `apply --what-if` performs read-only group what-if
without cost approval. It cannot create the group just to preview it. Full ARM
outputs stay in local evidence. A successful ARM deployment is followed by an
inventory check; it does not claim managed-identity propagation, telemetry
ingestion, IQ query planning, or model inference has been tested.

## Provisioned resources and cost boundaries

- AIServices S0 account and Foundry project, each with a system-assigned identity.
- Search Basic, one partition / one replica and system-assigned identity.
  `disableLocalAuth: true` is used **without** incompatible `authOptions`.
  The free semantic allowance does not make Basic hosting or IQ inference free.
- Log Analytics PerGB2018 with approved retention (minimum 30 days) and a 1 GB/day
  ingestion cap; workspace-based App Insights. Both disable local authentication.
  The ingestion cap is best-effort, not a strict financial limit.
- Four explicitly pinned model deployments; no dynamic quota, automatic model
  upgrade, spillover, fine-tuning job, or fine-tuned hosting deployment.
- A project Search connection using AAD, with the lab marker in its metadata.
  Resources supporting tags receive ownership tags; role assignments and
  connections use descriptions/metadata plus the manifest instead.
- A project `lab-appinsights` connection using **`ProjectManagedIdentity`**,
  category `AppInsights`, the new Application Insights **resource ID** as target
  and metadata `ResourceId`, and a lab ownership marker. It uses the public
  `2026-07-01` connection API and waits for the project and scoped publisher
  role before creation. No credential/key property is sent and local auth stays
  disabled.

The exact `ProjectManagedIdentity` value is published in
[`ConnectionAuthType` in the 2026-07-01 OpenAPI][connection-openapi]. The generic
Bicep reference's derived-auth examples omit this newer enum value; it is **not**
interchangeable with `ManagedIdentity`, `AAD`, or an invented credentials object.
The official [starter template][starter-connection] establishes that an
AppInsights connection targets the resource ID; its older **ApiKey** auth example
is intentionally not copied. Microsoft's [trace setup][trace-setup] documents
automatic server-side tracing after the connection, and the [Entra ingestion
guide][trace-entra] specifies **project managed identity** plus
**Monitoring Metrics Publisher** at that App Insights scope.

ARM success verifies this connection's type, target, and ownership, but returns
`trace_ingestion_verified: false`. After parent-authorized agent execution,
wait for RBAC/ingestion propagation (typically 2–5 minutes per the Entra guide)
and inspect the new trace before claiming server-side telemetry works.
Container-hosted agent code may additionally need its own Agent Identity
publisher role; this lab does not provision that different hosting path.

Operator roles are restricted to the new account/project/Search/monitoring
resources: Azure AI Developer for account-level learning-loop data operations,
Cognitive Services OpenAI User for inference, Foundry User on the new project for
current Agent APIs, Search Service Contributor + Search Index Data Contributor
for schema/content setup, and scoped monitoring read/publish access. No Owner,
Contributor, subscription-scope, or resource-group-scope grants are added.

The project identity has Search Index Data Reader, OpenAI User on its new account,
and telemetry publishing. The Search identity has **Cognitive Services User** on
the new account, as required by the current
[knowledge-base access documentation][search-access] for model-based planning.
That documented role includes key-list actions, but local authentication is
disabled and bootstrap never retrieves or uses service keys. It is not a reason
to enable keys. Operator UPN/object ID and managed principal IDs are local inputs
or ARM references, never hardcoded into the template.

The ledger records each target ID, SKU and observed/recorded creation state.
Unknown estimates remain `null` / `UNKNOWN_NOT_ZERO`. Search's **continuous
hosting**, metered inference, logs/retention, and separately approved
**fine-tuning training** / **fine-tuned model hosting** are distinct entries.
The coordinator verified a North Central US Basic Search retail reference of
**USD 0.101/hour** on 2026-09-30: approximately **USD 2.424/24 hours** or
**USD 73.73/730 hours** for one search unit. The ledger stores this dated,
currency-specific **unit-price reference separately** from unknown total costs
and the approved budget. It is not a pricing guarantee, tenant-specific quote,
total experiment estimate, or approval; it excludes inference, IQ, telemetry,
training, and fine-tuned hosting charges.
Search does not stop billing when the approval expires; budget enforcement and
authorized eventual cleanup are separate responsibilities. No deletes are
implemented here.

## Integration contract and offline validation

`main(argv: list[str] | None) -> int` can be routed from `python -m lab bootstrap`
before importing the normal SDK/config stack. Python functions return dictionaries:

- `plan(*, subscription_id, tenant_id, expected_user, environment=None,
  root=Path(".lab"), location="northcentralus", retention_days=30, models=None,
  resource_group=None, agent_sku=None)`
- `group_authorization_template(config)`
- `prepare_group_creation(config_path, authorization_path, *, run=az_json)`
- `confirm_group_creation(config_path, *, run=az_json)`
- `bind_created_group(config_path, intent_path, created_path, *, run=az_json)`
- `repair_dependencies(config_path, approval_path, *, max_provisioning_retries,
  failed_deployment_path=None, failed_operations_path=None, run=az_json)`
- `require_owned_resources(config_path, account_id, *, run=az_json)`
- `preflight(config_path, *, run=az_json, persist=True, approval_path=None)`
- `apply(config_path, approval_path=None, *, run=az_json, what_if=False,
  retry=False, sleep=time.sleep, clock=time.monotonic)`
- `status(config_path, *, run=az_json, approval_path=None)`
- `validate_approval(config, approval, *, now=None)`

`BootstrapError` is a sanitized fail-closed exception. `run` is an injectable
`list[str] -> decoded JSON` Azure CLI adapter. Status/preflight evidence is
commit-safe by allowlisting, while `.env`, parameter documents, raw ARM output,
manifests, and ledgers remain local. This repository-relative template must also
be distributed if packaging bootstrap outside the repository.

Before a later hourly-billed SFT deployment or other new account mutation,
the caller must invoke `require_owned_resources(bootstrap_config, account_id)`.
This public **read-only** guard validates the immutable plan/template, persisted
creation receipts (including any coordinator-created RG binding), completed
bootstrap state, active CLI identity, and the live RG/account/ARM-deployment
IDs, tags, readiness, and deployment parameters. A matching SFT job scope alone
is insufficient. Arbitrary existing accounts and unfinished bootstrap plans
fail closed with `BootstrapError`. It performs no Azure writes and does not
rewrite the manifest. Its returned account/RG IDs are **private scope evidence**.
Current budget/processing approval and per-job call/candidate/epoch limits remain
separate caller checks; successful ownership verification never grants them.

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_bootstrap.py'
.venv/bin/python -S -m lab.bootstrap --help
```

Tests use a fake Azure control plane and project-local test directories. They do
not deploy, modify permissions, run paid models, or claim cloud validation.

[search-access]: https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base#configure-access
[connection-openapi]: https://github.com/Azure/azure-rest-api-specs/blob/main/specification/cognitiveservices/resource-manager/Microsoft.CognitiveServices/CognitiveServices/stable/2026-07-01/cognitiveservices.json
[starter-connection]: https://github.com/Azure-Samples/azd-ai-starter-basic/blob/main/infra/core/ai/ai-project.bicep
[trace-setup]: https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup
[trace-entra]: https://learn.microsoft.com/azure/foundry/observability/how-to/trace-ingestion-entra-authentication
