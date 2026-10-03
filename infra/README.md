# Isolated Foundry lab infrastructure

This directory contains the reproducible infrastructure contract used to prepare
an isolated lab environment. It supports steps **01–03** of the end-to-end
participant guide. A participant with approved provisioning access can prepare
their own environment; otherwise the owning operator performs these steps and
hands off actual configuration values.

Use the [operator guide](../guide/en/admin-setup.md) or
[한국어 운영자 가이드](../guide/admin-setup.md) for the current prerequisites.
The template also provisions the read-only knowledge and monitoring connections
used by the Contoso sample agent. The participant guide connects this setup to
**Foundry Evaluation → Agent Optimizer → same-criteria reevaluation → cleanup**.
Creating only an empty portal project does not prepare this complete sample.

## What bootstrap does

`lab.bootstrap` uses Python's standard library and an authenticated Azure CLI.
It separates local planning, read-only readiness checks, scope-bound approval,
resource creation, ownership records, and runtime verification.

```bash
python3 -S -m lab.bootstrap plan \
  --subscription "$AZURE_SUBSCRIPTION_ID" \
  --tenant "$AZURE_TENANT_ID" \
  --expected-user "$EXPECTED_AZURE_USER" \
  --environment lab-evaluation-en \
  --location northcentralus
python3 -S -m lab.bootstrap preflight --config .lab/lab-evaluation-en/config.json
python3 -S -m lab.bootstrap status --config .lab/lab-evaluation-en/config.json
```

**Command details:** `plan` creates only private local files. `preflight` reads
identity, permissions, model/SKU support, quota, and regional capacity. `status`
reads the recorded resource state. These commands do not prove model inference
or evaluation quality. `--config` here is the plan JSON, not a runtime `.env`.

Bootstrap generates a new `rg-foundry-eval-v11-<date>-<suffix>` group name in
`northcentralus`. A matching name alone is not ownership evidence. Existing
environments, configurations, and resource groups are not silently adopted or
overwritten. Do not run `apply` again simply because an old note said pending.

## Model roles

The current defaults are candidates that require a fresh availability check:

| Role | Model | Version | Deployment type | Requested ARM capacity |
|---|---|---|---|---:|
| Prepared sample agent | gpt-6-sol | 2026-09-22 | GlobalStandard | 20 |
| Foundry Evaluation Judge | gpt-6-luna | 2026-09-22 | GlobalStandard | 20 |
| Agent Optimizer / knowledge planner | gpt-5.5 | 2026-04-24 | GlobalStandard | 20 |
| Read-only knowledge embeddings | text-embedding-3-small | 1 | GlobalStandard | 10 |

The `gpt-6-sol` Agent was verified through an actual pinned Foundry prompt-agent
call with the read-only knowledge tool, followed by managed Evaluation.
The separate `gpt-6-luna` Judge was verified in the real managed evaluation.
Runtime support is role-specific; catalog visibility alone is not sufficient.

`gpt-6-luna` is not in the current official list of supported **optimization
models**, so that role remains `gpt-5.5`. See
[Agent Optimizer model roles](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models).

Both released instruction variants use the same Sol model and generation
settings. Changing the Agent model requires a new same-model baseline and
candidate comparison; old scores are not transferable. Keep the workshop's
released versions at v1/v2 and use explicitly pinned drafts for candidate
development. An existing released version is immutable and is not overwritten.

To choose other verified deployments, supply an explicit models JSON with
`plan --models-json <file>`. Each entry contains `name`, `version`, `sku`,
`capacity`, `deployment`, and `roles`. Exactly one mapping is required for each
of `agent`, `judge`, `planner`, `optimizer`, and `embedding`; planner and
optimizer may share a deployment. A model's availability does not establish
support for every role.

## Approval, ownership, and execution

The generated `approval.example.json` is **unapproved**. Operators must bind
actual user authorization to the exact plan/template/model hashes before
applying it. Repository documentation is not a customer's spending approval.

```bash
python3 -S -m lab.bootstrap preflight \
  --config "$LAB_BOOTSTRAP_CONFIG" \
  --approval "$LAB_COST_APPROVAL_FILE"
python3 -S -m lab.bootstrap apply \
  --config "$LAB_BOOTSTRAP_CONFIG" \
  --approval "$LAB_COST_APPROVAL_FILE"
python3 -S -m lab.bootstrap status \
  --config "$LAB_BOOTSTRAP_CONFIG" \
  --approval "$LAB_COST_APPROVAL_FILE"
```

**Command details:** Preflight checks the actual authorization and readiness.
`apply` creates the approved group, resources, model deployments, connections,
and minimum required resource-scoped RBAC. The final `status` checks the same
plan; it does not submit a second deployment.

GlobalStandard processing location is not an NCUS-only data-residency guarantee.
Quota is capacity, not free inference. ARM capacity units depend on the
model/SKU; never apply a universal TPM conversion. Budget alerts are not spending
cutoffs, and hosting/log costs can continue after a terminal closes.

The operator must verify the intended user, tenant, and subscription for CLI,
SDK, and portal separately. Do not infer an MCP principal from a subscription
list. No provider registration, shared permission expansion, cross-region
fallback, rollback, or resource deletion is automatic.

## Resume and retain accurate evidence

- Use the original `config.json`, ownership manifest, and deployment ID.
- A timeout does not mean a request was never accepted. Inspect remote state
  before retrying.
- `--retry` is only for a verified terminal owned failure and a separately
  authorized retry allowance. It cannot resubmit an unknown outcome.
- The `repair-dependencies` and `repair-trace-routing` commands preserve
  failure receipts and require their own validated scope; they are not silent
  edits to a previously approved plan.
- An `APPLIED` result confirms infrastructure, not model quality or production
  approval. Follow it with a real connectivity check and managed evaluation.
- `python -m lab cleanup` removes only recorded objects, not the resource group
  or continuing Search/model/log hosting. Follow participant
  [step 10](../guide/en/handbook.md#cleanup) for authorized dedicated-group
  deletion and an `az group exists` absence check. Preserve shared resources.

Private `.env`, `.lab/`, approvals, credentials, raw responses, and signed
download URLs must not enter the public site or distribution archive. The
published verification record contains only sanitized observations and hashes.
Set `LAB_ARTIFACTS_DIR` and `LAB_LANGUAGE` before starting Python; keep English and
Korean run records separate.
