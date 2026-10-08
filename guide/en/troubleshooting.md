# Lab troubleshooting {#issue-guide}

[Ten lab steps](handbook.md#setup) · [Access, authorization, and setup reference](admin-setup.md#approval)

**Start with the blocked step and check the symptom, action and completion criteria.** Do not silently change data, evaluators or models, or submit the same operation under a new name to bypass an error.

Executable commands appear in **Run in your terminal** blocks. Use each step's **Action order** links to find the command or portal procedure. Code/portal tables and source under **Optional · how it works** are references, not another program to execute or edit to hide an error.

| Symptom | Where to look |
|---|---|
| HTML shows an explanation but the execution command is hard to find | Use the step's **Action order**; there is no need to open optional explanations. [Sign-in commands](handbook.md#setup-login) · [Runtime check](handbook.md#resources-runtime-check). |
| Terms, installation, sign-in or file paths are unclear | [Basic terms](handbook.md#basics) · [Codespaces](#codespaces) · [Environment and sign-in](#environment) |
| Authorization, permissions or model capacity blocks provisioning | [Provisioning](#provisioning) |
| Policy retrieval or Agent responses fail | [Policies and Agent](#knowledge) |
| Evaluation is unfinished or scores/reasons are missing | [Evaluation and results](#evaluation) |
| Optimize is unavailable or candidate selection is unclear | [Optimizer](#optimizer) |
| Deletion fails or resources must be retained | [Cleanup and retention](#cleanup) |

## How to use this guide {#start}

Keep timestamps, steps, commands, target IDs, error codes and actions in your private lab record. Preserve original responses and receipts rather than editing failures into successes. Do not append run-specific validation logs or results to reusable guides.

## Environment, sign-in and local files {#environment}

Resolve Python, Git, and Microsoft Azure CLI installation and PATH issues before signing in to Microsoft Azure.

| Symptom | Action | Completion criteria |
|---|---|---|
| `py`, `python3.13`, `git`, or `az` reports `command not found` or `not recognized` | Complete [OS-specific installation in 01](handbook.md#setup-local), close all terminals, and reopen them; restart VS Code too. If it still fails, check the approved installation paths and PATH. Inspect paths with `Get-Command py, git, az` on Windows or `command -v git az` on macOS/Linux. | [All three version checks](handbook.md#setup-verify) succeed in the same new terminal. |
| `winget` or `brew` is missing | On Windows, use the [official installer path](handbook.md#setup-windows). On macOS, complete [Homebrew installation and the PATH instructions under Next steps](handbook.md#setup-macos). | Prepare and verify the tools using one installation method without bypassing organizational restrictions. |
| Microsoft Store opens instead of Python, or `py` is missing | Check Launcher, pip, and PATH options in the regular Windows Python installer. Run `py -3.13 --version` in a new PowerShell window, substituting your installed version if different. | An installed Python 3.11–3.14 runs, not a Store shortcut. |
| Python is outside 3.11–3.14, or `.venv` uses a different Python | Select a supported version separately rather than replacing system Python. Create the lab environment with [the same verified command](handbook.md#setup-venv), such as `py -3.13` or `python3.13`. Check ownership and retention needs before replacing an existing `.venv`. | The environment's `python --version` is supported and `python -m pip --version` points inside that `.venv`. |
| Linux reports `No module named venv` or `ensurepip is not available` | Install `python3-venv` from the [Ubuntu setup instructions](handbook.md#setup-linux). For a version-specific Python, confirm its matching venv package and an approved installation path. | The selected Python creates `.venv` and its pip check succeeds. |
| Installation permissions, proxy, or certificate errors block installation | Check the official download URL, error, and permitted installation path. Obtain required installation/network authorization without disabling TLS checks, security tools, or organizational policies. | Installation uses an approved path and all three version checks succeed. |
| `.venv/bin/activate` or `Activate.ps1` is missing | Create the virtual environment in the repository and follow the [OS-specific setup order](handbook.md#setup-local). | `python -m pip --version` and `python -m lab --help` work in the same environment. |
| `ModuleNotFoundError` | Confirm the intended environment and run `python -m pip install -r requirements.lock` with its Python. | Required imports and dataset checks work in that environment. |
| PowerShell activation is blocked by policy | Use `.\.venv\Scripts\python.exe` without changing organizational policy. | Python runs without a policy change. |
| Previous settings are missing in a new terminal | Follow [terminal resumption](handbook.md#setup-resume) to restore the existing virtual environment, language, and record-folder variables. Do not repeat clone, plan, or apply. | Confirm the original identity and last completed step in `notes.md`, then continue with the same records. |
| Cannot find `agents/` or `knowledge/` execution records | Follow the [record-folder explanation](handbook.md#resources-notes) and look under your `LAB_ARTIFACTS_DIR`. `data/` and `scripts/` are under the repository folder instead. | Open your own language/environment's records, not an example path. |
| Portal and CLI accounts differ | These are separate sign-ins. Compare user, tenant and subscription with the portal using [01's sign-in/query commands](handbook.md#setup-login); complete personal authentication yourself. | All three approved values match. Do not substitute another identity or copy tokens to bypass authentication. |
| `AzureCliCredential` fails with both tenant and subscription | Use the repository authentication path: verify the tenant first, then specify the subscription on the credential. | Calls use the intended subscription without dropping tenant checks. |
| Artifacts go to the other language's folder | Set `LAB_LANGUAGE` and `LAB_ARTIFACTS_DIR` before starting Python with [01's language/record-folder commands](handbook.md#setup-language). | Dataset, configuration, workspace and results share the same language; existing records are not overwritten. |

## GitHub Codespaces {#codespaces}

| Symptom | Action and completion criteria |
|---|---|
| Create codespace is unavailable or usage is exhausted | Check account/organization policy and Codespaces spending limits. If unavailable, use the [local-computer path](handbook.md#setup-local-install), not a policy bypass. |
| Initial setup lacks `az`, `.venv`, or packages | Inspect the creation log for `.devcontainer/devcontainer.json` and dependency-installation failures. Do not provision until setup finishes. To apply the new configuration to an existing codespace, preserve private records first, then use **Codespaces: Rebuild Container** in the command palette. Do not delete `.lab`. |
| Device-code sign-in is blocked | Use an approved authentication/execution environment. On an authorized local computer, you can use `az login` with browser sign-in. Never send codes to someone else or change security policy to bypass the block. |
| Portal Browse cannot find `dev.jsonl` | Browse selects your computer's files. Choose the unchanged file [downloaded from Codespaces Explorer](handbook.md#dataset-download). |
| `candidate.txt` exists but the command cannot find it | Use the [candidate-saving steps](handbook.md#optimizer-candidate) to verify it is under `.lab` in **the same codespace as the lab terminal**, not only on your computer. |
| Private-network resources are unreachable | Do not assume Codespaces is connected to the required VNet/VPN. Use an approved network environment without disabling public-access restrictions or firewalls. |
| Unsure which codespace to resume or delete | Match the original repository/codespace and `notes.md`. Follow [backup, stop, and deletion](handbook.md#cleanup-codespaces); do not create another codespace and duplicate Microsoft Azure provisioning. |

## Provisioning, authorization and quota {#provisioning}

| Symptom | Action | Completion criteria |
|---|---|---|
| `setup` was canceled or stopped on invalid input | Before resource creation, rerun `bootstrap setup` with the same environment name to reuse its plan. Supply actual approved values, not invented amounts, durations, or empty evidence. | No Microsoft Azure changes occur before the final `CREATE ...` confirmation; prior creation records are inspected only. |
| `setup requires an interactive terminal` | Run it directly in VS Code **Terminal → New Terminal**. Pipes and automation use the [individual plan/approval path](handbook.md#resources-plan). | Noninteractive execution never becomes automatic authorization. |
| Existing `approval.json` expired or differs in scope | Preserve it and use the [approval worksheet](admin-setup.md#approval) to verify actual reauthorization and timestamps. Setup does not overwrite approvals or extend expiry. | Use only current authorization bound to the exact plan. |
| Plan reports `BLOCKED_AWAITING_APPROVAL` | Inspect `plan_status` and `mutations_performed`, then prepare the [actual authorization](admin-setup.md#approval). | Distinguish local planning from Microsoft Azure provisioning. |
| Approval fails despite `approved: true` | Check hashes, models, approver, validity, budget, acknowledgments and `approval_reason`. | Readiness is READY and authorization is READY_FOR_APPROVED_APPLY. |
| Provider is not Registered | Follow [provider registration](admin-setup.md#rbac), verify your registration permission/authorization, and register only the required providers. | Rerun the same preflight after all four providers are Registered. |
| Contributor cannot assign roles | Resource creation and role assignment are separate permissions. Obtain authorization for an execution scope in which you can perform this lab yourself. | Verify effective permissions and resume the same plan. Do not add subscription-wide Owner to bypass the issue. |
| Model, SKU, version, quota or capacity error | Inspect the planned role requirements and preflight reason. A replacement needs a separate plan and authorization. | Confirm support and capacity, then verify actual calls. |
| Runtime `*_tpm` is BLOCKED | Check the real allocation using the [TPM setup instructions](admin-setup.md#throughput). | All five TPM checks and overall preflight report PASS. |
| `unknown resource` after creation | Check whether this is verified default Smart Detection linked to your Application Insights, another workload, or changed receivers. Allow link propagation during creation. | Inspect the same `bootstrap status`; do not delete alerts or edit the manifest to bypass it. |
| Apply times out or its outcome is unknown | Preserve the original config, manifest and deployment ID; read [02's `bootstrap status` command](handbook.md#resources-status) and the group's Deployments. Do not repeat `apply`. | Wait for active work; do not resubmit an unknown outcome. |
| The local environment already exists | Resume the same lab with its original configuration. A different lab needs a new environment name and authorization. | Do not adopt or overwrite existing plans, settings or resources. |

Use `--retry` only for a verified terminal owned failure and a separate retry allowance. `repair-dependencies` and `repair-trace-routing` also require matching failure evidence and scoped authorization. `APPLIED` describes infrastructure, not answer quality, production approval or confirmed trace ingestion.

## Policy retrieval and Agent setup {#knowledge}

| Symptom | Action and completion criteria |
|---|---|
| Deployment exists but model calls fail | Catalog/deployment readiness and runtime support differ. Inspect the API error and intended role, then verify the [actual response in 03](handbook.md#agent). |
| Setup remains `created_not_retrieval_tested` | Only creation is complete. Use [03's `iq probe` command](handbook.md#agent-search-probe) to confirm `retrieval_verified` and actual references. |
| Direct retrieval succeeds but the Agent tool returns 403 | Check Search-read/model-call permissions and connection audience for the project's managed identity. User retrieval alone is insufficient. |
| `native-agent` reports a configuration mismatch | Inspect the receipt and remote version first. Equivalent MCP allowlist representations are normalized, but different tools, permissions, models or output settings remain blocked. Do not delete the receipt or create another version to bypass it. |
| Existing v2 has different instructions or model | Fixed-comparison protection is working. Compare the original owned environment, instructions and model snapshot; do not overwrite v2 or create v3. |
| Retrieval differs between languages | Check the selected language's source documents, index, analyzer and hashes. Renaming another language's index is not reuse. |
| Private-network or `PublicNetworkAccess=Disabled` failure | Use an approved VNet/VPN/execution environment and check DNS. Do not disable the firewall or private endpoint. |

## Microsoft Foundry evaluation and safe resumption {#evaluation}

### Add run item-schema error {#evaluation-add-run}

If the following message appears, inspect the existing evaluation's Agent-target data source:

**Example error message · do not run it.**
{: .output-label}

```text
Unable to create data source configuration from item schema
```

The [`scripts/add_foundry_eval_run.py` helper in 09](handbook.md#decision) copies a completed baseline's remote data source and changes only the explicit candidate version. Confirm the same evaluation ID, registered dataset, Judge, thresholds and mappings, plus the actual version/instructions for all twelve items. Do not substitute new data or a local Judge.

### IDs and duplicate submissions {#evaluation-resume}

| Symptom | Action |
|---|---|
| Evaluation ID or run ID is unknown | Use [06's complete `native-evals` command](handbook.md#baseline-identifiers). Evaluation uses `eval_...`; the baseline is a completed version-one `evalrun_...`. |
| Several evaluations have the same name | Compare creation time, Agent, dataset and runs; do not select by name alone. |
| Helper exits with Still running | If the receipt has a run ID, resume collection with the identical command and `--out`. |
| Receipt has no run ID, or a remote run with the same name exists | Preserve the original and check submission acceptance and the actual run. Do not delete receipts, rename or automatically resubmit. |
| Changing the version clears its checkbox | Reselect explicit v1 and confirm one checked target. |
| Dataset preview has five rows | Compare the twelve-row source, registered version and complete result count; the preview alone is insufficient. |
| Scores or reasons are not visible | Read the response under `conversation_id → User view`; reasons are in Detailed metrics result under `Relevance.reason` and `TaskAdherence.reason`. |
| A required response field is Unassigned | Use [mapping checks](admin-setup.md#evaluation-mapping) to compare the Agent target, query column, and service-generated response mapping. Do not add reference answers as a JSONL response column or submit before resolving the issue. |
| Output items or scores are missing | Preserve failures/missing items and keep the denominator at twelve. Do not invent zero scores or passes. |

## Agent Optimizer and interpretation {#optimizer}

| Symptom | Action and completion criteria |
|---|---|
| No custom evaluators available | Use **Custom only OFF** or **View built-in evaluators** rather than creating a custom evaluator to bypass a filter. |
| Optimize or the selected model is unavailable | Check New Foundry, prompt Agent, project permissions, Preview availability and [role-specific model support](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models). |
| The authorized wait ends while the job is active | Inspect the same job ID's state, errors, and usage in Optimization runs; record follow-up checks. Stopping your wait is not cancellation. Do not submit a replacement job. |
| The job is Failed/Canceled or results are partial | Preserve actual state, job ID, and errors. Do not claim a completed candidate or repeat the request under another name. |
| View changes exposes only a partial diff, not complete instructions | Expand revised sections and inspect candidate details or Download/Export where provided. Without the complete text, do not create v2; record “retain v1; complete instructions unavailable” and continue to 10. |
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
| Retention is explicitly authorized | Do not run deletion commands. Record the actual inventory, reason, cost responsibility, review date, and subsequent deletion plan; keep ownership/configuration needed to reopen the environment. |
| Search charges remain after cleanup | `cleanup` handles recorded objects, not all hosting/models/groups/logs. Follow [authorized cleanup or retention in 10](handbook.md#cleanup). |
| `.env` or workspace is missing | Compare the configuration, manifest and Microsoft Azure inventory first. Do not fabricate ownership records to delete resources. |
| Monitoring in the group serves another group | Review shared action-group dependencies with the owner. A dedicated group does not authorize deleting shared resources. |
| Locks, permissions or dependencies block deletion | Read Locks, Activity log, and the failed operation. Obtain authorization for the required action before resuming; do not remove organizational locks without authorization or mark blocked deletion complete. |
| The group remains after a deletion request | Inspect asynchronous progress, then run [10's absence check](handbook.md#cleanup-verify). Only a successful `az group exists` result of `false` verifies absence. |
| Costs appear after deletion | Check the usage period, billing delay and remaining resources in other groups. Earlier usage charges do not disappear. |

Service-specific soft-delete retention and permanent deletion/purge require separate policy and authorization. See the [resource-group deletion documentation](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group).
