# Evaluate and improve a customer-support Agent · v1 {#좋은-에이전트는-평가에서-시작된다-v1}

<p class="eyebrow">CONTOSO ATLAS CLOUD · ONE LEARNING PATH</p>

**Score a support AI on 12 questions, improve its instructions, then compare its answers to the same questions.** No Azure or Foundry experience is required. You do need to install tools on your computer and have an Azure environment with access and cost authorization.

**Azure** is Microsoft's cloud platform. **Microsoft Foundry** is the platform for building and evaluating AI models and Agents on Azure. An **Agent** combines a model with instructions and tools. Here, a fictional **Contoso Atlas Cloud support Agent** searches policy documents before answering.

<div class="hero-summary" aria-label="Lab purpose and outcomes">
<div><strong>WHAT YOU BUILD</strong><span>A support Agent that answers using policy evidence.</span></div>
<div><strong>WHY IT MATTERS</strong><span>Judge quality from 12 answers and scoring reasons, not one convincing answer.</span></div>
<div><strong>HOW YOU PROCEED</strong><span>Keep questions, models, and scoring criteria fixed; change only instructions.</span></div>
<div><strong>WHAT YOU KEEP</strong><span>A before/after comparison, your decision, and resource-cleanup records.</span></div>
</div>

<p class="step-next no-print"><a href="#setup">Start with step 01 →</a></p>

**First, find your starting point.** The operator is the person responsible for the environment, access, and cost. For a solo lab, that is you or your organization's Azure administrator.

