# Isolated Foundry lab infrastructure

This directory contains the reproducible infrastructure contract used to prepare
an isolated lab environment. It is **operator preparation**, not an additional
participant exercise. The workshop itself is
**Foundry Evaluation → Agent Optimizer → same-criteria reevaluation**.

Use the [operator guide](../guide/en/admin-setup.md) or
[한국어 운영자 가이드](../guide/admin-setup.md) for the current prerequisites.
The template also provisions the read-only knowledge and monitoring connections
used by the prepared Contoso sample agent. Participants do not need to construct
that supporting infrastructure during the evaluation lab.

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
| Prepared sample agent | gpt-4.1-mini | 2025-04-14 | Standard | 20 |
| Foundry Evaluation Judge | gpt-6-luna | 2026-09-22 | GlobalStandard | 20 |
| Agent Optimizer / knowledge planner | gpt-5.5 | 2026-04-24 | GlobalStandard | 20 |
| Read-only knowledge embeddings | text-embedding-3-small | 1 | GlobalStandard | 10 |

The requested `gpt-6-luna` Judge was verified through a real managed Foundry
evaluation. Its direct Responses and prompt-agent probes returned HTTP 500 in
the tested environment, so an unverified agent version was not substituted for
the working baseline. This is an observed runtime limitation, not a universal
claim that the model lacks agent support.

`gpt-6-luna` is not in the current official list of supported **optimization
models**, so that role remains `gpt-5.5`. See
[Agent Optimizer model roles](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models).

The existing `gpt-4.1-mini` deployment works for this rehearsal, but its published
retirement is **2027-04-14**, and new subscriptions may face deprecation
restrictions. Do not promise that a fresh customer subscription can deploy it.
An operator must verify a working replacement before class, pin its version, and
start a new baseline if the agent model changes.

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
- The documented `repair-plan` and `repair-observability-plan` commands preserve
  failure receipts and require their own validated scope; they are not silent
  edits to a previously approved plan.
- An `APPLIED` result confirms infrastructure, not model quality or production
  approval. Follow it with a real connectivity check and managed evaluation.
- Delete only specifically authorized owned targets. Preserve shared models,
  the project, and other lab evidence unless their deletion is also requested.

Private `.env`, `.lab/`, approvals, credentials, raw responses, and signed
download URLs must not enter the public site or distribution archive. The
published verification record contains only sanitized observations and hashes.
Set `LAB_ARTIFACTS_DIR` and `LAB_LANGUAGE` before starting Python; keep English and
Korean run records separate.
