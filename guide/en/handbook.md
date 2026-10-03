# Great agents start with evaluation · v1 {#좋은-에이전트는-평가에서-시작된다-v1}

<p class="eyebrow">CONTOSO ATLAS CLOUD · ONE LEARNING PATH</p>

**Prepare Azure, evaluate and improve an Agent you create, and delete the resources when you finish.** Start at 01 if this is your first visit. If you received a prepared environment, still confirm your identity, permissions, and handoff details first.

Microsoft Foundry brings model deployment, Agent versioning, and evaluation into a project-based development environment. This lab builds a fictional **Contoso Atlas Cloud support Agent** and compares its responses using the same policies and 12 questions. Here, learning means **reading evaluation results and improving instructions**, not retraining model weights.

<div class="hero-summary" aria-label="Lab purpose and outcomes">
<div><strong>WHAT YOU BUILD</strong><span>A policy-grounded support Agent and a comparison record containing actual responses and evaluator reasons.</span></div>
<div><strong>WHY IT MATTERS</strong><span>Explain improvement using matched conditions, scores, evidence, and failures rather than one convincing answer.</span></div>
<div><strong>HOW YOU PROCEED</strong><span>Prepare → evaluate v1 → analyze weaknesses → improve instructions → reevaluate → clean up.</span></div>
<div><strong>WHAT YOU KEEP</strong><span>Actual run IDs, dataset hashes, an accept/retain/hold decision, and deletion or retention-handoff evidence.</span></div>
</div>

<ol class="learning-path" role="list" aria-label="Lab steps">
<li><a href="#setup"><strong>01</strong> Check your account, computer, and access</a></li>
<li><a href="#resources"><strong>02</strong> Create the Foundry environment</a></li>
<li><a href="#agent"><strong>03</strong> Connect policies and create the Agent</a></li>
<li><a href="#start"><strong>04</strong> Register the dataset</a></li>
<li><a href="#prepare"><strong>05</strong> Select evaluation criteria</a></li>
<li><a href="#baseline"><strong>06</strong> Run Foundry Evaluation</a></li>
<li><a href="#analyze"><strong>07</strong> Read scores and reasons</a></li>
<li><a href="#optimize"><strong>08</strong> Improve instructions with Agent Optimizer</a></li>
<li><a href="#decision"><strong>09</strong> Reevaluate and compare v1/v2</a></li>
<li><a href="#cleanup"><strong>10</strong> Save results and delete resources</a></li>
</ol>

Use **your own representative tasks and business criteria**, not a public benchmark alone. Synthetic Contoso policies demonstrate **evaluate → learn → improve → reevaluate** without publishing private customer data.

