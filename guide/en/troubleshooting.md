# Lab troubleshooting {#issue-guide}

[Ten lab steps](handbook.md#setup) · [Access, authorization, and setup reference](admin-setup.md#approval)

**Start with the blocked step and check the symptom, action and completion criteria.** Do not silently change data, evaluators or models, or submit the same operation under a new name to bypass an error.

Executable commands appear in **Run in your terminal** blocks. Use each step's **Action order** links to find the command or portal procedure. Code/portal tables and source under **Optional · how it works** are references, not another program to execute or edit to hide an error.

| Symptom | Where to look |
|---|---|
| HTML shows an explanation but the execution command is hard to find | Use the step's **Action order**; there is no need to open optional explanations. [Sign-in commands](handbook.md#setup-login) · [Runtime check](handbook.md#resources-runtime-check). |
| Terms, installation, sign-in or file paths are unclear | [Basic terms](handbook.md#basics) · [Codespaces](#codespaces) · [Environment and sign-in](#environment) |
| Authorization, permissions, account type, providers or model quota block provisioning | [Provisioning](#provisioning) |
| The first provisioning failed and `setup`/`apply` will not submit again | [First provisioning failure recovery](#provisioning-retry) |
| Policy retrieval or Agent responses fail | [Policies and Agent](#knowledge) |
| After one failed `smoke`, `iq`, or `native-agent` call in 03, the same command is refused | [Recovery after a first call failure](#knowledge-first-failure) |
| Evaluation is unfinished or scores/reasons are missing | [Evaluation and results](#evaluation) |
| Optimize is unavailable or candidate selection is unclear | [Optimizer](#optimizer) |
| Deletion fails or resources must be retained | [Cleanup and retention](#cleanup) |

## How to use this guide {#start}

Keep timestamps, steps, commands, target IDs, error codes and actions in your own notes. Preserve original responses and receipts rather than editing failures into successes. Do not append run-specific validation logs or results to reusable guides.

## Environment, sign-in and local files {#environment}

Resolve Python, Git, and Azure CLI installation and PATH issues before signing in to Microsoft Azure.

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
| Previous settings are missing in a new terminal | Follow [resumption](handbook.md#setup-resume), activate the existing virtual environment, and keep the original `--config` path. Do not repeat language/record variables, clone, plan, or apply. | Confirm the original identity with `az account show` and the last completed step with the read-only resume checks, then continue with the same records. |
| Cannot find `agents/` or `knowledge/` execution records | Follow the [record-folder explanation](handbook.md#resources-notes) and look under that environment's `artifacts/`. `data/` and `scripts/` are under the repository folder instead. | Open your own language/environment's records, not an example path. |
| Portal and CLI accounts differ | These are separate sign-ins. Compare user, tenant and subscription with the portal using [01's sign-in/query commands](handbook.md#setup-login); complete personal authentication yourself. | All three approved values match. Do not substitute another identity or copy tokens to bypass authentication. |
| `AzureCliCredential` fails with both tenant and subscription | Use the repository authentication path: verify the tenant first, then specify the subscription on the credential. | Calls use the intended subscription without dropping tenant checks. |
| Another language or environment's records are selected | Check that `--config` points to your original `.lab/lab-en/.env`. [Language and record location come from that configuration](handbook.md#setup-language), not a shell-variable change. | Dataset, configuration, workspace, and results belong to the same environment; existing records are not overwritten. |
| Earlier records are under the repository's shared `artifacts/` | Preserve them and verify the original configuration, language, and ownership. Do not automatically move or replace them; see the [configuration reference](admin-setup.md#runtime-settings). | Do not resubmit paid work before locating its original records. |

## GitHub Codespaces {#codespaces}

| Symptom | Action and completion criteria |
|---|---|
| Create codespace is unavailable or usage is exhausted | Check account/organization policy and Codespaces spending limits. If unavailable, use the [local-computer path](handbook.md#setup-local-install), not a policy bypass. |
| Initial setup lacks `az`, `.venv`, or packages | Inspect the creation log for `.devcontainer/devcontainer.json` and dependency-installation failures. Do not provision until setup finishes. To apply the new configuration to an existing codespace, preserve private records first, then use **Codespaces: Rebuild Container** in the command palette. Do not delete `.lab`. |
| Device-code sign-in is blocked | Use an approved authentication/execution environment. On an authorized local computer, you can use `az login` with browser sign-in. Never send codes to someone else or change security policy to bypass the block. |
| Portal Browse cannot find `dev.jsonl` | Browse selects your computer's files. Choose the unchanged file [downloaded from Codespaces Explorer](handbook.md#dataset-download). |
| `candidate.txt` exists but the command cannot find it | Use the [candidate-saving steps](handbook.md#optimizer-candidate) to verify it is under `.lab` in **the same codespace as the lab terminal**, not only on your computer. |
| Private-network resources are unreachable | Do not assume Codespaces is connected to the required VNet/VPN. Use an approved network environment without disabling public-access restrictions or firewalls. |
| The codespace stopped or disconnected while a command was running | Restart it from [your Codespaces](https://github.com/codespaces), open **Terminal → New Terminal**, and follow [resumption](handbook.md#setup-resume). Inspect state before acting: [`bootstrap status`](handbook.md#resources-status) for provisioning, [`native-evals`](handbook.md#baseline-identifiers) for evaluations, and the [09 resume rules](handbook.md#decision-run) for a reevaluation. Do not repeat `apply` or submit under a new name. A stopped codespace left unused is deleted after 30 days by default; keep a [backup of `.lab/`](handbook.md#cleanup-codespaces). |
| Unsure which codespace to resume or delete | Match the original repository/codespace and its `.lab/<environment>/` folder. Follow [backup, stop, and deletion](handbook.md#cleanup-codespaces); do not create another codespace and duplicate Microsoft Azure provisioning. |

## Provisioning, authorization and quota {#provisioning}

| Symptom | Action | Completion criteria |
|---|---|---|
| Blocked with `The signed-in principal is not independently verified` | The CLI sign-in name differs from the Microsoft Entra ID user name. Personal Microsoft accounts (Gmail, Outlook, and similar) and guest invitations are affected. [Check with two commands](handbook.md#setup-account-type) and sign in again with a work or school (member) account. Do not change inputs to bypass it. If you already ran `setup`, start again with a new environment name (`lab-en-02`). | The two commands print the same value and `bootstrap setup` passes the identity check. |
| `Bootstrap blocked: … user principal name is required.` at the very start | The CLI sign-in name (`az account show --query user.name`) contains a character that is not allowed, such as the `#` in `#EXT#` or an apostrophe. `bootstrap` accepts only a `name@domain` made of letters, digits, and `. _ + -`, and no environment folder is created in that case. Do not change inputs; follow the [member account check](handbook.md#setup-account-type) and sign in with another member account. | The sign-in name has the allowed form and `bootstrap setup` proceeds through the identity check. |
| Blocked with `Active Azure CLI subscription/tenant/user differs` | The signed-in account, subscription, or tenant changed after the plan was made. Sign in again with the original account and subscription. If you meant to change them, start again with a new environment name; there is no automatic switch and no editing of `config.json`. | The user, tenant, and subscription in `az account show` match the plan. |
| `setup` was canceled or stopped on invalid input | Before resource creation, rerun `bootstrap setup` with the same environment name to reuse its plan. Supply actual approved values, not invented amounts, durations, or empty evidence. | No Microsoft Azure changes occur before the final `CREATE ...` confirmation; prior creation records are inspected only. |
| `setup requires an interactive terminal` | Run it directly in VS Code **Terminal → New Terminal**. Pipes and automation use the [individual plan/approval path](handbook.md#resources-plan). | Noninteractive execution never becomes automatic authorization. |
| Existing `approval.json` expired or differs in scope | Preserve it and use the [approval worksheet](admin-setup.md#approval) to verify actual reauthorization and timestamps. Setup does not overwrite approvals or extend expiry. | Use only current authorization bound to the exact plan. |
| Plan reports `BLOCKED_AWAITING_APPROVAL` | Inspect `plan_status` and `mutations_performed`, then prepare the [actual authorization](admin-setup.md#approval). | Distinguish local planning from Microsoft Azure provisioning. |
| Approval fails despite `approved: true` | Check hashes, models, approver, validity, budget, acknowledgments and `approval_reason`. | Readiness is READY and authorization is READY_FOR_APPROVED_APPLY. |
| Provider is not Registered (`is not registered; bootstrap never registers providers`) | Read the state of the four providers with the [provider check and registration commands](handbook.md#resources-prereq-providers) and register only those that are `NotRegistered` with `az provider register --namespace ... --wait`. If you lack registration permission, verify your registration permission/authorization in [provider registration](admin-setup.md#rbac). | Rerun the same `bootstrap setup` after all four providers are Registered. |
| Contributor cannot assign roles | Resource creation and role assignment are separate permissions. Obtain authorization for an execution scope in which you can perform this lab yourself. | Verify effective permissions and resume the same plan. Do not add subscription-wide Owner to bypass the issue. |
| Model, SKU, version, quota or capacity error (`Insufficient unallocated quota`, `Free quota cannot be verified`, `Insufficient regional model capacity`) | Inspect the planned role requirements and preflight reason. If quota is missing or short, resolve it in this order using the [quota pre-check](handbook.md#resources-prereq-quota): check the tier and remaining quota, upgrade a free-trial subscription, and request quota. This lab supports only `northcentralus`, so the region cannot change, and replacing a pinned model needs a separate plan and authorization and changes the comparison conditions. Do not bypass the block. | Each of the four models has `limit − used` at or above its requested capacity, and the readiness check of the same `bootstrap setup` becomes READY. |
| Runtime `*_tpm` is BLOCKED | Check the real allocation using the [TPM setup instructions](admin-setup.md#throughput). | All five TPM checks and overall preflight report PASS. |
| `unknown resource` after creation | Check whether this is verified default Smart Detection linked to your Application Insights, another workload, or changed receivers. Allow link propagation during creation. | Inspect the same `bootstrap status`; do not delete alerts or edit the manifest to bypass it. |
| Apply times out or its outcome is unknown | Preserve the original config, manifest and deployment ID; read [02's `bootstrap status` command](handbook.md#resources-status) and the group's Deployments. Do not repeat `apply`. | Wait for active work; do not resubmit an unknown outcome. |
| The local environment already exists | Resume the same lab with its original configuration. A different lab needs a new environment name and authorization. | Do not adopt or overwrite existing plans, settings or resources. |

Use `--retry` only for a verified terminal owned failure and a separate retry allowance. `repair-dependencies` and `repair-trace-routing` also require matching failure evidence and scoped authorization. `APPLIED` describes infrastructure, not answer quality, production approval or confirmed trace ingestion.

### First provisioning failure recovery {#provisioning-retry}

**Symptom:** `bootstrap setup` ended with an error such as `DeploymentFailed`. In `bootstrap status`, `resources.arm_deployment.provisioning_state` is `Failed`, or the group's **Deployments** in the portal lists a `Failed` deployment.

**Why can't I just run it again?** Provisioning is designed to be submitted only once. Running `setup` again only inspects status, and `bootstrap apply` is refused with `RETRY_REQUIRED`. The approval written by the quick path has no retry allowance (`max_provisioning_retries`), so even `--retry` is refused with `RETRY_BUDGET_EXHAUSTED`. This is a safeguard, not a broken environment, and you do not submit the same deployment again under another name.

**Retry once with the same plan.**

**1. Read the cause.** In the portal, open the resource group → **Deployments** → the failed deployment and read its error details together with the `bootstrap status` output. Quota or capacity shortage, an unregistered provider, and transient service errors are common. If a [pre-check](handbook.md#resources-prereq) can fix the cause, fix it first.

**2. Decide whether to try once more.** Only if you can authorize the cost and time of one more attempt, open `.lab/lab-en/approval.json` in your editor and add `"max_provisioning_retries": 1`. The approval's start and expiry times must still be valid; if they have expired, reauthorize with the [approval worksheet](admin-setup.md#approval). Do not change any other field or edit `config.json` or `manifest.json`.

**3. Run it with the retry stated explicitly.** Do not run the same command in another window at the same time.

```sh
python -m lab bootstrap apply --config .lab/lab-en/config.json --approval .lab/lab-en/approval.json --retry
```

**4. Check the result.** When `status: APPLIED` appears, continue with the [portal and runtime checks](handbook.md#resources-runtime-check) in 02. If it fails again, the allowed attempts are used up, so start again in a new environment as described below.

**If you cannot retry, start again in a new environment.** Do not revive the same environment when the failure cannot be confirmed (`UNKNOWN_SUBMISSION`, where a submission was made but no deployment is visible, or `UNRESOLVED_DEPLOYMENT_STATE`) or when it fails again after the retry.

1. Some resources may exist and Search is billed hourly, so first clean up the group named `names.resource_group` in `config.json` with the [group deletion procedure in 10](handbook.md#cleanup-delete). Deletion is separate from the creation authorization, so go through every confirmation in that procedure.
2. Run [`bootstrap setup`](handbook.md#resources-quickstart) again with a new environment name (for example `lab-en-02`), and change the `.lab/lab-en` path in later commands to `.lab/lab-en-02`.

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

### Recovery after a first call failure {#knowledge-first-failure}

**Symptom:** After one failed `smoke`, `iq prepare`, `iq probe`, or `native-agent` call in 03, the same command is **refused immediately** with a message such as `failed or its outcome is unknown` or `outcome is unknown`.

**Why does this happen?** These commands save a receipt before each call and never retry automatically. This protects against submitting a request whose outcome is unknown twice; it does not mean the environment is broken. The most common first failure is a 401 or 403 right after 02, before the roles take effect. Read the printed error first and fix the cause. Roles can take up to about 10 minutes, so wait 5–10 minutes and also check the deployment names and quota. **Preserve the original records instead of deleting them.** The steps below assume the request was clearly rejected.

| Command | Record that blocks the same command (under `.lab/lab-en/artifacts/`) | Recovery |
|---|---|---|
| `smoke` | `runs/model-smoke/model-smoke.json` | Run it with a **new `--run-id`**. |
| `iq probe` | `knowledge/probes/<question hash>/iq-request.json` | Run it with **a differently worded `--query`**. |
| `iq prepare` | `knowledge/document-embeddings.json` or `knowledge/upload-response.json` | Rename **only the one record** the refusal names to keep it, then rerun the same command. |
| `native-agent` | `agents/native-v1.json` | Check whether v1 exists remotely, then decide. |

**`smoke`:** Run it with a new run-id. If it fails again, raise the number, as in `model-smoke-3`. The first record stays, and later steps do not depend on the run-id.

```sh
python -m lab --config .lab/lab-en/.env smoke --run-id model-smoke-2 --confirm
```

**`iq probe`:** A different question text is handled as a new request. Confirm `status: retrieval_verified` with nonempty references. Do not repeat the retrieval preparation (`iq prepare`).

```sh
python -m lab --config .lab/lab-en/.env iq probe --confirm --query "Tell me about the Contoso Atlas Cloud refund policy."
```

**`iq prepare`:** If the refusal says `This embedding request failed or its outcome is unknown`, the cause is `knowledge/document-embeddings.json`; if it says `The upload contract changed or its outcome is unknown`, it is `knowledge/upload-response.json`. If the error printed in the terminal was a rejection such as 401, 403, 404, or 429 (for embeddings it is also in the record's `error.type`), fix the cause, rename **only that one record** to keep it, and rerun the same command. Even when you cannot tell whether the service received the request, embedding the 8 documents costs little and the upload uses `mergeOrUpload`, so it creates no duplicate documents. Indexes, sources, and knowledge bases you already created are confirmed through the ownership record and reused, not overwritten.

```sh
python -c "import pathlib,sys,time; p=pathlib.Path(sys.argv[1]); p.rename(p.with_name(p.name+'.failed-'+time.strftime('%Y%m%d-%H%M%S')))" ".lab/lab-en/artifacts/knowledge/document-embeddings.json"
python -m lab --config .lab/lab-en/.env iq prepare --confirm
```

Change the path in the first command to match the rejected record. Renaming the file in your editor is equivalent; never delete it or edit its contents.

**`native-agent`:** The refusal is `The creation outcome is unknown; inspect the receipt and remote state, do not resubmit.`, because `agents/native-v1.json` was saved with `"status": "creating"` before the call.

1. In Microsoft Foundry, open **Build → Agents** and check whether `lab-en-iq` has **Version 1**.
2. **If v1 exists,** it was created but the response was lost. Running the same `native-agent --version 1 --confirm` again compares the remote v1 with the configuration and completes without creating a new version. Do not move the record.
3. **If v1 does not exist,** the request was rejected and nothing was created. Rename the record to keep it, then rerun the same command.

```sh
python -c "import pathlib,sys,time; p=pathlib.Path(sys.argv[1]); p.rename(p.with_name(p.name+'.failed-'+time.strftime('%Y%m%d-%H%M%S')))" ".lab/lab-en/artifacts/agents/native-v1.json"
python -m lab --config .lab/lab-en/.env native-agent --version 1 --confirm
```

The v2 in 09 works the same way with `agents/native-v2.json` and `--version 2 --prompt .lab/lab-en/candidate.txt`. If the records disagree (for example, the portal shows it but no local record exists) or you cannot resolve the cause, do not bypass the check by renaming; [start again in a new environment](#provisioning-retry).

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
| Helper exits with Still running | If the receipt has a run ID, resume collection with the identical command. |
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