| Your situation | Your path |
|---|---|
| A facilitator or operator provided the environment | Complete your identity/computer checks in 01. Use the [handoff](admin-setup.md#handoff) to verify 02–03 and agree who runs commands, then continue at 04. Do not repeat creation. |
| You have an authorized subscription and will create the environment | Follow 01–10. An authorized person performs the resource creation and access configuration in 02. |
| You have no assigned subscription/project or cost authorization | Do not start Azure creation or calls. Send the [operator preparation guide](admin-setup.md#start) to the responsible person. |

**Time and cost:** Allow half a day when starting from scratch, plus any permission/quota approval wait. Prepared environments still need evaluation/optimization waiting time. Model calls, Search, and logs can incur charges. **Closing your browser does not end those charges; finish the cleanup in 10.**

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

Here, **learning means reading evaluation results and improving instructions**, not retraining model weights. Use only the supplied synthetic policies and questions. Do not upload private customer records or put the test answers into the instructions.

| Where you work | What you do there |
|---|---|
| [Azure Portal](https://portal.azure.com) | Verify identity, subscription, permissions, actual resources, and deletion scope. |
| Your computer's terminal | The window where you prepare files and run supplied commands. Step 01 explains how to open it. |
| [Microsoft Foundry](https://ai.azure.com) | Inspect the project, Agent, and policy tool; run evaluations and Optimizer; read comparisons. |

**How to read a step:** Follow the explanation, actions, then **completion criteria**. Keep Azure Portal and Foundry open in separate browser tabs. Match controls by their English UI names. **Use your own account/project values, not the names in the illustrations.**

Steps 01–03 prepare the environment, 04–09 evaluate and improve, and 10 cleans up. **Steps 04–06 continue in the same evaluation wizard.** Do not create a separate evaluation for each step. Reading marks are personal bookmarks, not evidence of completed operations.

**V1 is the original Agent; v2 is the candidate with revised instructions.** These are complete Agent versions. Keep their models, tools, and output format fixed. Retaining v1 when no improvement is found is a valid lab outcome; creating v2 is not production approval.

## 01. Check your account, computer, and access {#setup}

<a id="environment"></a><a id="sdk-prerequisites"></a>

<div class="lab-concept" data-learning-frame="setup">
<p><strong>What:</strong> Confirm the Azure subscription, access, and local execution environment.</p>
<p><strong>Why:</strong> Different browser and CLI identities can cause access failures or create resources in the wrong environment.</p>
<p><strong>How · where:</strong> Check subscription/access in Azure Portal, then compare tools, login, and language settings in the terminal. No Azure resources are created yet.</p>
</div>

<div class="concept-primer" id="basics" role="group" aria-label="Azure terms for first-time participants">
<p><strong>Six terms to recognize before opening the portal.</strong> You do not need to memorize them; distinguish their roles.</p>
<dl>
<div><dt>Tenant / Directory</dt><dd>The boundary that manages an organization's users and access. One account can access several organizations, so check the selected directory too.</dd></div>
<div><dt>Subscription</dt><dd>The unit that groups Azure usage and billing. Confirm which subscription will pay for this lab.</dd></div>
<div><dt>Resource group</dt><dd>A group of Azure resources managed together. A dedicated lab group makes the eventual deletion scope easier to identify.</dd></div>
<div><dt>Project</dt><dd>The Foundry workspace for your Agents, data, and evaluations. Stay in the same project throughout the lab.</dd></div>
<div><dt>Model</dt><dd>The AI that generates answers. Deploying makes a model available to call; the deployment name identifies that callable deployment.</dd></div>
<div><dt>Role / Scope</dt><dd>A role defines allowed actions; its scope defines where they apply. Signing in does not automatically grant creation, evaluation, and deletion access.</dd></div>
</dl>
</div>

### Confirm your Azure account and subscription {#setup-account}

1. Sign in to the [Azure portal](https://portal.azure.com) with **your own account assigned for this lab**. A prepared class does not require creating another account or subscription. Only if you have no account, follow the [Azure account instructions](https://azure.microsoft.com/pricing/purchase-options/azure-account); request approved subscription access for an organization account.
2. Search for **Subscriptions** in the top search box and open the intended subscription. Confirm portal status **Active** and record its **Subscription ID** and **Directory/Tenant ID**. The CLI describes the same usable subscription as **Enabled**. If it is missing, check directory and subscription filters under your account.
3. Open the permissions menu **Access control (IAM) → Check access** and inspect your role and scope. Older UI versions may label this **View my access**. The person creating the environment needs both resource-creation and role-assignment authority. Participants using a prepared environment do not need those same creation privileges. See [access by responsibility](admin-setup.md#rbac).
4. Agree on a budget, end time, and cleanup owner. Do not create resources without subscription access and cost authorization. Do not grant new subscription-wide Owner access or disable organizational security controls as a shortcut.

<figure class="portal-shot" id="portal-subscription-overview" data-capture-scope="shared">
<img src="../../web/assets/portal/shared/21-subscription-overview.png" alt="Azure subscription Overview with Subscription ID, Directory, Status, and My role under Essentials." width="1440" height="347" loading="lazy">
<figcaption><strong>Check the subscription and status.</strong> Find Subscription ID, Directory, Status, and My role under Essentials. Portal <strong>Active</strong> and CLI <strong>Enabled</strong> describe the same usable state. <a href="../../web/assets/portal/shared/21-subscription-overview.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-check-access" data-capture-scope="shared">
<img src="../../web/assets/portal/shared/22-check-access.png" alt="Access control IAM Check access page showing active roles and their scopes." width="1440" height="850" loading="lazy">
<figcaption><strong>Read the role and its scope together.</strong> Open Access control (IAM) → Check access and inspect your active assignments. Confirm where each role applies; do not add broader access than the task requires. <a href="../../web/assets/portal/shared/22-check-access.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

### Install tools and download the lab {#setup-local}

Install [Python](https://www.python.org/downloads/) **3.11–3.14**, [Git](https://git-scm.com/downloads), and the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli). Python runs the supplied programs, Git downloads the lab, and Azure CLI provides the `az` sign-in/query commands. Request administrator help if your work computer restricts installation.

**If the tools are already installed, start with [installation checks](#setup-verify) and do not reinstall working tools.** The Windows/macOS examples below explicitly select **3.13** so an unsupported newer Python is not selected. If you already use another supported version, replace `py -3.13` or `python3.13` with its version-specific command, using the same Python for verification and virtual-environment creation. Python 3.10 or earlier and 3.15 or later are outside this lab's supported range.

First open **your computer's terminal**. Search for **PowerShell** in Windows Start, **Terminal** in macOS Spotlight, or the terminal in your Linux app menu. This guide does not run in Azure Portal's Cloud Shell or the Python prompt showing `>>>`.

**Reading commands:** Run **one command at a time** and wait for it to finish. A long command can wrap across screen/PDF lines; do not insert a line break within that command.

Copy buttons copy the **whole block**. If it contains several commands, paste into an editor first and run them individually. Replace `YOUR_...` with your value, preserving the surrounding double quotes.

Blocks labeled `Shared terminal` work on all operating systems. For `macOS/Linux` or `PowerShell` blocks, read the preceding description and **run only the blocks for your OS**. **Stop at an error instead of running the next command**, and use that step's troubleshooting link.

Follow one of [Windows installation](#setup-windows), [macOS installation](#setup-macos), or [Linux installation](#setup-linux), then continue to [installation checks](#setup-verify).

#### Windows · install in PowerShell {#setup-windows}

Run `winget --version` in PowerShell. If it prints a version, use the Windows package manager **WinGet** to run the following commands one at a time. Personally review installation agreements and administrator prompts within your organization's authorization.

```powershell
winget install --exact --id Python.Python.3.13 --source winget
winget install --exact --id Git.Git --source winget
winget install --exact --id Microsoft.AzureCLI --source winget
```

**If WinGet is missing or unavailable, use the official installers instead.** You do not need to use both methods.

| Tool | Download and installer choices |
|---|---|
| Python | From [Windows downloads](https://www.python.org/downloads/windows/), choose the **latest Python 3.13 patch release** and an installer matching your computer. Use the regular installer, not the embeddable package; select **Add python.exe to PATH** and include **pip and the Python Launcher**. |
| Git | Download the appropriate installer from [Git for Windows](https://git-scm.com/install/windows). Keep **Git from the command line and also from 3rd-party software** on the PATH selection screen so Git works in PowerShell. |
| Azure CLI | Follow **Microsoft Installer (MSI)** in the [official Windows instructions](https://learn.microsoft.com/cli/azure/install-azure-cli-windows?pivots=msi). Choose the 64-bit MSI for a typical x64 computer. |

Continue to [checking all three tools in a new terminal](#setup-verify). If `py` is not recognized, check the Python installer's Launcher option.

#### macOS · install with Homebrew {#setup-macos}

Run `brew --version` in Terminal. If the command is missing, follow the [official Homebrew installation instructions](https://brew.sh/), complete the PATH configuration printed under **Next steps**, then check again in a new terminal. Do not bypass your organization's software or Command Line Tools approval process.

```bash
brew update
brew install python@3.13 git azure-cli
```

This uses [Homebrew's versioned Python package](https://formulae.brew.sh/formula/python@3.13) and [Microsoft's macOS Azure CLI instructions](https://learn.microsoft.com/cli/azure/install-azure-cli-macos). **Use `python3.13` for this path.** An existing `python3` can still point to macOS's system Python or another version; do not overwrite or forcibly relink the system interpreter.

#### Linux · Ubuntu 24.04 LTS example {#setup-linux}

The following targets **Ubuntu 24.04 LTS**, which provides Python 3.12 by default. For another distribution, follow its Python instructions, [Git installation guidance](https://git-scm.com/install/linux), and [official Azure CLI installation instructions](https://learn.microsoft.com/cli/azure/install-azure-cli-linux). If Python is outside the supported range, request a supported execution environment rather than replacing the system interpreter.

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git curl
curl -fsSL 'https://azurecliprod.blob.core.windows.net/$root/deb_install.sh' -o install-azure-cli.sh
```

The last command **only downloads** [Microsoft's Ubuntu/Debian installation script](https://learn.microsoft.com/cli/azure/install-azure-cli-linux?pivots=apt). Open `install-azure-cli.sh` in a text editor and inspect it before running the following command with authorization to install system packages. Ask your administrator to perform the installation if you do not have `sudo` access.

```bash
sudo bash install-azure-cli.sh
```

#### Verify installation in a new terminal {#setup-verify}

**After installation, close all existing terminal windows and open a new one.** PATH is the list of locations used to find commands; an existing window might not receive the newly installed paths. If you use VS Code's terminal, exit and reopen VS Code too.

**Windows PowerShell:**

```powershell
py -3.13 --version
git --version
az version
```

**macOS · the Homebrew path above:**

```bash
python3.13 --version
git --version
az version
```

**Linux · the Ubuntu path above:**

```bash
python3 --version
git --version
az version
```

| Check | Expected output and requirement |
|---|---|
| Lab Python | A version such as `Python 3.13.x`; `x` is the actual patch number. The minor version must be **3.11, 3.12, 3.13, or 3.14**. |
| Git | An installed version such as `git version 2.x...`. |
| Azure CLI | JSON containing a version such as `"azure-cli": "2.x..."`. **This check does not require Azure sign-in.** |

Python information in `az version` describes Azure CLI's own runtime, not verification of the lab's Python installation. **All three commands must succeed before** downloading the lab or creating its virtual environment. For `command not found`, `not recognized`, or Microsoft Store opening instead of Python, see [installation and PATH troubleshooting](troubleshooting.md#environment).

#### Download the lab files {#setup-download}

```sh
git clone https://github.com/junwoojeong100/foundry-evaluation-labs-v1.git
cd foundry-evaluation-labs-v1
```

If you already downloaded the repository, enter its folder rather than cloning it again. With GitHub **Code → Download ZIP**, extract the archive first and open the folder containing `pyproject.toml` and `requirements.lock`. Downloading only an HTML file omits the code, data, and images.

#### Create a virtual environment with the verified Python {#setup-venv}

Run subsequent commands from the **lab folder containing `pyproject.toml` and `requirements.lock`**. `.venv` is an isolated Python package environment for this lab. Create it with **the same Python you verified above**, running only the one path matching your operating system.

**macOS · the Homebrew path above:**

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

**Linux · the Ubuntu path above:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**In Windows PowerShell, run:**

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell policy blocks activation, do not change organizational policy. Replace `python` in subsequent commands with `.\.venv\Scripts\python.exe`. If `.venv` already exists, confirm that it belongs to this lab rather than overwriting another task's environment.

**After preparing the virtual environment, run these shared commands.** Confirm Python 3.11–3.14 and a pip path inside `.venv` from the first two commands before installing packages.

```sh
python --version
python -m pip --version
python -m pip install -r requirements.lock
python -m lab --help
python scripts/build_datasets.py --language en --check
```

Confirm that the command list appears and the dataset check succeeds. For `ModuleNotFoundError`, use `python -m pip --version` to check that Python and pip belong to `.venv`. Do not install packages into an unrelated system interpreter.

### Pin the CLI identity and lab language {#setup-login}

First replace `YOUR_SUBSCRIPTION_ID` below with the subscription ID you recorded. Sign in with **the same account** in the browser opened by `az login`, then return to the terminal.

```sh
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

**Prepared environment:** Agree on your responsibilities using the [handoff](admin-setup.md#handoff). If command-line/Python access has not been configured for your own account, the operator performs setup in 02–03, ID lookup in 06, and commands in 09, then supplies the results. Do not copy the operator's `.env` or sign-in session.
{: .note}

**Completion criteria:** Python 3.11–3.14, Git, and Azure CLI versions are verified; the user, tenant, and subscription match; the virtual environment's Python commands and English dataset check succeed. For blockers, see [environment troubleshooting](troubleshooting.md#environment).
{: .completion-check}

<p class="step-next no-print"><a href="#resources" data-next-step>Next: 02. Create the Foundry environment →</a></p>

## 02. Create the Foundry environment {#resources}

<a id="first-infrastructure-failure"></a>

<div class="lab-concept" data-learning-frame="resources">
<p><strong>What:</strong> Prepare a Foundry project, models, Search, and monitoring in a dedicated resource group.</p>
<p><strong>Why:</strong> The group bounds cost and cleanup; the project organizes Agents and evaluations. An empty project alone does not provide policy retrieval.</p>
<p><strong>How · where:</strong> Plan, authorize, and provision from the terminal, then compare both portals with the outputs. Reuse a prepared environment instead of creating duplicates.</p>
</div>

**Do not run creation commands for an already prepared environment.** Compare the hierarchy below, actual portal values, and completion evidence for 02–03 with the handoff, then continue at [04](#start).
{: .note}

<figure class="concept-flow" id="resource-map" aria-label="Containment from Azure subscription to Foundry project">
<ol>
<li><strong>Azure subscription</strong><span>Usage and billing</span></li>
<li><strong>Resource group</strong><span>This lab's resources</span></li>
<li><strong>Foundry resource</strong><span>AI service and deployments</span></li>
<li><strong>Project</strong><span>Agents, data, evaluations</span></li>
</ol>
<figcaption>Each item contains the next. The same lab group also contains <strong>Azure AI Search</strong> for policy retrieval and <strong>Application Insights / Log Analytics</strong> for execution records.</figcaption>
</figure>

An **endpoint** is the address a program uses to connect to a service. Use the project's **Project endpoint** for this lab, not the adjacent Azure OpenAI endpoint.

### Create a local provisioning plan {#resources-plan}

Replace the placeholders with the values recorded in 01. An **ID identifies a resource; it is not its display name**. Do not enter a subscription name in an ID field.

| Placeholder | Your value |
|---|---|
| `YOUR_SUBSCRIPTION_ID` | `subscription` from `az account show` |
| `YOUR_TENANT_ID` | `tenant` from the same output |
| `YOUR_SIGN_IN_NAME` | `user` from the same output |

This command writes only a plan and unapproved authorization example under `.lab/lab-en/` on your computer; it does not call Azure.

```sh
python -m lab bootstrap plan --subscription "YOUR_SUBSCRIPTION_ID" --tenant "YOUR_TENANT_ID" --expected-user "YOUR_SIGN_IN_NAME" --environment lab-en --location northcentralus
```

Confirm `plan_status: CREATED_LOCAL_ONLY`, `mutations_performed: false`, and `config_path`. `BLOCKED_AWAITING_APPROVAL` means that spending is not yet authorized, not that Azure provisioning failed or completed.

| Generated file | What to check |
|---|---|
| `.lab/lab-en/config.json` | Identity, generated resource names, and exact model/version/capacity selections. Do not edit this hashed plan. |
| `.lab/lab-en/approval.example.json` | The initially unapproved cost and change scope. |
| `.lab/lab-en/manifest.json` | Provisioning, ownership, and interruption records. Preserve this file. |
| `.lab/lab-en/.env` | Not present yet. Successful provisioning creates this runtime configuration. |

Use your text editor's **Open file** action to inspect these files. `.lab` stores lab records and may appear as a hidden folder. JSON stores settings as name/value pairs. Do not convert these files to Word documents or change their extensions.

The model roles are **answer generation (Agent), scoring (Judge), instruction suggestions/search planning (Optimizer/planner), and numerical representations for search (embedding)**. You do not develop a new model in this lab.

This repository's setup region is **North Central US (`northcentralus`)**. Defaults are Agent `gpt-6-sol`, Judge `gpt-6-luna`, Optimizer/search planner `gpt-5.5`, and embedding `text-embedding-3-small`. Check the exact versions, SKUs (deployment types), and capacity units in the [model table](admin-setup.md#prepare) and plan. Do not silently substitute a different region or model.

### Allocate the recommended minimum TPM {#resources-tpm}

**TPM (Tokens Per Minute) is a per-deployment token rate limit**, not the model's context window or guaranteed processing speed. These starting requirements cover **one environment running one 12-case evaluation or Optimizer job at a time**. They are recommended minimums with headroom for evaluation/retrieval calls, not proven absolute lower bounds or a guarantee against 429 errors.

| Role/model | Recommended minimum TPM to start | ARM capacity in a new default plan |
|---|---:|---:|
| Agent · `gpt-6-sol` | **100,000** | 100 |
| Judge · `gpt-6-luna` | **100,000** | 100 |
| Optimizer / search planner · `gpt-5.5` | **100,000** | 100, one deployment shared by both roles |
| Embedding · `text-embedding-3-small` | **10,000** | 10 |

New `bootstrap plan` output requests these capacities. **ARM units depend on the model/SKU**; do not universally multiply capacity by 1,000. After deployment, confirm actual TPM with runtime preflight below. Unallocated subscription quota does not establish that an individual deployment has enough TPM assigned.

Existing plans and deployments are not automatically increased. For a prepared environment, follow the [operator TPM setup instructions](admin-setup.md#throughput) within its authorization. Do not edit `config.json`, approval hashes, or the manifest to bypass checks.

**Shared users or overlapping jobs require additional capacity.** Azure rate-limits estimated tokens based on inputs and maximum-output settings, not only billed tokens. **RPM (Requests Per Minute)** and short-window request bursts are separate constraints. See the [official TPM/RPM explanation](https://learn.microsoft.com/azure/foundry/openai/how-to/quota#understanding-rate-limits).

### Check readiness and obtain cost authorization {#resources-approval}

```sh
python -m lab bootstrap preflight --config .lab/lab-en/config.json
```

**Preflight checks readiness before execution.** Look for `readiness_status: READY`. Quota is your subscription's allowed usage; capacity is actual availability in a region. If blocked, read `reason` and follow [provisioning troubleshooting](troubleshooting.md#provisioning). Without an approval file, the overall status can still await approval even when readiness is READY. Do not keep creating new environments or switching regions.

The actual budget owner opens `.lab/lab-en/approval.example.json` in an editor and uses **Save As** to create `.lab/lab-en/approval.json`. Keep the original `scope_sha256`, `models`, and `retention_days`. Complete **every field in the [approval worksheet](admin-setup.md#approval)** according to the real authorization, including approver, currently valid timestamps, currency/budget, wait/hosting bounds, and resource/RBAC/global-processing consent.

Changing only `approved` to `true` is insufficient. The budget value is not an Azure spending cutoff, and a documentation example is not spending authorization.

```sh
python -m lab bootstrap preflight --config .lab/lab-en/config.json --approval .lab/lab-en/approval.json
```

**Proceed only when both `readiness_status: READY` and `status: READY_FOR_APPROVED_APPLY` are present.**

### Provision and confirm the resources in the portal {#resources-create}

```sh
python -m lab bootstrap apply --config .lab/lab-en/config.json --approval .lab/lab-en/approval.json
python -m lab bootstrap status --config .lab/lab-en/config.json --approval .lab/lab-en/approval.json
```

The first command creates resources, deployments, connections, and resource-scoped roles. It can take time; do not launch a second `apply` in another terminal. Confirm **APPLIED**, a generated `.lab/lab-en/.env`, and `status` showing `phase: succeeded` with the expected resources present. After a timeout, inspect `status` first and follow the [resume procedure](troubleshooting.md#provisioning).

1. In [Azure Portal](https://portal.azure.com) → **Resource groups**, search for `names.resource_group` from `config.json`. Confirm the subscription, region, and complete resource list.
2. Open [Foundry](https://ai.azure.com) with **New Foundry** enabled. If **Select a project to continue** appears, choose `names.project` and select **Let's go**. Read and **Close** the welcome tour if shown. If already in New Foundry, use the upper-left project selector. Do not use a Classic hub-based project.
3. In the project's **Home** (Overview in some layouts), find **Project endpoint**. It must match `AZURE_AI_PROJECT_ENDPOINT` in `.env`, in the form `https://account.services.ai.azure.com/api/projects/project`.
4. In **Models + endpoints** or **Build → Models**, locate the deployments matching `.env` values `MODEL_DEPLOYMENT`, `JUDGE_DEPLOYMENT`, `OPTIMIZER_DEPLOYMENT`, and `EMBEDDING_DEPLOYMENT`. See [portal orientation](admin-setup.md#prepare) if labels differ.

<figure class="portal-shot" id="portal-created-resources">
<img src="../../web/assets/portal/en/23-resource-group.png" alt="Resource group Overview showing Foundry, project, Search, monitoring resources, and deployment status." width="1440" height="1000" loading="lazy">
<figcaption><strong>Compare the plan with actual resources.</strong> Check the group name and Location, then identify Foundry, Foundry project, Search, Application Insights, and Log Analytics. Open Deployments to inspect each deployment's status and any failure details. <a href="../../web/assets/portal/en/23-resource-group.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-select-project" data-capture-layout="dialog">
<img src="../../web/assets/portal/en/24-select-project.png" alt="New Foundry project-selection dialog with the project selector and Let's go button." width="640" height="474" loading="lazy">
<figcaption><strong>Select the project you prepared.</strong> Compare its name with <code>names.project</code> and open it with Let's go. This selects an existing project; it does not create another. After bootstrap, do not use Create a new project to duplicate the environment. <a href="../../web/assets/portal/en/24-select-project.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-project-endpoint">
<img src="../../web/assets/portal/en/25-project-overview.png" alt="Foundry project Home with the project selector, View deployments, Project endpoint, and Azure OpenAI endpoint." width="1440" height="492" loading="lazy">
<figcaption><strong>Check the project and endpoint.</strong> Compare the upper-left project name and <strong>Project endpoint</strong> with your configuration. Do not substitute Azure OpenAI endpoint. Open the model list through View deployments. <a href="../../web/assets/portal/en/25-project-overview.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

```sh
python -m lab --config .lab/lab-en/.env preflight
```

Inspect `agent_tpm`, `judge_tpm`, `optimizer_tpm`, `iq_planner_tpm`, and `embedding_tpm` under `checks`. Each `observed` value is actual deployment TPM; `expected` is the recommended minimum above. Insufficient or unverifiable token limits report `BLOCKED`: do not continue to model calls. Prepare the allocation, then rerun the same read-only preflight.

**Completion criteria:** Runtime preflight and all five TPM checks report `PASS`; your project and role-specific deployments are present. This is read-only configuration evidence. The next step verifies actual model responses.
{: .completion-check}

<p class="step-next no-print"><a href="#agent" data-next-step>Next: 03. Connect policies and create the Agent →</a></p>

## 03. Connect policies and create the Agent {#agent}

<a id="model-smoke"></a><a id="iq"></a>

<div class="lab-concept" data-learning-frame="agent">
<p><strong>What:</strong> Connect a read-only synthetic-policy tool to the pinned v1 baseline Agent.</p>
<p><strong>Why:</strong> Recalling a policy is not the same as retrieving it. Retrieval under your user identity does not establish access for the Agent's managed identity.</p>
<p><strong>How · where:</strong> Prepare model, retrieval, and Agent from the terminal; inspect instructions, tools, and an actual response in Foundry. Transmit data and make calls once within the approved scope.</p>
</div>

### Verify the model and policy retrieval {#agent-knowledge}

**These three commands perform actual uploads/model calls and can incur charges.** For a prepared environment, obtain the operator's verified results instead of repeating them. When preparing your own environment, check each result before continuing.
{: .note .warning}

**1. Verify that the model responds.** `smoke` is a short functional check.

First pass the [TPM checks in 02](#resources-tpm). One successful short response does not establish sufficient throughput for the full evaluation.

```sh
python -m lab --config .lab/lab-en/.env smoke --run-id model-smoke --confirm
```

Confirm **`status: completed`** in the output.

**2. Prepare policy retrieval.** Upload the [eight supplied synthetic policies](../../data/en/knowledge/documents.json) to the search service.

```sh
python -m lab --config .lab/lab-en/.env iq prepare --confirm
```

Confirm **`uploaded_documents: 8`**. The program prepares a search index (searchable documents), a knowledge base, and an MCP connection through which the Agent calls retrieval. You do not need to edit the implementation.

**3. Verify that a query retrieves policies.**

```sh
python -m lab --config .lab/lab-en/.env iq probe --confirm
```

Confirm **`status: retrieval_verified`** with nonempty references. `created_not_retrieval_tested` means creation only. If an error occurs, preserve the records and follow [retrieval troubleshooting](troubleshooting.md#knowledge).

In the portal, open **Build → Knowledge → Knowledge bases** and inspect Connection, the created knowledge base, and Knowledge sources. One knowledge-base row does not mean there is only one policy document.

<figure class="portal-shot" id="portal-policy-connection">
<img src="../../web/assets/portal/en/26-knowledge-base.png" alt="Knowledge Foundry IQ page with Connection, knowledge-base name, Knowledge sources, and Active status." width="1440" height="374" loading="lazy">
<figcaption><strong>Confirm the policy connection.</strong> Inspect Connection, Knowledge sources, and Active for the intended base. Active is registration state; verify actual retrieval with <code>iq probe</code>. The free-retrieval banner does not make the whole lab free, and setup inspection does not require changing the billing plan. <a href="../../web/assets/portal/en/26-knowledge-base.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

### Create v1 with the fixed comparison configuration {#agent-create}

```sh
python -m lab --config .lab/lab-en/.env native-agent --version 1 --confirm
```

This creates **`lab-en-iq` version `1`** using the instructions in `prompts/en/baseline.txt` and the verified policy tool. Record `agent_name`, `version`, and `receipt`. A **receipt is a file recording the operation's result**. The command reuses an identical v1 in the same owned workspace; it does not adopt another Agent or create v3.

<figure class="portal-shot" id="portal-agent-configuration">
<img src="../../web/assets/portal/en/27-agent-configuration.png" alt="Agent Playground with Version, Model, Instructions, connected Knowledge, and Chat controls." width="1440" height="1000" loading="lazy">
<figcaption><strong>Check version, instructions, and Knowledge.</strong> Select Version 1, inspect Model and Instructions on the left, and confirm the policy MCP connection under Knowledge. Enter your question in Chat on the right. <a href="../../web/assets/portal/en/27-agent-configuration.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

In the portal, open **Build → Agents → lab-en-iq → version 1**. Use the command's actual Agent name. Send this one question in **Test/Playground**:

> I first purchased a monthly subscription in September 2026. What are the refund application conditions?

The reply is **JSON with four fields**, not just a chat sentence. Braces and quotation marks are expected, not an error.

| Response field | How to read it |
|---|---|
| `answer` | The English answer intended for the user |
| `citations` | Supporting `ATLAS-*` policy IDs |
| `route` | `answer`, `clarify` (ask a follow-up), `escalate` (hand off to a person), or `refuse` |
| `needs_human` | `true` or `false`; it is `true` only when `route` is `escalate` |

Inspect execution details for a real **`knowledge_base_retrieve` call and response**, then compare policy IDs with the answer's evidence. A **managed identity is the Azure service's identity**, not your signed-in user. Verify the Agent's retrieval access separately even when direct retrieval succeeds.

**Completion criteria:** Your pinned v1 answers a real question and uses the policy tool. Connection success or valid JSON alone is not measured quality. Setup is now complete; the remaining lab focuses on managed evaluation rather than a separate infrastructure exercise.
{: .completion-check}

<p class="step-next no-print"><a href="#start" data-next-step>Next: 04. Register the dataset →</a></p>

## 04. Register the dataset {#start}

<a id="demo"></a><a id="understand"></a><a id="data"></a>

<div class="lab-concept" data-learning-frame="start">
<p><strong>What:</strong> Register the English dev12 file once so both versions receive the same questions.</p>
<p><strong>Why:</strong> Changing questions or reference answers obscures the instruction change. Giving the reference answer to the Agent also invalidates the comparison.</p>
<p><strong>How · where:</strong> Check count/hash in the terminal, then register the original file or reuse its exact version in the Foundry evaluation wizard.</p>
</div>

<p class="wizard-context" data-wizard-step="1"><strong>Part 1 of the same evaluation wizard.</strong> 04 selects data → 05 sets scoring criteria → 06 submits. Do not select Submit yet.</p>

A **dataset is the collection of test questions**. Use **[data/en/optimizer/dev.jsonl](../../data/en/optimizer/dev.jsonl)**: **12 JSONL rows**, called **dev12** for short. Each line is one test case in JSON format. Do not edit it or convert it to Excel, CSV, or a JSON array.

```sh
python -c "import hashlib,pathlib; p=pathlib.Path('data/en/optimizer/dev.jsonl'); print('rows =',len(p.read_text(encoding='utf-8').splitlines())); print('sha256 =',hashlib.sha256(p.read_bytes()).hexdigest())"
```

Record `rows = 12` and SHA-256 in your private notes. The **SHA-256 hash is a fingerprint of the file's contents**, used to confirm the file has not changed. Copy the output; you do not need to memorize or type it manually.

| Column | Type | Use |
|---|---|---|
| `query` | String | The only Agent input |
| `context` | String | Policy reference for supported evaluators and case review |
| `ground_truth` | JSON string | Structured reference answer, never a generation prompt |

Only the question reaches the Agent. `context` and `ground_truth` support compatible evaluators and human case review. The other supplied dataset files are outside this required lab.

<figure class="concept-flow" id="evaluation-flow" aria-label="Flow from the question to the response and its scoring">
<ol>
<li><strong>Question · query</strong><span>One dataset row at a time</span></li>
<li><strong>Agent</strong><span>Model + instructions + retrieval</span></li>
<li><strong>Actual response</strong><span>answer and three other fields</span></li>
<li><strong>Evaluators + Judge</strong><span>Scores and reasons</span></li>
</ol>
<figcaption>The Agent searches policies through its tool. Do not append the dataset's reference answer to the Agent input. The Agent only advises; it cannot actually refund, submit, delete, or grant access.</figcaption>
</figure>

**In Foundry, follow these actions.** If the operator supplied different names, use the handoff values instead of the example names below.

1. Open **Build → Evaluations → Create → Create new evaluation**. Some layouts label the same menu **Evaluation**, singular.
2. Select target type **Agent**, **`lab-en-iq`**, and version **1**. Use **Pin currently latest** only while latest really is version 1. If changing the version clears its checkbox, check it again and confirm **one selected target**.
3. Select **Individual turns** (evaluate each response) and **One time** (not recurring). Do not select Synthetic data to generate new questions.
4. Select **Upload new dataset → Browse**, then choose `data/en/optimizer/dev.jsonl` **inside your computer's lab folder**. Name it **`lab-en-dev12`**, use first version **`1`**, and wait for registration. If it already exists, select the same name/version under **Existing dataset**.
5. Verify `query`, `context`, and `ground_truth`. A **five-row preview is not the dataset total**; the original contains 12. Record its name/version and continue to 05 in this same wizard.

<figure class="portal-shot" id="portal-evaluation-dataset">
<img src="../../web/assets/portal/en/15-evaluation-dataset.png" alt="Foundry evaluation dataset selection and preview of query, context, and ground_truth columns." width="1440" height="1000" loading="lazy">
<figcaption><strong>Select the English dataset.</strong> Confirm the registration name/version and the query, context, and ground_truth columns. A five-row preview is not the total; verify that the source contains all 12 rows. <a href="../../web/assets/portal/en/15-evaluation-dataset.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Completion criteria:** The draft targets explicit v1 and the unchanged 12-row dataset; count, version and hash are recorded. [Data contract](../../data/README.en.md#schema).
{: .completion-check}

<p class="step-next no-print"><a href="#prepare" data-next-step>Next: 05. Select evaluation criteria →</a></p>

## 05. Select evaluation criteria {#prepare}

<a id="calibration"></a>

<div class="lab-concept" data-learning-frame="prepare">
<p><strong>What:</strong> Select Relevance, TaskAdherence, and the actual Judge deployment.</p>
<p><strong>Why:</strong> Defining scales, pass rules, and mappings beforehand prevents moving the criteria after seeing results. These two evaluators use different scales.</p>
<p><strong>How · where:</strong> Open each evaluator's settings in Foundry Criteria and confirm the threshold and Judge. Send only query to the Agent.</p>
</div>

<p class="wizard-context" data-wizard-step="2"><strong>Part 2 of the same evaluation wizard.</strong> Continue from the screen left open in 04. Do not create another evaluation or select Submit yet.</p>

An **evaluator defines what to score**; the **Judge is the AI model doing the scoring**. **Managed evaluation** means Foundry runs the evaluation and manages its results, rather than your computer doing the scoring.

1. In **Configure agents**, leave the custom prompt override unset. Use **`{{item.query}}` only** as user input. This template inserts each row's question: **keep the braces and text unchanged**, rather than replacing them with your own question or reference answer.
2. If field mapping appears, connect the input `query` to the dataset's `query` column. Mapping pairs **an input field with a data column**. Do not append `context` or `ground_truth` to the Agent input.
3. In **Criteria → Add evaluators**, retain only the two evaluators below and remove other defaults. TaskAdherence can also appear as **Task Adherence**.
4. Open each evaluator's settings, set its pass rule below, and select **Apply**. Under **Evaluation model/Judge**, select the **deployment name identified by `JUDGE_DEPLOYMENT`** in your `.env` or handoff.

| Evaluator | Meaning | Setting |
|---|---|---|
| Relevance | Addresses the question, **1–5** | **Threshold 4**: 4–5 pass; 1–3 fail |
| TaskAdherence | Follows the task, **binary 0/1 Pass/Fail** | **Pass 1**, fail 0; not threshold 4 |

Preserve the service-generated `response` mappings. If a response field is **Unassigned**, or the prepared Judge is missing, request the [operator mapping check](admin-setup.md#evaluation-mapping) instead of guessing a value.

| Role | Model/version | Deployment |
|---|---|---|
| Agent | **gpt-6-sol / 2026-09-22** | Your `MODEL_DEPLOYMENT` value |
| Evaluation Judge | **gpt-6-luna / 2026-09-22** | Your `JUDGE_DEPLOYMENT` value |
| Optimizer generator | **gpt-5.5 / 2026-04-24** | Your `OPTIMIZER_DEPLOYMENT` value |

Agent, Judge, and Optimizer support can differ by role. Check the [Optimizer support list](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models) and select the deployment prepared for each role.

<figure class="portal-shot" id="portal-evaluation-criteria">
<img src="../../web/assets/portal/en/16-evaluation-criteria.png" alt="Evaluation Criteria settings for Relevance, TaskAdherence, and the Judge deployment." width="1440" height="1000" loading="lazy">
<figcaption><strong>Separate the evaluators from the Judge.</strong> Set Relevance threshold 4 and TaskAdherence pass 1. Select the Judge deployment named by your <code>JUDGE_DEPLOYMENT</code> setting. <a href="../../web/assets/portal/en/16-evaluation-criteria.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Completion criteria:** The two evaluator scales, thresholds, mappings and actual Judge deployment are recorded. The saved remote definition, not a stale local environment default, determines the Judge.
{: .completion-check}

<p class="step-next no-print"><a href="#baseline" data-next-step>Next: 06. Run Foundry Evaluation →</a></p>

## 06. Run Foundry Evaluation {#baseline}

<div class="lab-concept" data-learning-frame="baseline">
<p><strong>What:</strong> Generate real responses from pinned v1 and collect managed scores and reasons.</p>
<p><strong>Why:</strong> A candidate needs a recorded starting point for comparison. Completed means processing ended, not that every response was correct.</p>
<p><strong>How · where:</strong> Review and submit once in Foundry, inspect all 12 items, and use read-only terminal lookup to record the actual evaluation and run IDs.</p>
</div>

<p class="wizard-context" data-wizard-step="3"><strong>Part 3 of the same evaluation wizard.</strong> Review the settings from 04–05 and select Submit once here. Submission incurs real model-call costs.</p>

An **evaluation is the saved configuration**; a **run is one execution of it**. The first v1 run is your **baseline**, the starting point for comparison.

1. In **Review**, confirm **v1 + original dev12 + query-only input + two evaluators + your Luna Judge**.
2. Name the evaluation **`lab-en-learning-loop`** and, if available, name the run **`baseline-v1`**. Use handoff names in a prepared class. If the baseline is already completed, open its results instead of submitting again.
3. For an authorized job not already submitted, select **Submit** once. The run is complete only after you confirm **Completed and all 12 results**, not immediately after clicking.

<figure class="portal-shot" id="portal-evaluation-review">
<img src="../../web/assets/portal/en/17-evaluation-review.png" alt="Foundry evaluation Review page for checking Agent, version, dataset, and evaluator settings." width="1440" height="1000" loading="lazy">
<figcaption><strong>Review before Submit.</strong> Confirm Agent version 1, the same dev12, query-only input, both evaluators, and the Judge. Submit once within the approved scope, then inspect the run status. <a href="../../web/assets/portal/en/17-evaluation-review.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Open **Evaluations → your evaluation name → Evaluation runs → baseline run**.

| State | What to do |
|---|---|
| Running / In Progress | Refresh the same run and wait. Do not submit another. |
| Completed | Check all 12 results and error counts, then continue to 07. This does not mean every answer is correct. |
| Failed / Partial, or missing results | Preserve the error/run ID and use [evaluation troubleshooting](troubleshooting.md#evaluation). Do not mark it complete. |

If it remains unfinished after 30 minutes, record the state/error and notify the facilitator. Stopping your wait does not cancel the remote job.

Use this **read-only command** to retrieve actual evaluation and run IDs. If you chose a different name, use that exact name with `--name`.

```sh
python -m lab --config .lab/lab-en/.env native-evals --name lab-en-learning-loop
```

Record `evaluation_id` and the `run_id` whose **`agent_version` is `"1"` and `status` is `completed`**. Evaluation IDs use `eval_...`; run IDs use `evalrun_...`. They are not interchangeable. If several evaluations have the same name, compare their portal creation times, Agents, and runs to select yours. This command submits nothing.

**Completion criteria:** The real Foundry run is Completed and exposes 12 output items. Record failed/error counts in `result_counts` too. A failed or incomplete run stays failed/incomplete. No local custom Judge substitutes for this managed Evaluation.
{: .completion-check}

<p class="step-next no-print"><a href="#analyze" data-next-step>Next: 07. Read scores and reasons →</a></p>

## 07. Read scores and reasons {#analyze}

<a id="score-rubric"></a><a id="worked-evaluation"></a>

<div class="lab-concept" data-learning-frame="analyze">
<p><strong>What:</strong> Connect actual responses and evaluator reasons to policy evidence.</p>
<p><strong>Why:</strong> An average can hide a date, citation, or routing failure. Explain the defect before deciding which instruction to change.</p>
<p><strong>How · where:</strong> Read Foundry detailed metrics, User view, and the source policy together; record a hypothesis and behaviors to preserve in notes.md.</p>
</div>

1. Open the completed baseline run from 06 and read its pass/fail/error counts.
2. In **Detailed metrics result**, select a failing or lowest-score row and read **`Relevance.reason`** and **`TaskAdherence.reason`**. A `reason` explains why that score was assigned.
3. Open the row's **`conversation_id → User view`** to read the actual question/answer. Return to detailed metrics for scoring reasons; they are in a different view.
4. Find the cited policy ID in the [source policies](../../data/en/knowledge/documents.json). Review a good case the same way. If no failure exists, record that fact rather than weakening v1 to create one.

<figure class="portal-shot" id="portal-evaluation">
<img src="../../web/assets/portal/en/18-evaluation-results.png" alt="Foundry evaluation summary and per-question detailed metrics." width="1440" height="1000" loading="lazy">
<figcaption><strong>Read per-question scores and reasons.</strong> Check pass, fail, and error counts, then open Detailed metrics result for Relevance.reason and TaskAdherence.reason. Inspect individual cases, not only averages. <a href="../../web/assets/portal/en/18-evaluation-results.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Relevance 4/5 is not 80% accuracy. TaskAdherence 1 means Pass, not a low five-point score. Missing values are not zeros or successful rows. Generic evaluators do not certify every business rule.

**Illustrative scores, not results from an actual run:**

| Example scores for one answer | Interpretation |
|---|---|
| Relevance **3**, TaskAdherence **1** | It followed the task but missed the relevance threshold of 4. It did not pass both criteria. |
| Relevance **5**, TaskAdherence **1** | It passed both scoring criteria. A person must still check policy dates, conditions, and citations. |
| Missing score | Check for an evaluation error or missing output. Do not record it as zero or a pass. |

<figure class="portal-shot" id="portal-evaluation-case">
<img src="../../web/assets/portal/en/19-evaluation-case.png" alt="User view showing the question and the Agent's JSON response." width="1440" height="340" loading="lazy">
<figcaption><strong>Compare the response with policy.</strong> Read the question and JSON answer in User view, then check policy dates, conditions, and citations. Return to Detailed metrics result for the reasons; an incorrect response is not a reference answer. <a href="../../web/assets/portal/en/19-evaluation-case.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Watch for wrong date boundaries, unnecessary assumptions, numeric retrieval IDs instead of document citations, incorrect human routing, invented actions and unsupported certainty. A truthful statement of uncertainty must not be replaced with a fabricated fact to satisfy a Judge.

Create `.lab/lab-en/notes.md` in a text editor and fill in this worksheet with your results. `.md` is a plain-text note file; create your local lab-record folder first if it does not yet exist. Bring across the values recorded in 01–06. Keep full responses/reasons separately, and use the worksheet for identifiable runs/cases and concise observations.

| Record | What to write |
|---|---|
| Baseline | Actual evaluation ID, run ID, Agent version, and dataset hash |
| Results | Per-metric pass/fail/error counts across all 12 cases |
| Problem case | Question, problematic sentence in the actual response, evaluator reason, and policy ID |
| Improvement hypothesis | For a date-boundary mistake, require checking effective dates and inclusive boundaries; do not embed the answer |
| Behaviors to preserve | Correct citations, honest uncertainty, and action boundaries already working well |

<p class="share-checkpoint" id="share-baseline"><strong>Discuss:</strong> State the run ID, each metric's scale/pass count, a concrete problematic answer and the instruction behavior you want to improve.</p>

**Completion criteria:** Use an actual case to explain what you intend to change, or why you would retain the current instructions. An average score alone is insufficient.
{: .completion-check}

<p class="step-next no-print"><a href="#optimize" data-next-step>Next: 08. Improve instructions with Agent Optimizer →</a></p>

## 08. Improve instructions with Agent Optimizer {#optimize}

<a id="tune"></a>

<div class="lab-concept" data-learning-frame="optimize">
<p><strong>What:</strong> Generate instruction candidates with Agent Optimizer and review the changes.</p>
<p><strong>Why:</strong> Candidate generation does not guarantee improvement. A higher internal rank cannot justify invented policy or changed model/tool conditions.</p>
<p><strong>How · where:</strong> Run Instruction only in Foundry and inspect View changes. Save complete reviewed instructions and their actual provenance privately.</p>
</div>

**Agent Optimizer proposes and tests instruction improvements.** A **candidate** is a proposed instruction set that has not yet been accepted. This does not retrain the model.

1. Open **Build → Agents → lab-en-iq → Optimize Preview/Optimize**.
2. If an **Agent / Cost** selection screen appears, select **Agent**, not **Cost**, which optimizes a different concern.
3. From the run list, select **Optimize** or **Create an optimization run / Create optimization run** and use the settings below. Preview means a pre-release feature. If the menu or model is unavailable, stop and follow [Optimizer troubleshooting](troubleshooting.md#optimizer).

| Setting | Choice |
|---|---|
| Agent version | Explicit baseline **1** |
| Choose targets | **Instruction only** (change instructions); Model and Tool description off |
| Max candidates | Operator-approved bound; this run uses at most **2**, not more releases |
| Optimization model | Your `OPTIMIZER_DEPLOYMENT` / gpt-5.5 |
| Evaluation model | Your `JUDGE_DEPLOYMENT` / gpt-6-luna |
| Dataset | Same registered English dev12 version 1 |
| Criteria | Relevance 4; TaskAdherence binary pass 1 |

<figure class="portal-shot" id="portal-optimizer-target">
<img src="../../web/assets/portal/en/07-optimizer-target.png" alt="Agent Optimizer target settings for baseline version, Instruction only, candidate count, and model roles." width="1210" height="968" loading="lazy">
<figcaption><strong>Separate optimization scope and model roles.</strong> Select baseline version 1 and Instruction only, and keep candidates within the approved limit. Assign the prepared deployments to Optimization model and Evaluation model. <a href="../../web/assets/portal/en/07-optimizer-target.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

If Criteria shows **No custom evaluators available**, switch **Custom only OFF** or select **View built-in evaluators**. Open each built-in row, set its correct threshold and Apply. Do not create a custom scorer to bypass a filter.

<figure class="portal-shot" id="portal-optimizer-data">
<img src="../../web/assets/portal/en/08-optimizer-dataset.png" alt="Agent Optimizer list for selecting a registered evaluation dataset." width="1210" height="968" loading="lazy">
<figcaption><strong>Reuse the same English data.</strong> Select the dev12 registration/version used for the baseline and include all 12 cases. Editing or regenerating the file changes the comparison conditions. <a href="../../web/assets/portal/en/08-optimizer-dataset.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

In **Review**, confirm the Agent/version, dataset, evaluators, and estimated cost, then **Submit** once within the approved scope. An estimate is not a billing cap. Open the job in **Optimization runs**, wait at most 60 minutes, and retain its actual state. Reuse the same job ID when resuming. Optimization includes multiple internal calls.

Inspect original/candidate scores and **View changes**. The internal **0–1 ranking** is not the separate managed Evaluation mean or pass percentage. Keep model, tools, reasoning and output schema unchanged; an empty function-tool export does not authorize removal of the MCP policy connection.

<figure class="portal-shot" id="portal-optimizer-results">
<img src="../../web/assets/portal/en/09-optimizer-results.png" alt="Agent Optimizer results comparing the baseline with candidate scores and rankings." width="1440" height="1000" loading="lazy">
<figcaption><strong>Read the candidate, not just the ranking.</strong> Compare per-evaluator scores and review the instruction changes. If no candidate offers a sound improvement, retain v1 and record why. <a href="../../web/assets/portal/en/09-optimizer-results.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-optimizer-diff">
<img src="../../web/assets/portal/en/10-optimizer-changes.png" alt="View changes dialog comparing baseline and candidate instructions." width="1038" height="622" loading="lazy">
<figcaption><strong>Read the instruction changes.</strong> Use View changes to identify which response behaviors change. Reject invented policy, unsupported certainty, and non-instruction configuration changes; assess content and effect rather than length. <a href="../../web/assets/portal/en/10-optimizer-changes.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Save a candidate only after reviewing it.**

1. Select the candidate and inspect **View changes**. Reject instructions that invent policy or unsupported certainty.
2. Copy the **complete revised instructions**. If the view shows only changed lines, ask the operator to confirm the full text rather than using those fragments as the instruction file.
3. Save **UTF-8 plain text** to `.lab/lab-en/candidate.txt`. Do not use Word/rich text; check that the name is not `candidate.txt.txt`. Exclude diff (change comparison) `+`/`-` markers, UI explanations, and scores.
4. Record real job/candidate IDs and any manual edits/reasons in `notes.md`. Use this file next, not the repository's `prompts/en/candidate.txt`.

**Do not continually create v3, v4 and later releases.** Use the next step's CLI to create one v2 for comparison, so **do not use both Promote candidate and the CLI creation command**. Creating a version is separate from publishing it or approving activation.

<p class="share-checkpoint" id="share-optimizer"><strong>Discuss:</strong> Present the reviewed candidate and explain the changed behaviors, expected improvements, and possible regressions.</p>

**Completion criteria:** Record real job/candidate IDs, the reviewed instruction file, and change reasons. If no candidate is worth retaining, record “keep v1; no improvement observed” and continue at 10. Do not repeatedly run the same job to manufacture improvement.
{: .completion-check}

**Next path:** With a reviewed candidate file, continue to [09 reevaluation](#decision). Without one, go to [10 cleanup](#cleanup). Do not create v2 just to have another version.

<p class="step-next no-print"><a href="#decision" data-next-step>Next: 09. Reevaluate and compare v1/v2 →</a></p>

## 09. Reevaluate and compare v1/v2 {#decision}

<a id="review"></a><a id="operate"></a>

<div class="lab-concept" data-learning-frame="decision">
<p><strong>What:</strong> Reevaluate changed instructions under the same definition and record retain v1, accept v2, or hold.</p>
<p><strong>Why:</strong> A v2 label is not improvement evidence. Consider actual errors, latency/tokens, and statistical uncertainty alongside quality.</p>
<p><strong>How · where:</strong> Prepare explicit v2 and its same-definition run in the terminal, then compare every case in Foundry Compare runs. Do not publish to production.</p>
</div>

**For a prepared environment, confirm who runs commands first.** Version creation checks ownership records. If you have no participant-specific configuration and execution records, the owning operator runs these commands. Do not bypass that check by replacing the user name in their configuration. Participants compare the two supplied runs in the portal.
{: .note}

**1. Create v2 from the reviewed instructions.** Keep models, tools, data, evaluators, and Judge fixed, and preserve v1.

```sh
python -m lab --config .lab/lab-en/.env native-agent --version 2 --prompt .lab/lab-en/candidate.txt --confirm
```

Confirm `agent_name: lab-en-iq` and `version: "2"`. If a different v2 already exists or the model deployment changed, stop and preserve the original records. A new version alone does not demonstrate improvement.

**2. Add a v2 run to the same evaluation configuration.** The helper below is a supplied Python program. It uses the official Azure AI Projects/OpenAI SDK to reuse the baseline's dataset and evaluator settings, rather than creating a different evaluation.

| Placeholder | Where to find your value |
|---|---|
| `YOUR_PROJECT_ENDPOINT` | `AZURE_AI_PROJECT_ENDPOINT` in `.lab/lab-en/.env` |
| `YOUR_SUBSCRIPTION_ID` | The subscription ID from 01, also `AZURE_SUBSCRIPTION_ID` in that `.env` |
| `YOUR_EVALUATION_ID` | The selected `evaluation_id` from the `native-evals` output in 06 |
| `YOUR_BASELINE_RUN_ID` | That evaluation's completed version-1 `run_id`, not an Optimizer job ID |

Replace all four values and execute this single-line command. Submitting a new run incurs charges.

```sh
python scripts/add_foundry_eval_run.py --endpoint "YOUR_PROJECT_ENDPOINT" --subscription "YOUR_SUBSCRIPTION_ID" --evaluation "YOUR_EVALUATION_ID" --baseline "YOUR_BASELINE_RUN_ID" --version 2 --name candidate-v2 --out .lab/lab-en/artifacts/foundry-evaluations/candidate-v2.json
```

Confirm `status: completed` and all 12 cases. If the default 30-minute wait expires, the command returns exit code 2 with Still running. If the receipt contains a run ID, repeat the **identical command and `--out` path** to collect that run. For an unknown submission without a run ID or an existing remote name, follow [duplicate-submission recovery](troubleshooting.md#evaluation). Do not delete the receipt or rename the run to resubmit.

The helper verifies thresholds, Judge, mappings, and each output item's Agent version and instructions.

**3. Return to Foundry and compare.** In the same evaluation's **Evaluation runs**, select the v1 and v2 rows and **Compare runs**. Explicitly choose **v1 as Baseline**; selection order must not reverse the comparison.

<figure class="portal-shot" id="portal-evaluation-comparison">
<img src="../../web/assets/portal/en/20-evaluation-comparison.png" alt="Compare runs view showing baseline and candidate scores, means, and statistical results." width="1440" height="520" loading="lazy">
<figcaption><strong>Confirm the comparison direction and results.</strong> Select v1 as Baseline, then compare scores, pass counts, and statistical results. Inconclusive means a difference was not established; it is not evidence of equivalence. <a href="../../web/assets/portal/en/20-evaluation-comparison.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Compare responses, scores, and reasons for all 12 cases side by side. Require no decline in all-criteria passes or either metric's pass count/mean, and at least one strict measured improvement. Check factual truth, routing, and response format too, and record latency, tokens, and statistical results.

<p class="share-checkpoint" id="share-optimized"><strong>Explain the result:</strong> Identify the actual gain, unchanged criteria, any regression, and the remaining uncertainty. Observed improvement is not a guarantee that every future stochastic run will improve.</p>

In `notes.md`, record v1/v2 pass counts and means per metric, errors, latency/tokens, statistical results, and your decision side by side. If improvement criteria are not met, **retain v1 or hold the decision**. Do not adopt a candidate with actual policy errors merely because generic evaluators passed it.

**Latency** is time spent waiting for a response; **tokens** measure the amount of text processed by the model. A small score improvement can come with increased waiting time and cost.

| Decision | When it fits |
|---|---|
| Consider v2 for adoption | All 12 cases use the same conditions, quality does not regress and at least one measure improves, no policy errors are found, and latency/token tradeoffs were reviewed. Production approval is separate. |
| Retain v1 | No improvement, or previously correct behavior got worse. This is a valid learning outcome. |
| Hold the decision | Errors, missing results, or different conditions prevent a fair judgment. Record the missing evidence. |

**Completion criteria:** Record the two actual run IDs, complete same-criteria comparison, and the reasons for accepting, retaining, or holding. Do not accumulate release numbers. Production approval and independent generalization are separate and are not granted by this dev12 exercise.
{: .completion-check}

<p class="step-next no-print"><a href="#cleanup" data-next-step>Next: 10. Save results and delete resources →</a></p>

## 10. Save results and delete resources {#cleanup}

<a id="troubleshooting"></a><a id="sources"></a>

<div class="lab-concept" data-learning-frame="cleanup">
<p><strong>What:</strong> Preserve results, then remove your lab resources or hand them to an approved retention owner.</p>
<p><strong>Why:</strong> Search and logs can remain after the browser closes. Deleting the wrong shared group can also remove someone else's resources.</p>
<p><strong>How · where:</strong> Verify exact targets, ownership, and authorization in Azure Portal and the terminal, then verify absence after deletion.</p>
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
| Dedicated environment explicitly approved for retention | Do not run deletion commands. Record remaining resources, the retention reason, cost owner, and review date; verify that the resources remain and hand them over. |
| Operator-provided shared project | **Do not delete the resource group, Foundry resource, shared models, or Search service.** Remove only assigned objects and hand remaining resources to the operator. |
| Setup or execution stopped partway through | Compare `config.json`, the manifest, and actual Azure resources. Failure does not mean nothing was created. |

**Follow only the path matching your environment.** In a shared environment without your own configuration and local ownership records, hand CLI cleanup to the operator too. Do not copy another person's records to perform deletion.

For shared resources with your own local ownership records, first inspect this **plan-only** command:

```sh
python -m lab --config .lab/lab-en/.env cleanup
```

Read `mode: LOCAL_PLAN_ONLY`, `actions`, `never_deleted`, and `manual_follow_up`. Verify names, project, and ownership. Run the following only after obtaining authorization for exactly those deletions. If your environment name differs, use its matching prefix.

```sh
python -m lab --config .lab/lab-en/.env cleanup --confirm-prefix lab-en
```

Confirm `OWNED_OBJECTS_ABSENT`. This removes recorded Agent versions, search objects, and connections, but **not resource groups, model deployments, Search hosting, logs, or RBAC**. It does not automatically remove every portal-created dataset, evaluation, Optimizer job, Playground conversation, or model-smoke response. Delete authorized items individually in their owning view; if no delete action is offered, hand retention or project cleanup to the operator.

### Delete a dedicated group and verify its absence {#cleanup-delete}

Replace `YOUR_LAB_RESOURCE_GROUP` with **`names.resource_group`** from `config.json`. Verify subscription, ownership tags, and the entire inventory, not just a familiar prefix.

```sh
az group show --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP" --query "{name:name,location:location,tags:tags}" -o json
az resource list --subscription "YOUR_SUBSCRIPTION_ID" --resource-group "YOUR_LAB_RESOURCE_GROUP" --query "[].{name:name,type:type}" -o table
```

**Resource-group deletion is irreversible and removes the group's Foundry resources, model deployments, Search, and monitoring together.** After saving evidence and receiving approval for that exact group, choose one method:

The default Application Insights Smart Detection action group can also serve alerts in other resource groups. A dedicated lab group does not establish that every resource is independent. Review shared dependencies with the owner before deletion, or retain the group; do not delete alerts, permissions, or locks simply to bypass a check.

1. **Portal:** Azure Portal → Resource groups → exact group → **Delete resource group**. Read the deletion inventory, type the requested group name, and confirm.
2. **CLI:** Run the command below and review the target again at the confirmation prompt. Do not append `--yes` to bypass confirmation.

<figure class="portal-shot" id="portal-delete-review">
<img src="../../web/assets/portal/en/28-delete-review.png" alt="Resource-group deletion review with the target inventory, group-name confirmation field, and Delete and Cancel buttons." width="1440" height="1000" loading="lazy">
<figcaption><strong>Read the proposed inventory and confirmation field first.</strong> Verify the group name and every resource. Only after authorization, enter the group name and proceed with Delete. Use Cancel if the target is wrong or deletion is not approved. <a href="../../web/assets/portal/en/28-delete-review.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

```sh
az group delete --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP"
```

An accepted request is not completed deletion. Check portal notifications and group status, then verify that this command successfully prints **`false`**:

```sh
az group exists --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP"
```

Authentication or network errors are not `false` and do not prove deletion. If `true`, inspect deletion progress. For **Locks**, permissions, or dependencies in other groups, follow [deletion troubleshooting](troubleshooting.md#cleanup). Do not remove organizational locks without authorization.

Afterward, open **Cost Management → Cost analysis** for the subscription, time range, and group. Billing updates can lag, and earlier usage charges do not disappear. Separately check logs/storage in other groups and service-specific soft-deleted resources. Permanent deletion/purge requires organizational policy and separate authorization.

**Final completion criteria:** Verify an authorized dedicated-group deletion and record the time, or hand over an explicitly retained dedicated/shared-resource inventory with reasons, cost owner, and retention review date. Do not delete `.lab` first and lose ownership evidence. See the [operator cleanup worksheet](admin-setup.md#cleanup) and [deletion troubleshooting](troubleshooting.md#cleanup).
{: .completion-check}
