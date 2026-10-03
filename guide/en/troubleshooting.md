# Execution issues and resolutions {#issue-guide}

[Guide from the beginning](handbook.md#setup) · [Operator authorization and handoff](admin-setup.md#approval) · [Actual quality measurements](verification.md)

**Start with the blocked step, then follow symptom, cause, resolution, and verification.** Historical Azure measurements, this revision's read-only observations, and local checks are distinct. Documenting a resolution does not establish that a new cloud execution succeeded.

## Scope and how to use this record {#start}

| Evidence category | Source and limitation |
|---|---|
| Earlier service execution | The rehearsal recorded by the existing guides, portal captures, and `evidence/latest.json`, as of 2026-10-01. Published quality measurements use English data. |
| Read-only observations on 2026-10-03 | The existing lab's CLI user, tenant, and subscription matched. `native-evals` retrieved v1, v2, and a draft run from that same evaluation. |
| Documentation/code changes on 2026-10-03 | Added first-time setup, native Agent creation commands, ID lookup, cleanup boundaries, and formal Korean prose. The [final section](#verification) describes verification scope. |
| Not performed in this revision | New Azure resource creation, role changes, data uploads, paid evaluations, Optimizer reruns, and actual cloud deletion. Existing measurements are not relabeled as a new Korean run. |

For a new issue, record **time, step, command, error code, target ID, change, and recheck result** in private `notes.md`. Before publication, remove subscription/account identifiers, tokens, cookies, and signed URLs. Preserve failed responses and unfavorable evaluation outcomes.

## Environment, login, and local files {#environment}

| Symptom | Cause and resolution | Ready-to-continue check |
|---|---|---|
| The guide starts with an already-prepared project and Agent | The earlier participant guide had only six evaluation steps; operator setup assumed existing infrastructure. New [01–03](handbook.md#setup) connect account, installation, provisioning, retrieval, and Agent preparation. | Confirm your own project, Agent, and actual tool response; passing link checks is not environment readiness. |
| `.venv/bin/activate` or `Activate.ps1` is missing | Create the virtual environment from the repository folder first. Windows and macOS/Linux activation paths differ. Follow the [installation sequence](handbook.md#setup-local). | The venv's `python -m pip --version` and `python -m lab --help` succeed. |
| `ModuleNotFoundError` | Wrong interpreter or missing locked dependencies. Run `python -m pip install -r requirements.lock` using the venv Python. | Run dataset checks and the intended command with that same Python. |
| PowerShell policy blocks activation | Use `.\.venv\Scripts\python.exe` without changing organizational policy. | The interpreter runs without a policy change. |
| Portal access works but CLI shows a different account | Browser and CLI authentication are separate. Compare directory/subscription filters and the user, tenant, and subscription from `az account show`. | All three approved values match; no ambient identity fallback. |
| `AzureCliCredential` fails when given both tenant and subscription | The corresponding Azure CLI argument combination is incompatible. `lab/auth.py` first validates the tenant, then supplies only the subscription to the credential. | The same verified identity/subscription is used; tenant validation remains intact. |
| Korean runs use English artifacts, or vice versa | Set `LAB_LANGUAGE` and `LAB_ARTIFACTS_DIR` before Python starts. Reading `.env` cannot change an artifacts path already selected at import time. | Language-specific folder and workspace metadata agree; original artifacts remain untouched. |

The first two gaps were confirmed by reviewing the previous guide sources. Authentication argument and language constraints are verified implementation/regression-test facts, not newly induced authentication failures or paid calls.

## Provisioning, authorization, and quota {#provisioning}

| Symptom | Action | Verification |
|---|---|---|
| Plan returns `BLOCKED_AWAITING_APPROVAL` | The local plan exists, but spending is not approved. Distinguish `plan_status` from `mutations_performed`. | Confirm `CREATED_LOCAL_ONLY` and `false`, then complete the [approval worksheet](admin-setup.md#approval). |
| Approval fails despite `approved: true` | Possible hash/model mismatch, wrong approver, invalid timezone/date interval, or missing budget/consent. Read `approval_reason`; correct only genuinely authorized fields. | Both readiness READY and approval READY_FOR_APPROVED_APPLY are present. |
| A provider is not Registered | An authorized subscription administrator registers it through organizational procedures. Bootstrap does not register it automatically. | All four providers are registered; rerun the same preflight. |
| Contributor access fails on role assignments | Resource creation and role-assignment authority are separate. Use an already-authorized provisioning operator. | Effective required access is confirmed; do not grant new subscription-wide Owner as a workaround. |
| Model/SKU/version/region capacity or quota is blocked | Compare the role-specific plan with preflight `reason`. If substitution is needed, verify support for each role and obtain a new plan/authorization. | Verify catalog, quota, capacity, and then actual Agent/tool execution. |
| Apply times out or has an unknown result | Preserve config, manifest, and deployment ID. Inspect `bootstrap status` and the group's **Deployments** in Azure Portal. | Wait if active; do not create another environment or resubmit while the outcome remains unresolved. |
| Environment already exists | This protects an existing plan from overwrite. Use its original config with status. | Resume that lab; only a separate authorized lab receives a new scope. |
| Old recovery command names do not exist | Actual CLI names are `repair-dependencies` and `repair-trace-routing`. The outdated infrastructure documentation names were corrected. | Check `python -m lab.bootstrap --help`. These are not general retries; matching failure evidence and separate authorization are required. |

`--retry` applies only to a verified **terminal failure** of the owned deployment, within an explicit retry allowance. It is not permission to repeat an unknown POST. `APPLIED` establishes infrastructure creation, not model quality, production approval, or successful trace ingestion.

## Policy retrieval and Agent setup {#knowledge}

| Symptom | Action | Verification |
|---|---|---|
| A model appears in the catalog but the Agent fails | Deployment success and Agent runtime support differ. Record the real API error, model/version, and tool path. | Complete the [smoke and actual Agent call in 03](handbook.md#agent). |
| Setup remains `created_not_retrieval_tested` | Only creation is complete. Run `iq probe` and inspect response, references, and activity. | `retrieval_verified` with actual sources. |
| Direct retrieval succeeds but Agent tool returns 403 | Direct retrieval uses the CLI user; the Agent connection uses the project managed identity. Check Search/model permissions and the connection audience for that identity. | A successful `knowledge_base_retrieve` response inside an Agent execution. |
| English/Korean search behaves inconsistently | `lab/knowledge.py` uses the selected `en.microsoft` or `ko.microsoft` analyzer. Preserve the original language, index, and document hash. | Distinguish language regression checks from live retrieval; renaming an existing index does not isolate it. |
| Agent setup is described only by a function name, with no executable entry point | This revision connects `native-agent --version 1/2` to existing `ensure_fixed_release`, including policy MCP, strict JSON, ownership, and model snapshots. | Local regression checks cover the command; a fresh environment still requires actual creation and tool-response verification. |
| Existing v2 has different instructions or the model changed | The fixed-comparison guard stops the operation. Preserve records instead of overwriting v2 or creating v3. | Compare owned Agent, model, tools, output settings, and intended instructions. |
| `PublicNetworkAccess=Disabled` or private-network timeout | Use the approved VNet, VPN, or organizational execution environment. Do not disable firewalls/private endpoints. | Have the network owner verify DNS/connectivity, then recheck the same endpoint. |

## Foundry evaluation and safe resumption {#evaluation}

### The portal Add run action returned an item-schema error {#evaluation-add-run}

**Previously observed message:**

```text
Unable to create data source configuration from item schema
```

In that session, portal Add run could not reconstruct the existing Agent-targeted data source. This is not evidence of a service-wide outage or identical behavior in every subscription.

**Resolution:** Use [`scripts/add_foundry_eval_run.py` in 09](handbook.md#decision) to copy the completed baseline's remote data source and change only the explicit candidate version. It submits a real run under the same managed evaluation definition. A local Judge, changed JSONL, or different criteria is not a substitute.

**Verification:** Confirm evaluation ID, original dataset registration, Relevance 4, TaskAdherence 1, Judge/mappings, and actual version/instructions for all 12 output items. Existing completed v1/v2 runs were also confirmed in this revision's read-only lookup. No new paid run was submitted to reproduce the portal error.

### Prevent wrong IDs and duplicate submissions {#evaluation-resume}

| Symptom | Resolution |
|---|---|
| Evaluation/run IDs are difficult to find | Use `native-evals --name`. Select the `eval_...` evaluation and completed version-1 `evalrun_...` baseline. |
| Several evaluations share a name | Compare portal time, Agent, dataset, and runs. Do not choose by name alone. |
| Helper exits with Still running | If the receipt has a run ID, repeat the same command and output path to collect that run. |
| Receipt exists without a run ID | Acceptance is unknown. Preserve it and inspect the portal/service. Do not delete the receipt, rename the run, or automatically resubmit. |
| A remote run already uses that name | Open it or restore its original receipt instead of forcing a duplicate through a new name. |
| Selecting v1 clears the target checkbox | Reselect the Agent after pinning v1; confirm exactly one target. |
| Dataset preview has five rows | This can be a preview limit. Compare the source's 12 rows, registered version, and actual result count. |
| TaskAdherence 1 looks like a low score | It is binary 0/1; 1 means Pass. Do not apply Relevance's 1–5 scale. |
| Reasons are not shown in the conversation view | `conversation_id → User view` shows the question/answer. Use **Detailed metrics result** for `Relevance.reason` and `TaskAdherence.reason`. |
| Output items or metrics are missing | Preserve failures/missing values and the 12-case denominator. Never invent zeros or passes. |

## Agent Optimizer and result interpretation {#optimizer}

| Observation or symptom | Resolution and verification |
|---|---|
| An earlier UI showed **No custom evaluators available** | Use **Custom only OFF** or **View built-in evaluators**. A filter issue does not require creating a different custom evaluator. |
| Optimize is missing or a model cannot be selected | Check New Foundry, prompt-Agent type, project access, preview availability, and role-specific model support. Record tenant availability rather than claiming success when unavailable. |
| Candidate changed the model or tool descriptions | Check **Choose targets → Instruction only** and disable model comparison. Different non-instruction settings invalidate an instruction-only comparison. |
| The actual Optimizer retained v1 | The execution in `evidence/latest.json` selected the strong baseline. Do not hide this or relabel it as automatic candidate promotion. |
| An operator further edited the instructions | Record “operator-reviewed after Agent Optimizer” and perform a separate same-criteria managed evaluation. The published historical v2 follows this pattern. |
| Optimizer ranking improved but reevaluation differs | Its internal 0–1 ranking is not the separate evaluation mean/pass rate. Review full responses, policy errors, and regressions. |
| Means improved but statistics are Inconclusive | The historical Relevance result is 4.8333 → 4.9167; service PairedTTest is Inconclusive. This does not establish significance or equivalence. |
| Latency/tokens increased alongside quality | Historical v2 p95 increased 10.97 → 42.97 seconds; Agent tokens increased 46,167 → 55,858. Report the tradeoff with the quality result. |

Original responses, scores, reasons, and actual run IDs are in the [latest quality report](verification.md#status). Twelve reused synthetic development cases do not establish independent generalization or production safety.

## Deletion and ongoing costs {#cleanup}

| Symptom | Resolution and verification |
|---|---|
| The earlier guide ended at result handoff | [Step 10](handbook.md#cleanup) now provides dedicated/shared paths, inventory checks, authorization, group deletion, and absence verification. |
| Search charges remain after cleanup succeeds | `cleanup` removes owned objects, not Search hosting, models, groups, or logs. Confirm dedicated-group deletion or an operator retention plan. |
| Missing workspace or `.env` prevents cleanup | Use the interrupted setup's config/manifest and actual Azure inventory. Do not fabricate local ownership records. |
| Group deletion fails due to locks, permissions, or dependencies | Inspect **Locks**, **Activity log**, and the failed deletion in Azure Portal. Ask the lock owner for scoped action; do not remove it unilaterally. |
| Deletion is accepted but the group remains | Inspect asynchronous progress. Only a successful `az group exists` returning `false` proves group absence. |
| Cost analysis still shows charges after deletion | Prior usage and aggregation delay can remain. Check date range, resources, and any external retained services. |
| Soft-deleted items remain | Follow service-specific retention policy. An authorized owner decides whether separate permanent deletion/purge is necessary. |

Follow the [Azure resource-group deletion documentation](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group). Group deletion is irreversible; individual service recovery features do not guarantee resource-group recovery.

## Portal illustrations and learning structure {#portal-captures}

On 2026-10-03, after the user completed login, **Playwright Headless** captured 14 new image files. The temporary login browser and authenticated headless context were closed afterward; authentication state was not exported to a file. Only opaque privacy masks and cropping were applied, without replacing statuses, failure history, or instructions.

| Step illustrated | New views and what to inspect |
|---|---|
| 01 Environment/access | Two shared views: subscription Essentials and Check access. Distinguish status, role, and scope. |
| 02 Provisioning checks | Three views per language: resource inventory, existing-project selection, and project endpoint. Selection is not additional creation. |
| 03 Policy/Agent | Two views per language: Knowledge connection and pinned v1 configuration. Active/disabled Save are not retrieval or evaluation success. |
| 10 Cleanup | One unsubmitted deletion review per language. Inspect proposed resources, empty confirmation, and disabled Delete; both panes were closed with Cancel. |

Each complete edition uses its previous 12 plus eight added views, totaling 20. The two administrative views are shared rather than duplicated, so there are 14 new files. Korean and English Agent/knowledge views were captured separately in their corresponding existing projects.

| Observed difference or issue | Resolution in the guide |
|---|---|
| The supplied reference `.htm` URL returned 404 | Verified the same repository's actual `index.ko.html`. Used only the goal/concept/preparation/execution/completion/troubleshooting structure, not its data or scoring. |
| Portal status is Active; CLI status is Enabled | Documented the equivalent states in 01 and the caption rather than requiring identical wording. |
| Current IAM uses Check access instead of View my access | Captured active assignments and Scope; documented both UI labels. |
| The New Foundry toggle did not immediately become checked | The existing-project selection dialog and Let's go were required first; the guide now shows that actual step. |
| Inventory/deletion content uses embedded React frames | Masked subscription/identity values inside the iframe as well as the outer page, then inspected the images. |
| The deletion pane says “resources being deleted” | Clarified that this is the proposed list. Confirmation/button state and actual resource absence require separate checks. |
| Knowledge shows a free-retrieval banner | Clarified that the whole lab is not free and no plan upgrade is required for inspection. No plan change was made. |

**Observed before/after result:** Resource IDs, per-Agent version lists, and evaluation/run ID lists were compared through read-only requests.

| Environment | Resources before/after | Agents/versions before/after | Evaluations/runs before/after |
|---|---|---|---|
| Existing Korean lab | 5 / 5 | Agents 3 / 3; versions 4 / 4 | Evaluations 2 / 2; runs 7 / 7 |
| Existing English lab | 6 / 6 | Agents 6 / 6; versions 10 / 10 | Evaluations 6 / 6; runs 23 / 23 |

No resources, Agent versions, evaluations, or Optimizer jobs were created or deleted; no chat or retrieval question was submitted. The displayed English v1 instruction hash matched the baseline source. The Korean image preserves remote v1 instructions from before the prose revision; it is not a new execution.

Hashes, dimensions, redactions, and states are in the [Korean manifest](../../web/assets/portal/captures.json), [English manifest](../../web/assets/portal/en/captures.json), and [shared administrative manifest](../../web/assets/portal/shared/captures.json). Earlier images, evaluation data, and measured JSON remain unchanged.

**Illustrated-edition checks:** All 582 automated checks passed. Both languages were inspected at 1440px desktop and 390px mobile with four overview cards, ten step explanations, 18 participant figures, and two operator-reference figures. New-figure language switching, progress/theme persistence, full-size image opening, and JavaScript-disabled navigation worked without page-level horizontal overflow or page errors.

## Checks from the preceding ten-step revision {#verification}

The 579 checks and PDFs with 12 images each below describe the **ten-step revision completed before the additional captures**. The later Portal/structure work is documented above and in the capture manifests. Earlier numbers are not relabeled as verification of new files.

**Actual read-only observation:** On 2026-10-03, the existing approved environment's CLI identity matched all three expected values and its subscription was Enabled. `native-evals` retrieved completed v1/v2 runs with 12 cases each, plus a separate draft run, from `contoso-en-sol-learning-loop`. The v1 11/12 and v2 12/12 counts matched the published report. No new evaluation, optimization, Agent creation, or deletion request was sent.

**Local reproduction commands:** Run in the virtual environment; these create no Azure resources.

During automated verification, `--help` correctly exited through `SystemExit(0)`, and macOS temporary paths exposed the `/var` symlink. The test harness now recognizes successful help exits and resolves its temporary directory to a physical path. Bootstrap's symlink protection was not weakened, and no user files were moved.

| Check performed in this revision | Result |
|---|---|
| Local execution | Executed both guides' local plans, unapproved-apply refusal, and row-count/hash commands. All 579 automated checks passed. |
| Browser | Verified both languages at 1440px desktop and 390px mobile. Ten-step navigation, language switching, progress/theme persistence, and JavaScript-disabled navigation worked, with no page-level horizontal overflow or page errors. |
| Print/PDF | Both complete editions include 12 language-matched portal images. Required content, local-machine links, out-of-page text, and nearly empty-page checks passed. |
| Platform scope | Actual execution used macOS. Windows PowerShell commands are provided separately, not represented as tested on Windows. |

```bash
python scripts/build_datasets.py --language ko --check
python scripts/build_datasets.py --language en --check
python scripts/build_guide.py --check
python -m unittest discover -s tests -q
```

The first direct PDF-check invocation reported `ModuleNotFoundError: pymupdf`. After reconfirming the import and version in the selected virtual environment, both files passed through the module entry point below. The initial import failure's cause was not established; it is not labeled a defective package. If the PDF dependency is genuinely missing, install `requirements-verification.lock` in the maintenance environment only.

```bash
python -m scripts.verify_pdf docs/Foundry-Learning-Loop-Lab-KO.pdf --language ko --out .lab/verification/pdf-ko.json
python -m scripts.verify_pdf docs/Foundry-Learning-Loop-Lab-EN.pdf --language en --out .lab/verification/pdf-en.json
```

Checks cover the two HTML editions' ten-step sequence, reciprocal anchors, links, command arguments, fixed-Agent ownership/configuration invariants, read-only ID lookup, and duplicate-submission guards. Local mocks do not establish a fresh Azure creation, paid execution, or deletion. A new lab must still satisfy each step's real completion criteria.

Formalizing authored Korean instructions changes the baseline prompt, system messages in supporting generated data, and corresponding manifest hashes. **Policies, questions, reference answers, evaluation dev12, and historical measured output remain unchanged.** Use the original run's instruction snapshot when reproducing an earlier execution; do not overwrite historical hashes with the revised prompt hash.

Official references: [project creation](https://learn.microsoft.com/azure/foundry/how-to/create-projects), [Foundry RBAC](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry), [Agent Optimizer](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent), and [resource-group deletion](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group).