| Where you work | What you do there |
|---|---|
| [Azure Portal](https://portal.azure.com) | Verify identity, subscription, permissions, actual resources, and deletion scope. |
| Local terminal | Prepare files and the virtual environment, then run authorized setup and ID-lookup commands. |
| [Microsoft Foundry](https://ai.azure.com) | Inspect the project, Agent, and policy tool; run evaluations and Optimizer; read comparisons. |

**How to read a step:** Start with its **what, why, and how** panel. Follow the commands or numbered actions, and find the controls named in each screenshot caption. Check the final **completion criteria** before continuing. Opening a screen or marking a section as read does not complete a live operation.

**How to follow this guide:** Steps 01–03 prepare the environment; 04–09 use the Foundry portal for evaluation and improvement. Unless stated otherwise, run commands from the repository's top-level folder. Replace `YOUR_...` placeholders with your own values. Names in illustrative output and historical screenshots are not your resource names.

| Before you start | Guidance |
|---|---|
| Time | Allow half a day for first-time setup. Permission and quota approval waits are separate. |
| Cost | Model, evaluation, and optimization calls, Search hosting, and logs can incur charges. A free subscription does not guarantee access to every model. |
| Access | Use a dedicated lab environment you are authorized to create and clean up. An operator can perform only the privileged steps and supply the handoff. |
| Prepared environment | Obtain every value in the [operator handoff](admin-setup.md#handoff), verify the completion criteria in 02–03, and continue at 04 without creating duplicate resources. |
| Finish | Complete the deletion checks or approved retention handoff in 10, not just the evaluation report. |

**Version meaning:** v1/v2 are complete Foundry Agent versions. Keep the model, tools, and output format fixed; change only instructions. Do not weaken v1 or promise an improvement before measuring it. In a new lab, v2 is initially a comparison candidate; creating it is not acceptance or production approval.

<p class="output-notice" id="portal-screenshots-note"><strong>How to read the pictures:</strong> These are real Portal captures made with Playwright Headless. Steps 01–03 and 10 were illustrated on 2026-10-03: two subscription/access views are shared administrative controls; six additional views use the existing English lab. Controls are English. Identifying information is masked, not statuses, instructions, or scores. No creation, saving, chat, or final deletion was submitted. Compare names with your own environment. Neither earlier evaluation pictures nor new captures replace the <a href="verification.md">measured quality report</a>.</p>

## 01. Check your account, computer, and access {#setup}

<a id="environment"></a><a id="sdk-prerequisites"></a>

<div class="lab-concept" data-learning-frame="setup">
<p><strong>What:</strong> Confirm the Azure subscription, access, and local execution environment.</p>
<p><strong>Why:</strong> Different browser and CLI identities can cause access failures or create resources in the wrong environment.</p>
<p><strong>How · where:</strong> Check subscription/access in Azure Portal, then compare tools, login, and language settings in the terminal. No Azure resources are created yet.</p>
</div>

### Confirm your Azure account and subscription {#setup-account}

1. Sign in to the [Azure portal](https://portal.azure.com). If you do not have an account, follow the [Azure account instructions](https://azure.microsoft.com/pricing/purchase-options/azure-account) to obtain your own or an organization-provided account. For an organization account, first request access to the approved subscription.
2. Search for **Subscriptions** in the top search box and open the intended subscription. Confirm portal status **Active** and record its **Subscription ID** and **Directory/Tenant ID**. The CLI describes the same usable subscription as **Enabled**. If it is missing, check directory and subscription filters under your account.
3. Open **Access control (IAM) → Check access** and inspect your assignments. Older UI versions may label this **View my access**. Automated setup requires both resource creation and role-assignment permissions. Contributor alone does not grant role-assignment authority. See [required access and administrator requests](admin-setup.md#rbac).
4. Agree on a budget, end time, and cleanup owner. Do not create resources without subscription access and cost authorization. Do not grant new subscription-wide Owner access or disable organizational security controls as a shortcut.

<figure class="portal-shot" id="portal-subscription-overview" data-capture-scope="shared">
<img src="../../web/assets/portal/shared/21-subscription-overview.png" alt="Actual Azure subscription Overview showing Essentials, Subscription ID, Directory, Status, and My role; identity and billing details are masked or cropped." width="1440" height="347" loading="lazy">
<figcaption><strong>Check the subscription and status.</strong> Find Subscription ID, Directory, Status, and My role under Essentials. Portal <strong>Active</strong> and CLI <strong>Enabled</strong> describe the same usable state. This administrative view is shared between the two guide languages. <a href="../../web/assets/portal/shared/21-subscription-overview.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-check-access" data-capture-scope="shared">
<img src="../../web/assets/portal/shared/22-check-access.png" alt="Actual Azure Portal Access control IAM and Check access page showing active role and scope, with user identity masked." width="1440" height="850" loading="lazy">
<figcaption><strong>Read the role and its scope together.</strong> Find Access control (IAM) on the left, Check access at the top, and active assignments below. Owner was already assigned to the capture account; the picture is not a recommendation to grant participants that role. <a href="../../web/assets/portal/shared/22-check-access.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

### Install tools and download the lab {#setup-local}

Install [Python](https://www.python.org/downloads/) **3.11–3.14**, [Git](https://git-scm.com/downloads), and the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli). Use a **macOS/Linux terminal or Windows PowerShell**, not the interactive Python prompt. Open a new terminal after installation.

```bash
git --version
az version
git clone https://github.com/junwoojeong100/foundry-evaluation-labs-v1.git
cd foundry-evaluation-labs-v1
```

If you already downloaded the repository, enter its folder rather than cloning it again. With GitHub **Code → Download ZIP**, extract the archive first and open the folder containing `pyproject.toml` and `requirements.lock`. Downloading only an HTML file omits the code, data, and images.

**On macOS/Linux, run:**

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
```

**In Windows PowerShell, run:**

```powershell
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell policy blocks activation, do not change organizational policy. Replace `python` in subsequent commands with `.\.venv\Scripts\python.exe`. If `.venv` already exists, confirm that it belongs to this lab rather than overwriting another task's environment.

**After preparing the virtual environment, run these shared commands:**

```bash
python -m pip install -r requirements.lock
python -m lab --help
python scripts/build_datasets.py --language en --check
```

Confirm that the command list appears and the dataset check succeeds. For `ModuleNotFoundError`, use `python -m pip --version` to check that Python and pip belong to `.venv`. Do not install packages into an unrelated system interpreter.

### Pin the CLI identity and lab language {#setup-login}

```bash
az login
az account list --query "[].{name:name,id:id,state:state}" -o table
az account set --subscription "YOUR_SUBSCRIPTION_ID"
az account show --query "{user:user.name,tenant:tenantId,subscription:id,state:state}" -o json
```

Replace `YOUR_SUBSCRIPTION_ID` with the ID you recorded. Compare the final `user`, `tenant`, and `subscription` with the portal, and record them for the plan. Browser and CLI sign-ins are separate. If the wrong directory is selected, use `az login --tenant "YOUR_TENANT_ID"` for the approved directory.

Use **`lab-en`** as this English lab's environment name. If that local plan already exists, resume its original records rather than creating it again. For a separate class, choose a new name such as `lab-en-02` and change every subsequent path and prefix consistently.

**On macOS/Linux, set:**

```bash
export LAB_LANGUAGE=en
export LAB_ARTIFACTS_DIR="$PWD/.lab/lab-en/artifacts"
```

**In Windows PowerShell, set:**

```powershell
$env:LAB_LANGUAGE = "en"
$env:LAB_ARTIFACTS_DIR = Join-Path (Get-Location).Path ".lab/lab-en/artifacts"
```

Repeat virtual-environment activation and these two settings in each new terminal. Never change `LAB_LANGUAGE` while reusing another language's run folder. The generated `.env` is configuration, not a shell or PowerShell script; do not execute or `source` it.

**Completion criteria:** The user, tenant, and subscription match; the Python commands and English dataset check succeed. For blockers, see [environment troubleshooting](troubleshooting.md#environment).

<p class="step-next no-print"><a href="#resources" data-next-step>Next: 02. Create the Foundry environment →</a></p>

## 02. Create the Foundry environment {#resources}

<a id="first-infrastructure-failure"></a>

<div class="lab-concept" data-learning-frame="resources">
<p><strong>What:</strong> Prepare a Foundry project, models, Search, and monitoring in a dedicated resource group.</p>
<p><strong>Why:</strong> The group bounds cost and cleanup; the project organizes Agents and evaluations. An empty project alone does not provide policy retrieval.</p>
<p><strong>How · where:</strong> Plan, authorize, and provision from the terminal, then compare both portals with the outputs. Reuse a prepared environment instead of creating duplicates.</p>
</div>

```text
Azure subscription
└─ Dedicated lab resource group
   ├─ Foundry resource
   │  ├─ Four role-specific model deployments
   │  └─ Project → Agent, evaluations, data
   ├─ Azure AI Search → read-only Contoso policy retrieval
   └─ Application Insights + Log Analytics → monitoring and logs
```

A project is the workspace containing Agents and evaluations. A model name identifies the product; a **deployment name identifies the model instance your environment calls**. The project endpoint and Azure OpenAI endpoint are not interchangeable.

### Create a local provisioning plan {#resources-plan}

Insert the three identity values from 01. This command creates only a plan and unapproved authorization example under `.lab/lab-en/`; it makes no Azure calls.

```bash
python -m lab bootstrap plan --subscription "YOUR_SUBSCRIPTION_ID" --tenant "YOUR_TENANT_ID" --expected-user "YOUR_SIGN_IN_NAME" --environment lab-en --location northcentralus
```

Confirm `plan_status: CREATED_LOCAL_ONLY`, `mutations_performed: false`, and `config_path`. `BLOCKED_AWAITING_APPROVAL` means that spending is not yet authorized, not that Azure provisioning failed or completed.

| Generated file | What to check |
|---|---|
| `.lab/lab-en/config.json` | Identity, generated resource names, and exact model/version/capacity selections. Do not edit this hashed plan. |
| `.lab/lab-en/approval.example.json` | The initially unapproved cost and change scope. |
| `.lab/lab-en/manifest.json` | Provisioning, ownership, and interruption records. Preserve this file. |
| `.lab/lab-en/.env` | Not present yet. Successful provisioning creates this runtime configuration. |

This repository's setup region is **North Central US (`northcentralus`)**. Defaults are Agent `gpt-6-sol`, Judge `gpt-6-luna`, Optimizer/search planner `gpt-5.5`, and embedding `text-embedding-3-small`. Check the exact versions, SKUs, and capacity units in the [model table](admin-setup.md#prepare) and plan. Do not silently substitute a different region or model.

### Check readiness and obtain cost authorization {#resources-approval}

```bash
python -m lab bootstrap preflight --config .lab/lab-en/config.json
```

Look for `readiness_status: READY`. If access, provider registration, model version, quota, or capacity is blocked, read `reason` and follow [provisioning troubleshooting](troubleshooting.md#provisioning). Without an approval file, the overall status can still await approval even when readiness is READY. Do not keep creating new environments or switching regions.

The actual budget owner opens `.lab/lab-en/approval.example.json` in an editor and uses **Save As** to create `.lab/lab-en/approval.json`. Keep the original `scope_sha256`, `models`, and `retention_days`. Complete **every field in the [approval worksheet](admin-setup.md#approval)** according to the real authorization, including approver, currently valid timestamps, currency/budget, wait/hosting bounds, and resource/RBAC/global-processing consent.

Changing only `approved` to `true` is insufficient. The budget value is not an Azure spending cutoff, and a documentation example is not spending authorization.

```bash
python -m lab bootstrap preflight --config .lab/lab-en/config.json --approval .lab/lab-en/approval.json
```

**Proceed only when both `readiness_status: READY` and `status: READY_FOR_APPROVED_APPLY` are present.**

### Provision and confirm the resources in the portal {#resources-create}

```bash
python -m lab bootstrap apply --config .lab/lab-en/config.json --approval .lab/lab-en/approval.json
python -m lab bootstrap status --config .lab/lab-en/config.json --approval .lab/lab-en/approval.json
```

The first command creates resources, deployments, connections, and resource-scoped roles. It can take time; do not launch a second `apply` in another terminal. Confirm **APPLIED**, a generated `.lab/lab-en/.env`, and `status` showing `phase: succeeded` with the expected resources present. After a timeout, inspect `status` first and follow the [resume procedure](troubleshooting.md#provisioning).

1. In [Azure Portal](https://portal.azure.com) → **Resource groups**, search for `names.resource_group` from `config.json`. Confirm the subscription, region, and complete resource list.
2. Open [Foundry](https://ai.azure.com) with **New Foundry** enabled. If **Select a project to continue** appears, choose `names.project` and select **Let's go**. Read and **Close** the welcome tour if shown. If already in New Foundry, use the upper-left project selector. Do not use a Classic hub-based project.
3. In the project's **Overview**, find its endpoint. It must match `AZURE_AI_PROJECT_ENDPOINT` in `.env`, in the form `https://account.services.ai.azure.com/api/projects/project`.
4. In **Models + endpoints** or **Build → Models**, locate the deployments matching `.env` values `MODEL_DEPLOYMENT`, `JUDGE_DEPLOYMENT`, `OPTIMIZER_DEPLOYMENT`, and `EMBEDDING_DEPLOYMENT`. See [portal orientation](admin-setup.md#prepare) if labels differ.

<figure class="portal-shot" id="portal-created-resources">
<img src="../../web/assets/portal/en/23-resource-group.png" alt="Actual Overview of the existing English lab resource group, including Foundry, project, Search, monitoring resources, and preserved earlier deployment failures." width="1440" height="1000" loading="lazy">
<figcaption><strong>Compare the plan with actual resources.</strong> Check the group name and Location, then identify Foundry, Foundry project, Search, Application Insights, and Log Analytics. Earlier Failed deployment history remains visible. This existing environment is not presented as a new bootstrap success. <a href="../../web/assets/portal/en/23-resource-group.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-select-project" data-capture-layout="dialog">
<img src="../../web/assets/portal/en/24-select-project.png" alt="Actual New Foundry entry dialog with the existing English project selected; this selects a project rather than creating one." width="640" height="474" loading="lazy">
<figcaption><strong>Select the project you prepared.</strong> Compare its name with <code>names.project</code> and open it with Let's go. This selects an existing project; it does not create another. After bootstrap, do not use Create a new project to duplicate the environment. <a href="../../web/assets/portal/en/24-select-project.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-project-endpoint">
<img src="../../web/assets/portal/en/25-project-overview.png" alt="Existing English Foundry project Home showing the selected project, New Foundry, View deployments, and two endpoint fields with identifying values masked." width="1440" height="492" loading="lazy">
<figcaption><strong>Check the project and endpoint.</strong> First confirm the upper-left project name. The value to copy and compare is <strong>Project endpoint</strong>, not Azure OpenAI endpoint. Open the model list through View deployments. Read masked values in your own portal. <a href="../../web/assets/portal/en/25-project-overview.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

```bash
python -m lab --config .lab/lab-en/.env preflight
```

**Completion criteria:** Runtime preflight reports `PASS`; your project and role-specific deployments are present. This is read-only configuration evidence. The next step verifies actual model responses.

<p class="step-next no-print"><a href="#agent" data-next-step>Next: 03. Connect policies and create the Agent →</a></p>

## 03. Connect policies and create the Agent {#agent}

<a id="model-smoke"></a><a id="iq"></a>

<div class="lab-concept" data-learning-frame="agent">
<p><strong>What:</strong> Connect a read-only synthetic-policy tool to the pinned v1 baseline Agent.</p>
<p><strong>Why:</strong> Recalling a policy is not the same as retrieving it. Retrieval under your user identity does not establish access for the Agent's managed identity.</p>
<p><strong>How · where:</strong> Prepare model, retrieval, and Agent from the terminal; inspect instructions, tools, and an actual response in Foundry. Transmit data and make calls once within the approved scope.</p>
</div>

### Verify the model and policy retrieval {#agent-knowledge}

```bash
python -m lab --config .lab/lab-en/.env smoke --run-id model-smoke --confirm
python -m lab --config .lab/lab-en/.env iq prepare --confirm
python -m lab --config .lab/lab-en/.env iq probe --confirm
```

The first command obtains a real model response. The second prepares the [eight synthetic policies](../../data/en/knowledge/documents.json), embeddings, search index, knowledge base, and project MCP connection. The third performs actual retrieval.

Confirm smoke `status: completed`, knowledge setup `uploaded_documents: 8`, and retrieval **`status: retrieval_verified`** with nonempty references. `created_not_retrieval_tested` means creation only, not successful retrieval. If Search is not ready, preserve the records and follow [retrieval troubleshooting](troubleshooting.md#knowledge).

In the portal, open **Build → Knowledge → Knowledge bases** and inspect Connection, the created knowledge base, and Knowledge sources. One knowledge-base row does not mean there is only one policy document.

<figure class="portal-shot" id="portal-policy-connection">
<img src="../../web/assets/portal/en/26-knowledge-base.png" alt="Actual Knowledge Foundry IQ page in the English lab with the Connection, knowledge-base row, Knowledge sources, and Active status." width="1440" height="374" loading="lazy">
<figcaption><strong>Confirm the policy connection.</strong> Inspect Connection, Knowledge sources, and Active for the intended base. Active is registration state; verify actual retrieval with <code>iq probe</code>. The free-retrieval banner does not make the whole lab free, and setup inspection does not require changing the billing plan. <a href="../../web/assets/portal/en/26-knowledge-base.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

### Create v1 with the fixed comparison configuration {#agent-create}

```bash
python -m lab --config .lab/lab-en/.env native-agent --version 1 --confirm
```

This creates **`lab-en-iq` version `1`** using `prompts/en/baseline.txt`, the verified policy tool, and strict four-field JSON output. Record `agent_name`, `version`, and `receipt`. The command reuses an identical v1 in the same owned workspace; it does not adopt an unrelated same-named Agent or create v3.

<figure class="portal-shot" id="portal-agent-configuration">
<img src="../../web/assets/portal/en/27-agent-configuration.png" alt="Actual version-1 English Sol Agent Playground showing Model, Instructions, connected Knowledge, and empty Chat; Save is disabled and no message was sent." width="1440" height="1000" loading="lazy">
<figcaption><strong>Check version, instructions, and Knowledge.</strong> Locate Version above, Model and Instructions on the left, Knowledge below, and Chat on the right. The policy MCP connection appears under Knowledge. This is the existing English v1, whose displayed instruction hash matched the baseline source. Save was disabled and no chat was sent; use your own Agent name. <a href="../../web/assets/portal/en/27-agent-configuration.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

In the portal, open **Build → Agents → lab-en-iq → version 1**. Use the command's actual Agent name. Send this one question in **Test/Playground**:

> I first purchased a monthly subscription in September 2026. What are the refund application conditions?

Check for `answer`, `citations`, `route`, and `needs_human`. Inspect the execution details for a real **`knowledge_base_retrieve` call and response**. Compare `ATLAS-*` policy IDs with the answer's evidence. Direct retrieval can succeed while the Agent fails because its managed identity has different access.

**Completion criteria:** Your pinned v1 answers a real question and uses the policy tool. Connection success or valid JSON alone is not measured quality. Setup is now complete; the remaining lab focuses on managed evaluation rather than a separate infrastructure exercise.

<p class="step-next no-print"><a href="#start" data-next-step>Next: 04. Register the dataset →</a></p>

## 04. Register the dataset {#start}

<a id="demo"></a><a id="understand"></a><a id="data"></a>

<div class="lab-concept" data-learning-frame="start">
<p><strong>What:</strong> Register the English dev12 file once so both versions receive the same questions.</p>
<p><strong>Why:</strong> Changing questions or reference answers obscures the instruction change. Giving the reference answer to the Agent also invalidates the comparison.</p>
<p><strong>How · where:</strong> Check count/hash in the terminal, then register the original file or reuse its exact version in the Foundry evaluation wizard.</p>
</div>

Use **[data/en/optimizer/dev.jsonl](../../data/en/optimizer/dev.jsonl)** unchanged: **12 JSONL rows**. JSONL contains one JSON object per line. Do not convert it to Excel, CSV, or a JSON array.

```bash
python -c "import hashlib,pathlib; p=pathlib.Path('data/en/optimizer/dev.jsonl'); print('rows =',len(p.read_text(encoding='utf-8').splitlines())); print('sha256 =',hashlib.sha256(p.read_bytes()).hexdigest())"
```

Record `rows = 12` and SHA-256. The historical English rehearsal used `contoso-eval-en-dev12` version `1`; its name, IDs, and scores are not new results from your environment.

| Column | Type | Use |
|---|---|---|
| `query` | String | The only Agent input |
| `context` | String | Policy reference for supported evaluators and case review |
| `ground_truth` | JSON string | Structured reference answer, never a generation prompt |

Record all 12 rows, the registration/version and file SHA-256. Keep the bytes identical through baseline, optimization and reevaluation. The source has other reserved subsets; they are not part of this workshop.

The Agent returns exactly `answer`, `citations`, `route`, `needs_human`. `answer` is English, citations are supporting policy IDs, route is `answer/clarify/escalate/refuse`, and the Boolean `needs_human` is true only for `escalate`. The Agent cannot actually submit, refund, delete or grant access.

Open **Foundry New experience → Build → Evaluations → Create → Create new evaluation**. Select target type **Agent → `lab-en-iq`**, pin the baseline explicitly to **v1**, and confirm one checked target. **Pin currently latest** is safe only while latest really is v1; selecting it can clear the checkbox.

Choose **Individual turns** and **One time**. In a new project, select **Upload new dataset → Browse**, then the repository's `data/en/optimizer/dev.jsonl`. Name it **`lab-en-dev12`**, use first version **`1`**, and wait for upload/registration to finish. If already registered, use **Existing dataset** and select that same name/version. The preview may show five rows; the dataset still has 12.

<figure class="portal-shot" id="portal-evaluation-dataset">
<img src="../../web/assets/portal/en/15-evaluation-dataset.png" alt="Illustrative Foundry Existing dataset selection and five-row preview, not the current run result" width="1440" height="1000" loading="lazy">
<figcaption><strong>Find the dataset controls.</strong> Select the current operator-provided registration. The preview is not proof of the total row count. <a href="../../web/assets/portal/en/15-evaluation-dataset.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Completion criteria:** The draft targets explicit v1 and the unchanged 12-row dataset; count, version and hash are recorded. [Data contract](../../data/README.en.md#schema).

<p class="step-next no-print"><a href="#prepare" data-next-step>Next: 05. Select evaluation criteria →</a></p>

## 05. Select evaluation criteria {#prepare}

<a id="calibration"></a>

<div class="lab-concept" data-learning-frame="prepare">
<p><strong>What:</strong> Select Relevance, TaskAdherence, and the actual Judge deployment.</p>
<p><strong>Why:</strong> Defining scales, pass rules, and mappings beforehand prevents moving the criteria after seeing results. These two evaluators use different scales.</p>
<p><strong>How · where:</strong> Open each evaluator's settings in Foundry Criteria and confirm the threshold and Judge. Send only query to the Agent.</p>
</div>

In **Configure agents**, leave the custom prompt override unset. Input is **`{{item.query}}` only**; never append `context` or `ground_truth`. If field mapping appears, use query → query.

Retain exactly these two managed evaluators:

| Evaluator | Meaning | Setting |
|---|---|---|
| Relevance | Addresses the question, **1–5** | **Threshold 4** |
| TaskAdherence | Follows the task, **binary 0/1 Pass/Fail** | **Pass 1**, not threshold 4 |

In **Criteria → Add evaluators**, select the two evaluators. Open each row's settings, enter its threshold, and select **Apply**. For **Evaluation model/Judge**, select the deployment named by `JUDGE_DEPLOYMENT` in your `.env`, not the Agent or Optimizer deployment.

Preserve service-generated mappings: Relevance `response={{sample.output_text}}`; TaskAdherence `response={{sample.output_items}}`. Read the definition's Raw JSON rather than substituting old UI bindings.

| Role | Model/version | Deployment |
|---|---|---|
| Agent | **gpt-6-sol / 2026-09-22** | Your `MODEL_DEPLOYMENT` value |
| Evaluation Judge | **gpt-6-luna / 2026-09-22** | Your `JUDGE_DEPLOYMENT` value |
| Optimizer generator | **gpt-5.5 / 2026-04-24** | Your `OPTIMIZER_DEPLOYMENT` value |

Sol's actual Agent/tool invocation was verified. Model catalog visibility alone is insufficient, and the [Optimizer support list](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models) is role-specific. Catalog evaluator version links do not prove that a private service rubric version is pinned; preserve the actual definition and disclose that limit.

<figure class="portal-shot" id="portal-evaluation-criteria">
<img src="../../web/assets/portal/en/16-evaluation-criteria.png" alt="Illustrative Relevance and TaskAdherence configuration with separate Judge selection" width="1440" height="1000" loading="lazy">
<figcaption><strong>Read each metric's own scale.</strong> Keep Relevance threshold 4, binary TaskAdherence pass 1, and the current Luna Judge. <a href="../../web/assets/portal/en/16-evaluation-criteria.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Completion criteria:** The two evaluator scales, thresholds, mappings and actual Judge deployment are recorded. The saved remote definition, not a stale local environment default, determines the Judge.

<p class="step-next no-print"><a href="#baseline" data-next-step>Next: 06. Run Foundry Evaluation →</a></p>

## 06. Run Foundry Evaluation {#baseline}

<div class="lab-concept" data-learning-frame="baseline">
<p><strong>What:</strong> Generate real responses from pinned v1 and collect managed scores and reasons.</p>
<p><strong>Why:</strong> A candidate needs a recorded starting point for comparison. Completed means processing ended, not that every response was correct.</p>
<p><strong>How · where:</strong> Review and submit once in Foundry, inspect all 12 items, and use read-only terminal lookup to record the actual evaluation and run IDs.</p>
</div>

Review **v1 + original dev12 + query-only input + two evaluators + your Luna Judge**. Name the new evaluation **`lab-en-learning-loop`** and, if a run-name field is available, name the baseline **`baseline-v1`**. In a prepared class, use the operator's names. When only reading the recorded rehearsal, open its existing completed run rather than submitting another.

For a new authorized class, **Review → Submit** once. Keep the actual evaluation ID and run ID. Wait for completion and account for all 12 cases, including errors or missing results. A configured draft, HTTP creation receipt or successful model smoke is not a completed evaluation.

<figure class="portal-shot" id="portal-evaluation-review">
<img src="../../web/assets/portal/en/17-evaluation-review.png" alt="Illustrative Foundry evaluation Review page; use the current Sol target and own run identifiers" width="1440" height="1000" loading="lazy">
<figcaption><strong>Review before Submit.</strong> This picture illustrates the controls, not the current Sol run. Confirm the actual pinned version and saved evaluation contract. <a href="../../web/assets/portal/en/17-evaluation-review.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Open **Evaluations → your evaluation name → Evaluation runs → baseline run**. If Running, refresh that run and wait. If it remains unfinished after 30 minutes, record the state/error and notify the facilitator. Stopping your wait does not cancel the remote job.

Use this **read-only command** to retrieve actual evaluation and run IDs. If you chose a different name, use that exact name with `--name`.

```bash
python -m lab --config .lab/lab-en/.env native-evals --name lab-en-learning-loop
```

Record `evaluation_id` and the `run_id` whose **`agent_version` is `"1"` and `status` is `completed`**. Evaluation IDs use `eval_...`; run IDs use `evalrun_...`. They are not interchangeable. If several evaluations have the same name, compare their portal creation times, Agents, and runs to select yours. This command submits nothing.

**Completion criteria:** The real Foundry run is Completed and exposes 12 output items. Record failed/error counts in `result_counts` too. A failed or incomplete run stays failed/incomplete. No local custom Judge substitutes for this managed Evaluation.

<p class="step-next no-print"><a href="#analyze" data-next-step>Next: 07. Read scores and reasons →</a></p>

## 07. Read scores and reasons {#analyze}

<a id="score-rubric"></a><a id="worked-evaluation"></a>

<div class="lab-concept" data-learning-frame="analyze">
<p><strong>What:</strong> Connect actual responses and evaluator reasons to policy evidence.</p>
<p><strong>Why:</strong> An average can hide a date, citation, or routing failure. Explain the defect before deciding which instruction to change.</p>
<p><strong>How · where:</strong> Read Foundry detailed metrics, User view, and the source policy together; record a hypothesis and behaviors to preserve in notes.md.</p>
</div>

Read summary counts and **Detailed metrics result**, especially **`Relevance.reason`** and **`TaskAdherence.reason`**. `conversation_id → User view` opens the actual question/answer, not an inline Judge-reason panel.

Select a failing or lowest-score case and a good case. Connect **question → actual response → score/reason → policy and parsed reference answer**. If no failure exists, say so; never weaken the baseline to produce one.

<figure class="portal-shot" id="portal-evaluation">
<img src="../../web/assets/portal/en/18-evaluation-results.png" alt="Illustrative evaluation summary and detailed-metric controls; current values are in the latest v2 report" width="1440" height="1000" loading="lazy">
<figcaption><strong>Find scores and reasons.</strong> This earlier UI image is not current verification. Read the current run IDs and full case evidence in the latest report. <a href="../../web/assets/portal/en/18-evaluation-results.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Relevance 4/5 is not 80% accuracy. TaskAdherence 1 means Pass, not a low five-point score. Missing values are not zeros or successful rows. Generic evaluators do not certify every business rule.

<figure class="portal-shot" id="portal-evaluation-case">
<img src="../../web/assets/portal/en/19-evaluation-case.png" alt="Illustrative conversation_id User view showing a question and JSON answer, not Judge reasons" width="1440" height="340" loading="lazy">
<figcaption><strong>Read the response separately.</strong> Return to Detailed metrics result for the reasons and compare the source policy. Do not copy this older answer as current evidence. <a href="../../web/assets/portal/en/19-evaluation-case.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Watch for wrong date boundaries, unnecessary assumptions, numeric retrieval IDs instead of document citations, incorrect human routing, invented actions and unsupported certainty. A truthful statement of uncertainty must not be replaced with a fabricated fact to satisfy a Judge.

Create `.lab/lab-en/notes.md` in your editor and fill in this worksheet with your own results. Retain full responses and reasons separately; use the worksheet for identifiable runs/cases and concise observations.

| Record | What to write |
|---|---|
| Baseline | Actual evaluation ID, run ID, Agent version, and dataset hash |
| Results | Per-metric pass/fail/error counts across all 12 cases |
| Problem case | Question, problematic sentence in the actual response, evaluator reason, and policy ID |
| Improvement hypothesis | For a date-boundary mistake, require checking effective dates and inclusive boundaries; do not embed the answer |
| Behaviors to preserve | Correct citations, honest uncertainty, and action boundaries already working well |

<p class="share-checkpoint" id="share-baseline"><strong>Discuss:</strong> State the run ID, each metric's scale/pass count, a concrete problematic answer and the instruction behavior you want to improve.</p>

**Completion criteria:** You can explain a real weakness and a supported improvement hypothesis, not just an average.

<p class="step-next no-print"><a href="#optimize" data-next-step>Next: 08. Improve instructions with Agent Optimizer →</a></p>

## 08. Improve instructions with Agent Optimizer {#optimize}

<a id="tune"></a>

<div class="lab-concept" data-learning-frame="optimize">
<p><strong>What:</strong> Generate instruction candidates with Agent Optimizer and review the changes.</p>
<p><strong>Why:</strong> Candidate generation does not guarantee improvement. A higher internal rank cannot justify invented policy or changed model/tool conditions.</p>
<p><strong>How · where:</strong> Run Instruction only in Foundry and inspect View changes. Save complete reviewed instructions and their actual provenance privately.</p>
</div>

Open **Build → Agents → lab-en-iq → Optimize Preview/Optimize → Agent**, not Cost. For a new job, select **Create an optimization run** or **Create optimization run**. If preview access or model support differs in your subscription, see [Optimizer troubleshooting](troubleshooting.md#optimizer).

| Setting | Choice |
|---|---|
| Agent version | Explicit baseline **1** |
| Choose targets | **Instruction only**; Model and Tool description off |
| Max candidates | Operator-approved bound; this run uses at most **2**, not more releases |
| Optimization model | Your `OPTIMIZER_DEPLOYMENT` / gpt-5.5 |
| Evaluation model | Your `JUDGE_DEPLOYMENT` / gpt-6-luna |
| Dataset | Same registered English dev12 version 1 |
| Criteria | Relevance 4; TaskAdherence binary pass 1 |

<figure class="portal-shot" id="portal-optimizer-target">
<img src="../../web/assets/portal/en/07-optimizer-target.png" alt="Illustrative instruction-only Agent Optimizer target controls, not the current Sol job configuration" width="1210" height="968" loading="lazy">
<figcaption><strong>Separate the model roles.</strong> Use the current operator-provided Sol target, Luna Judge and supported generator; this capture only locates the controls. <a href="../../web/assets/portal/en/07-optimizer-target.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

If Criteria shows **No custom evaluators available**, switch **Custom only OFF** or select **View built-in evaluators**. Open each built-in row, set its correct threshold and Apply. Do not create a custom scorer to bypass a filter.

<figure class="portal-shot" id="portal-optimizer-data">
<img src="../../web/assets/portal/en/08-optimizer-dataset.png" alt="Illustrative Agent Optimizer dataset selection using the existing English dev12 registration" width="1210" height="968" loading="lazy">
<figcaption><strong>Reuse the data.</strong> Same registered version and all 12 cases; synthetic regeneration or a changed upload would change the experiment. <a href="../../web/assets/portal/en/08-optimizer-dataset.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

In **Review**, confirm the Agent/version, dataset, evaluators, and estimated cost, then **Submit** once within the approved scope. An estimate is not a billing cap. Open the job in **Optimization runs**, wait at most 60 minutes, and retain its actual state. Reuse the same job ID when resuming. Optimization includes multiple internal calls.

Inspect original/candidate scores and **View changes**. The internal **0–1 ranking** is not the separate managed Evaluation mean or pass percentage. Keep model, tools, reasoning and output schema unchanged; an empty function-tool export does not authorize removal of the MCP policy connection.

**Current run:** the managed Optimizer retained the strong v1 baseline. Its generated candidates were not automatically promoted. The operator used the observed failures to refine the instructions and verified that reviewed draft separately. The current v2 source is therefore **operator-reviewed after Agent Optimizer**, not the service's automatically recommended candidate.

<figure class="portal-shot" id="portal-optimizer-results">
<img src="../../web/assets/portal/en/09-optimizer-results.png" alt="Illustrative Optimizer result controls; the latest job results are reported separately" width="1440" height="1000" loading="lazy">
<figcaption><strong>Read the candidate, not just the ranking.</strong> This image is an older UI example. The current report identifies the actual job and selected candidate. <a href="../../web/assets/portal/en/09-optimizer-results.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-optimizer-diff">
<img src="../../web/assets/portal/en/10-optimizer-changes.png" alt="Illustrative View changes dialog for comparing instructions; not the current Sol candidate text" width="1038" height="622" loading="lazy">
<figcaption><strong>Review the actual current diff.</strong> Reject invented policy, unsupported certainty or configuration changes. Longer instructions are not automatically better. <a href="../../web/assets/portal/en/10-optimizer-changes.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Bring the candidate into the next step.** Select it in the result and copy the complete revised instructions from **View changes**. Save them as UTF-8 plain text in `.lab/lab-en/candidate.txt`. Do not include diff `+`/`-` markers, UI explanations, or scores. If you edit the instructions, record “operator-reviewed after Agent Optimizer” and the reasons in `notes.md`. The repository's `prompts/en/candidate.txt` is an authored example, not the output of your new service run.

**Do not continually create v3, v4 and later releases.** This guide uses the next step's CLI to create one v2 for comparison, so **do not use both Promote candidate and the CLI creation command**. Experienced operators can validate explicit drafts before promotion, but that is not a hidden prerequisite for this path. Creating a version is separate from publishing it or approving activation.

<p class="share-checkpoint" id="share-optimizer"><strong>Discuss:</strong> Which instruction behavior changed, what should improve, and what could regress? Identify the actual candidate rather than copying an old screenshot.</p>

**Completion criteria:** Record real job/candidate IDs, the reviewed instruction file, and change reasons. If no candidate is worth retaining, record “keep v1; no improvement observed” and continue at 10. Do not repeatedly run the same job to manufacture improvement.

<p class="step-next no-print"><a href="#decision" data-next-step>Next: 09. Reevaluate and compare v1/v2 →</a></p>

## 09. Reevaluate and compare v1/v2 {#decision}

<a id="review"></a><a id="operate"></a>

<div class="lab-concept" data-learning-frame="decision">
<p><strong>What:</strong> Reevaluate changed instructions under the same definition and record retain v1, accept v2, or hold.</p>
<p><strong>Why:</strong> A v2 label is not improvement evidence. Consider actual errors, latency/tokens, and statistical uncertainty alongside quality.</p>
<p><strong>How · where:</strong> Prepare explicit v2 and its same-definition run in the terminal, then compare every case in Foundry Compare runs. Do not publish to production.</p>
</div>

Keep the model, tools, dataset, evaluators, and Judge fixed. Create v2 of the same Agent once from your reviewed file and preserve v1.

```bash
python -m lab --config .lab/lab-en/.env native-agent --version 2 --prompt .lab/lab-en/candidate.txt --confirm
```

Confirm `agent_name: lab-en-iq` and `version: "2"`. If a different v2 already exists or the model deployment changed, stop and preserve the original records. A new version alone does not demonstrate improvement.

Use the **same Foundry evaluation definition**. The portal's Add run previously failed with **`Unable to create data source configuration from item schema`**. This official Azure AI Projects/OpenAI Evals helper adds a real managed run to the existing definition; it is not local scoring.

| Placeholder | Where to find your value |
|---|---|
| `YOUR_PROJECT_ENDPOINT` | `AZURE_AI_PROJECT_ENDPOINT` in `.lab/lab-en/.env` |
| `YOUR_SUBSCRIPTION_ID` | The subscription ID from 01, also `AZURE_SUBSCRIPTION_ID` in that `.env` |
| `YOUR_EVALUATION_ID` | The selected `evaluation_id` from the `native-evals` output in 06 |
| `YOUR_BASELINE_RUN_ID` | That evaluation's completed version-1 `run_id`, not an Optimizer job ID |

Replace all four values and execute this single-line command. Submitting a new run incurs charges.

```bash
python scripts/add_foundry_eval_run.py --endpoint "YOUR_PROJECT_ENDPOINT" --subscription "YOUR_SUBSCRIPTION_ID" --evaluation "YOUR_EVALUATION_ID" --baseline "YOUR_BASELINE_RUN_ID" --version 2 --name candidate-v2 --out .lab/lab-en/artifacts/foundry-evaluations/candidate-v2.json
```

Confirm `status: completed` and all 12 cases. If the default 30-minute wait expires, the command returns exit code 2 with Still running. If the receipt contains a run ID, repeat the **identical command and `--out` path** to collect that run. For an unknown submission without a run ID or an existing remote name, follow [duplicate-submission recovery](troubleshooting.md#evaluation). Do not delete the receipt or rename the run to resubmit.

The helper verifies the remote thresholds, Judge, mappings, and every output item's actual version and system instructions. Historical rehearsal responses and scores cannot substitute for your new run.

In **Evaluation runs**, select both rows and **Compare runs**. Explicitly choose **v1 as Baseline**; selection order must not reverse the comparison.

<figure class="portal-shot" id="portal-evaluation-comparison">
<img src="../../web/assets/portal/en/20-evaluation-comparison.png" alt="Illustrative Compare runs layout; current v1/v2 values and statistical result are in the latest report" width="1440" height="520" loading="lazy">
<figcaption><strong>Confirm the comparison direction.</strong> This capture locates the Baseline control; it is not the current Sol measurement. Use the latest report's exact two run IDs. <a href="../../web/assets/portal/en/20-evaluation-comparison.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

The current [v2 verification](verification.md#status) publishes all 12 case responses, scores and reasons alongside the v1 control. Require no decline in all-criteria passes or either metric's pass count/mean, and at least one strict measured improvement. Check factual truth, routing and response format too. Report latency, tokens and the native statistical conclusion separately.

<p class="share-checkpoint" id="share-optimized"><strong>Explain the result:</strong> Identify the actual gain, unchanged criteria, any regression, and the remaining uncertainty. Observed improvement is not a guarantee that every future stochastic run will improve.</p>

In `notes.md`, record v1/v2 pass counts and means per metric, errors, latency/tokens, statistical results, and your decision side by side. If improvement criteria are not met, **retain v1 or hold the decision**. Do not adopt a candidate with actual policy errors merely because generic evaluators passed it.

**Completion criteria:** Record the two actual run IDs, complete same-criteria comparison, and the reasons for accepting, retaining, or holding. Do not accumulate release numbers. Production approval and independent generalization are separate and are not granted by this dev12 exercise.

<p class="step-next no-print"><a href="#cleanup" data-next-step>Next: 10. Save results and delete resources →</a></p>

## 10. Save results and delete resources {#cleanup}

<a id="troubleshooting"></a><a id="sources"></a>

<div class="lab-concept" data-learning-frame="cleanup">
<p><strong>What:</strong> Preserve results, then remove your lab resources or hand them to an approved retention owner.</p>
<p><strong>Why:</strong> Search and logs can remain after the browser closes. Deleting the wrong shared group can also remove someone else's resources.</p>
<p><strong>How · where:</strong> Verify exact targets, ownership, and authorization in Azure Portal and the terminal, then verify absence after deletion. The pictured confirmation dialog is unsubmitted.</p>
</div>

**Closing a browser, deleting an Agent, or running `cleanup` does not by itself stop all resource-group charges.**

### Preserve records before deletion {#cleanup-records}

1. Record the actual project, Agent, dataset version/hash, evaluation/run/job IDs, and decision in `notes.md`.
2. Use **Download/Export** where offered in the evaluation and Optimizer views. If unavailable, retain existing receipts and detailed results; do not claim an export you could not obtain.
3. Retain `.lab/lab-en/` plans, manifest, approvals, and run records in an organization-approved private location. Do not commit raw credentials, cookies, signed URLs, or account details. Public records should contain only the necessary synthetic cases, scores, and reasons.
4. Inspect Evaluations and Optimization runs for active jobs. Use **Cancel** where supported and verify the terminal state. Hand unresolved active jobs to the cleanup owner.

### Distinguish dedicated and shared environments {#cleanup-scope}

| Environment | Cleanup scope |
|---|---|
| Dedicated resource group created for you in 02 | Follow the group-deletion procedure below. Reconfirm that no unrelated resources are present and deletion is authorized. |
| Operator-provided shared project | **Do not delete the resource group, Foundry resource, shared models, or Search service.** Remove only assigned objects and hand remaining resources to the operator. |
| Setup or execution stopped partway through | Compare `config.json`, the manifest, and actual Azure resources. Failure does not mean nothing was created. |

For shared resources with local ownership records, first inspect this **plan-only** command:

```bash
python -m lab --config .lab/lab-en/.env cleanup
```

Read `mode: LOCAL_PLAN_ONLY`, `actions`, `never_deleted`, and `manual_follow_up`. Verify names, project, and ownership. Run the following only after obtaining authorization for exactly those deletions. If your environment name differs, use its matching prefix.

```bash
python -m lab --config .lab/lab-en/.env cleanup --confirm-prefix lab-en
```

Confirm `OWNED_OBJECTS_ABSENT`. This removes recorded Agent versions, search objects, and connections, but **not resource groups, model deployments, Search hosting, logs, or RBAC**. It does not automatically remove every portal-created dataset, evaluation, Optimizer job, Playground conversation, or model-smoke response. Delete authorized items individually in their owning view; if no delete action is offered, hand retention or project cleanup to the operator.

### Delete a dedicated group and verify its absence {#cleanup-delete}

Replace `YOUR_LAB_RESOURCE_GROUP` with **`names.resource_group`** from `config.json`. Verify subscription, ownership tags, and the entire inventory, not just a familiar prefix.

```bash
az group show --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP" --query "{name:name,location:location,tags:tags}" -o json
az resource list --subscription "YOUR_SUBSCRIPTION_ID" --resource-group "YOUR_LAB_RESOURCE_GROUP" --query "[].{name:name,type:type}" -o table
```

**Resource-group deletion is irreversible and removes the group's Foundry resources, model deployments, Search, and monitoring together.** After saving evidence and receiving approval for that exact group, choose one method:

1. **Portal:** Azure Portal → Resource groups → exact group → **Delete resource group**. Read the deletion inventory, type the requested group name, and confirm.
2. **CLI:** Run the command below and review the target again at the confirmation prompt. Do not append `--yes` to bypass confirmation.

<figure class="portal-shot" id="portal-delete-review">
<img src="../../web/assets/portal/en/28-delete-review.png" alt="Actual pre-deletion review for the English lab group showing the resource inventory, empty name-confirmation field, and disabled Delete button." width="1440" height="1000" loading="lazy">
<figcaption><strong>Read the proposed inventory and confirmation field first.</strong> Compare the group and every resource above, then locate Enter resource group name to confirm deletion below. “Resources being deleted” describes the proposed list, not completed deletion. During capture, the field remained empty, Delete stayed disabled, and the pane was closed with Cancel. Execute deletion only after authorization. <a href="../../web/assets/portal/en/28-delete-review.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

```bash
az group delete --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP"
```

An accepted request is not completed deletion. Check portal notifications and group status, then verify that this command successfully prints **`false`**:

```bash
az group exists --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP"
```

Authentication or network errors are not `false` and do not prove deletion. If `true`, inspect deletion progress. For **Locks**, permissions, or dependencies in other groups, follow [deletion troubleshooting](troubleshooting.md#cleanup). Do not remove organizational locks without authorization.

Afterward, open **Cost Management → Cost analysis** for the subscription, time range, and group. Billing updates can lag, and earlier usage charges do not disappear. Separately check logs/storage in other groups and service-specific soft-deleted resources. Permanent deletion/purge requires organizational policy and separate authorization.

**Final completion criteria:** Verify the dedicated group's absence and record the time, or hand over a shared-resource inventory with reasons, owner, and retention deadline. Do not delete `.lab` first and lose ownership evidence. See the [operator cleanup worksheet](admin-setup.md#cleanup) and [execution issue record](troubleshooting.md#verification) for the remaining boundaries.
