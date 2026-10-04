# Lab troubleshooting {#issue-guide}

[Ten participant steps](handbook.md#setup) · [Operator authorization and handoff](admin-setup.md#approval)

**Start with the blocked step and check the symptom, action and completion criteria.** Do not silently change data, evaluators or models, or submit the same operation under a new name to bypass an error.

| Symptom | Where to look |
|---|---|
| Terms, installation, sign-in or file paths are unclear | [Basic terms](handbook.md#basics) · [Environment and sign-in](#environment) |
| Authorization, permissions or model capacity blocks provisioning | [Provisioning](#provisioning) |
| Policy retrieval or Agent responses fail | [Policies and Agent](#knowledge) |
| Evaluation is unfinished or scores/reasons are missing | [Evaluation and results](#evaluation) |
| Optimize is unavailable or candidate selection is unclear | [Optimizer](#optimizer) |
| Deletion fails or resources must be retained | [Cleanup and retention](#cleanup) |

## How to use this guide {#start}

Keep timestamps, steps, commands, target IDs, error codes and actions in your private lab record. Preserve original responses and receipts rather than editing failures into successes. Do not append run-specific validation logs or results to reusable guides.

## Environment, sign-in and local files {#environment}

Resolve Python, Git, and Azure CLI installation and PATH issues before signing in to Azure.

| Symptom | Action | Completion criteria |
|---|---|---|
| `py`, `python3.13`, `git`, or `az` reports `command not found` or `not recognized` | Complete [OS-specific installation in 01](handbook.md#setup-local), close all terminals, and reopen them; restart VS Code too. If it still fails, check installation paths and PATH with your administrator. Inspect paths with `Get-Command py, git, az` on Windows or `command -v git az` on macOS/Linux. | [All three version checks](handbook.md#setup-verify) succeed in the same new terminal. |
| `winget` or `brew` is missing | On Windows, use the [official installer path](handbook.md#setup-windows). On macOS, complete [Homebrew installation and the PATH instructions under Next steps](handbook.md#setup-macos). | Prepare and verify the tools using one installation method without bypassing organizational restrictions. |
| Microsoft Store opens instead of Python, or `py` is missing | Check Launcher, pip, and PATH options in the regular Windows Python installer. Run `py -3.13 --version` in a new PowerShell window, substituting your installed version if different. | An installed Python 3.11–3.14 runs, not a Store shortcut. |
| Python is outside 3.11–3.14, or `.venv` uses a different Python | Select a supported version separately rather than replacing system Python. Create the lab environment with [the same verified command](handbook.md#setup-venv), such as `py -3.13` or `python3.13`. Check ownership and retention needs before replacing an existing `.venv`. | The environment's `python --version` is supported and `python -m pip --version` points inside that `.venv`. |
| Linux reports `No module named venv` or `ensurepip is not available` | Install `python3-venv` from the [Ubuntu setup instructions](handbook.md#setup-linux). For a version-specific Python, confirm the matching venv package with your administrator. | The selected Python creates `.venv` and its pip check succeeds. |
| Administrator permissions, proxy, or certificate errors block installation | Send the official download URL and error to your administrator for approved installation/network configuration. Do not disable TLS checks, security tools, or organizational policies. | Installation uses an approved path and all three version checks succeed. |
| `.venv/bin/activate` or `Activate.ps1` is missing | Create the virtual environment in the repository and follow the [OS-specific setup order](handbook.md#setup-local). | `python -m pip --version` and `python -m lab --help` work in the same environment. |
| `ModuleNotFoundError` | Confirm the intended environment and run `python -m pip install -r requirements.lock` with its Python. | Required imports and dataset checks work in that environment. |
| PowerShell activation is blocked by policy | Use `.\.venv\Scripts\python.exe` without changing organizational policy. | Python runs without a policy change. |
| Portal and CLI accounts differ | These are separate sign-ins. Compare user, tenant and subscription from `az account show` with the portal; complete personal authentication yourself. | All three approved values match. Do not substitute another identity or copy tokens to bypass authentication. |
| `AzureCliCredential` fails with both tenant and subscription | Use the repository authentication path: verify the tenant first, then specify the subscription on the credential. | Calls use the intended subscription without dropping tenant checks. |
| Artifacts go to the other language's folder | Set `LAB_LANGUAGE` and `LAB_ARTIFACTS_DIR` before starting Python. | Dataset, configuration, workspace and results share the same language; existing records are not overwritten. |

## Provisioning, authorization and quota {#provisioning}

| Symptom | Action | Completion criteria |
|---|---|---|
| Plan reports `BLOCKED_AWAITING_APPROVAL` | Inspect `plan_status` and `mutations_performed`, then prepare the [actual authorization](admin-setup.md#approval). | Distinguish local planning from Azure provisioning. |
| Approval fails despite `approved: true` | Check hashes, models, approver, validity, budget, acknowledgments and `approval_reason`. | Readiness is READY and authorization is READY_FOR_APPROVED_APPLY. |
| Provider is not Registered | The subscription administrator registers it through organizational procedures. | Rerun the same preflight after all four providers are registered. |
| Contributor cannot assign roles | Resource creation and role assignment are separate permissions. Use the authorized provisioning owner. | Verify effective permissions; do not add subscription Owner to bypass the issue. |
| Model, SKU, version, quota or capacity error | Inspect the planned role requirements and preflight reason. A replacement needs a separate plan and authorization. | Confirm support and capacity, then verify actual calls. |
| Runtime `*_tpm` is BLOCKED | Check the real allocation using the [TPM setup instructions](admin-setup.md#throughput). | All five TPM checks and overall preflight report PASS. |
| `unknown resource` after creation | Check whether this is verified default Smart Detection linked to your Application Insights, another workload, or changed receivers. Allow link propagation during creation. | Inspect the same `bootstrap status`; do not delete alerts or edit the manifest to bypass it. |
| Apply times out or its outcome is unknown | Preserve the original config, manifest and deployment ID; read `bootstrap status` and the group's Deployments. | Wait for active work; do not resubmit an unknown outcome. |
| The local environment already exists | Resume the same lab with its original configuration. A different lab needs a new environment name and authorization. | Do not adopt or overwrite existing plans, settings or resources. |

Use `--retry` only for a verified terminal owned failure and a separate retry allowance. `repair-dependencies` and `repair-trace-routing` also require matching failure evidence and scoped authorization. `APPLIED` describes infrastructure, not answer quality, production approval or confirmed trace ingestion.

## Policy retrieval and Agent setup {#knowledge}

| Symptom | Action and completion criteria |
|---|---|
| Deployment exists but model calls fail | Catalog/deployment readiness and runtime support differ. Inspect the API error and intended role, then verify the [actual response in 03](handbook.md#agent). |
| Setup remains `created_not_retrieval_tested` | Only creation is complete. Confirm `retrieval_verified` and actual references from `iq probe`. |
| Direct retrieval succeeds but the Agent tool returns 403 | Check Search-read/model-call permissions and connection audience for the project's managed identity. User retrieval alone is insufficient. |
| `native-agent` reports a configuration mismatch | Inspect the receipt and remote version first. Equivalent MCP allowlist representations are normalized, but different tools, permissions, models or output settings remain blocked. Do not delete the receipt or create another version to bypass it. |
| Existing v2 has different instructions or model | Fixed-comparison protection is working. Compare the original owned environment, instructions and model snapshot; do not overwrite v2 or create v3. |
| Retrieval differs between languages | Check the selected language's source documents, index, analyzer and hashes. Renaming another language's index is not reuse. |
| Private-network or `PublicNetworkAccess=Disabled` failure | Use an approved VNet/VPN/execution environment and check DNS. Do not disable the firewall or private endpoint. |

## Foundry evaluation and safe resumption {#evaluation}

### Add run item-schema error {#evaluation-add-run}

If the following message appears, inspect the existing evaluation's Agent-target data source:

```text
Unable to create data source configuration from item schema
```

The [`scripts/add_foundry_eval_run.py` helper in 09](handbook.md#decision) copies a completed baseline's remote data source and changes only the explicit candidate version. Confirm the same evaluation ID, registered dataset, Judge, thresholds and mappings, plus the actual version/instructions for all twelve items. Do not substitute new data or a local Judge.

### IDs and duplicate submissions {#evaluation-resume}

| Symptom | Action |
|---|---|
| Evaluation ID or run ID is unknown | Read `native-evals --name`. Evaluation uses `eval_...`; the baseline is a completed version-one `evalrun_...`. |
| Several evaluations have the same name | Compare creation time, Agent, dataset and runs; do not select by name alone. |
| Helper exits with Still running | If the receipt has a run ID, resume collection with the identical command and `--out`. |
| Receipt has no run ID, or a remote run with the same name exists | Preserve the original and check submission acceptance and the actual run. Do not delete receipts, rename or automatically resubmit. |
| Changing the version clears its checkbox | Reselect explicit v1 and confirm one checked target. |
| Dataset preview has five rows | Compare the twelve-row source, registered version and complete result count; the preview alone is insufficient. |
| Scores or reasons are not visible | Read the response under `conversation_id → User view`; reasons are in Detailed metrics result under `Relevance.reason` and `TaskAdherence.reason`. |
| Output items or scores are missing | Preserve failures/missing items and keep the denominator at twelve. Do not invent zero scores or passes. |

## Agent Optimizer and interpretation {#optimizer}

| Symptom | Action and completion criteria |
|---|---|
| No custom evaluators available | Use **Custom only OFF** or **View built-in evaluators** rather than creating a custom evaluator to bypass a filter. |
| Optimize or the selected model is unavailable | Check New Foundry, prompt Agent, project permissions, Preview availability and [role-specific model support](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models). |
| A candidate changes model or tool descriptions | Select **Instruction only** and disable model comparison. Non-instruction changes are not a same-condition comparison. |
| Candidate embeds policy dates, numbers or evaluation answers | Preserve the original service output and remove embedded answers or reject the candidate. Record manual changes, reasons and provenance, then reevaluate separately. |
| Only the baseline is selected, with no different candidate | Record why v1 is retained and continue to 10. Do not invent v2 or repeat the job to manufacture improvement. |
| Internal ranking differs from reevaluation | Internal 0–1 ranking and separate evaluation scores/pass rates differ. Inspect actual answers, policy errors and regression too. |
| TaskAdherence is 1 | That is a binary pass, not a one-out-of-five Relevance score. |
| Statistics are Inconclusive | A difference was not established; this is not evidence of significance or equivalence. |
| Quality improves but latency/tokens increase | Record the tradeoff too. Unknown billing is not zero cost. |

## Cleanup, retention and continuing costs {#cleanup}

| Symptom | Action and completion criteria |
|---|---|
| Retention is explicitly authorized | Do not run deletion commands. Record the inventory, cost owner and review date; keep ownership/configuration needed to reopen the environment. |
| Search charges remain after cleanup | `cleanup` handles recorded objects, not all hosting/models/groups/logs. Follow [authorized cleanup or retention in 10](handbook.md#cleanup). |
| `.env` or workspace is missing | Compare the configuration, manifest and Azure inventory first. Do not fabricate ownership records to delete resources. |
| Monitoring in the group serves another group | Review shared action-group dependencies with the owner. A dedicated group does not authorize deleting shared resources. |
| Locks, permissions or dependencies block deletion | Read Locks, Activity log and the failed operation; request action from the owner. Do not remove organizational locks without authorization. |
| The group remains after a deletion request | Inspect asynchronous progress. Only a successful `az group exists` result of `false` verifies absence. |
| Costs appear after deletion | Check the usage period, billing delay and remaining resources in other groups. Earlier usage charges do not disappear. |

Service-specific soft-delete retention and permanent deletion/purge require separate policy and authorization. See the [resource-group deletion documentation](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group).
