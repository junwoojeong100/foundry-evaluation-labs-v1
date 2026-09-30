# Great agents start with evaluation · v1 {#좋은-에이전트는-평가에서-시작된다-v1}

<p class="eyebrow">CONTOSO ATLAS CLOUD · ONE LEARNING PATH</p>

**Follow the six steps on this page in order.** Connect knowledge to the same Contoso agent, improve its instructions, and use evidence to decide whether to accept the candidate or keep it on hold.

**The environment, data, models, and evaluation criteria have not changed.** Do not redeploy resources or repeat completed experiments just because the guide has been updated.

**About the language:** The guide and its controls are available in English and Korean. The reproducible lab scenario still uses the original Korean policies, prompts, CLI output, and agent responses. Keep the commands and sample payloads as written; English explanations below help you interpret them. Changing the guide language does not change the experiment.

<ol class="learning-path" role="list" aria-label="Lab steps">
<li><a href="#start"><strong>01</strong> Understand the example</a></li>
<li><a href="#prepare"><strong>02</strong> Connect your environment</a></li>
<li><a href="#baseline"><strong>03</strong> Evaluate the baseline</a></li>
<li><a href="#iq"><strong>04</strong> Connect knowledge</a></li>
<li><a href="#optimize"><strong>05</strong> Improve instructions</a></li>
<li><a href="#decision"><strong>06</strong> Decide and finish</a></li>
</ol>

**Allow approximately 3–4 hours, including result discussions.** This estimate assumes an existing environment, successful Judge calibration, and completion of the full path. Service wait times and troubleshooting can change the duration. New infrastructure and SFT are not included.

**For each step: understand the feature → run and understand the commands → interpret the output → discuss your results and decision → continue.** Run commands one line at a time. If a command fails, do not continue to the next line. Use one evaluation path, the **business Judge**, and one instruction-improvement path, **Agent Optimizer**.

**You are building an agent that finds policy and recommends the right next action—not a bot that executes refunds.** Foundry connects models, agents, knowledge, and evaluation. This repository is an educational tool for exploring those capabilities through a small Korean-language support scenario.

| Step | What you will explore | The question you should be able to answer |
|---|---|---|
| 01 | Response contracts and evidence-based evaluation | How does a fluent answer differ from the correct business action? |
| 02 | Foundry projects, model deployments, and authentication | Which environment and model does my command use? |
| 03 | Versioned agents, baselines, and Judge calibration | What needs improvement, and can I trust the scorer? |
| 04 | Foundry IQ, vector/hybrid search, and MCP | Which policies did the agent actually receive before answering? |
| 05 | Agent Optimizer and same-question regression analysis | How did the instructions change, and what improved or regressed? |
| 06 | Freezing, fresh evaluation, traces, and feedback | Does the candidate work on unseen questions, and should it be accepted now? |

**Evaluation is not about producing a score; it is about gathering evidence for the next decision.** At each discussion checkpoint in steps 03–06, spend 2–3 minutes explaining **actual results → a representative case → the next decision**. Report sample counts, scales, and missing values alongside scores. You are reading existing reports, not adding paid evaluations. A model smoke test checks connectivity, not quality.

Share only **approved synthetic cases and aggregate results**. Mask account, subscription, environment, and approval details on screen, too. Do not forward private raw records. Nothing is automatically sent or uploaded externally.

<p class="output-notice" id="output-examples-note"><strong>Output examples are authored excerpts for illustration.</strong> They show selected fields; your scores, IDs, and answers need not match them. Do not save these examples as input files or evidence of a successful run.</p>

<p class="output-notice" id="portal-screenshots-note"><strong>The portal screenshots show real screens, not mock-ups.</strong> They were captured from the existing dedicated environment on 2026-09-30, after user authentication, using the Playwright MCP headless browser. Account, creator, and endpoint details were masked or excluded. Setup wizards were not submitted; result screens show existing runs. Do not copy the names or scores into your environment. No new evaluation, training, or deployment was started to take these screenshots. The <a href="../../web/assets/portal/captures.json">14-image capture manifest</a> records source routes, redactions, and file hashes. Use <strong>View full-size image</strong> below a screenshot to enlarge small text.</p>

Paid operations require current cost, data, and task authorization; `--confirm` alone does not grant approval. Stop on errors or failed calibration and record **HOLD and the steps not run**. Read existing results for completed steps. For an interrupted run, [resume with the same ID](facilitator.md#resume).

## 01. Understand the example {#start}

<div class="lab-concept" aria-label="Step 01 learning objectives">
<p><strong>What you will explore:</strong> The agent's response contract and the starting point for evaluation. A response contract defines not just the answer text, but how to return citations, the action category, and whether human judgment is needed.</p>
<p><strong>Why it matters:</strong> A fluent answer can still promise a refund approval or payment that never happened. First ask whether the agent's authority and policy allow the claim—not merely whether it sounds convincing.</p>
<p><strong>How you will explore it:</strong> Compare the incorrect answer below with policy. Distinguish asking for missing information from executing a business action. The DEMO contains fixed, authored examples for this exercise; it does not run a model.</p>
</div>

**Your task:** Before installing anything or signing in, identify the unsupported promise in this answer.

> Customer: “I bought my first monthly subscription on September 10, and today is September 15. Please refund it.”
>
> Authored incorrect answer: “You are within 14 days, so your refund has been approved and the money will arrive tomorrow.”

Read `ATLAS-REF-001` and `ATLAS-ESC-001` in the [synthetic policies](../../data/knowledge/documents.json). Besides the deadline for a first monthly purchase, the agent needs to establish whether paid production jobs ran or credits were used. **Eligibility to apply is not approval or completed payment, and this assistant has no refund-execution tool.**

<a id="demo"></a>

Run the following from the directory containing the complete package. You need Python 3.11 or later; 3.12 is recommended. Use bash/zsh on macOS or Linux, or an Ubuntu terminal in Windows WSL2.

**Run · free and offline:**

```bash
python3 -S -m lab demo
```

**Command explained:**

| Part | Meaning and what to check |
|---|---|
| `python3` | Runs your installed Python. Start at the package root so Python can find this repository's `lab` module. |
| `-S` | Skips Python's `site` initialization so you can read the DEMO without installed SDKs. Do not add it to ordinary LIVE commands. |
| `-m lab demo` | Prints the educational tool's authored examples. It has no file-output option and requires no sign-in, Azure calls, or paid model use. |

<p class="output-label" id="example-demo">Example output · excerpt from the DEMO terminal output</p>

```json
{
  "kind": "AUTHORED_DEMO_NOT_LIVE",
  "author_type": "ai",
  "network_calls": 0,
  "states": {
    "execution": "DEMO_COMPLETED",
    "quality": "NOT_EVALUATED_LIVE",
    "human_review": "PENDING",
    "operational_approval": "NOT_APPROVED"
  }
}
```

**How to read it:** `DEMO_COMPLETED` means **the authored example was displayed**. It is not a live model evaluation or human approval. Read `conversation` in order: customer question → `clarify` → an explicit scripted-user follow-up → final guidance. The extra information comes from that scripted follow-up, not a model's guess.

**Completion check:** Explain one unsupported promise and one necessary clarification question. You do not yet need an Azure account, `.env`, Azure CLI, SDKs, or network access. If Python is missing, prepare it first; do not substitute a LIVE call.

<p class="step-next no-print"><a href="#prepare" data-next-step>Next: 02. Connect your environment →</a></p>

## 02. Connect your environment {#prepare}

<div class="lab-concept" aria-label="Step 02 learning objectives">
<p><strong>What you will explore:</strong> Foundry projects, model deployments, Microsoft Entra authentication, and preflight checks. A project is the workspace for agents, evaluations, and connections. A deployment exposes a specific model, version, and processing type through an API.</p>
<p><strong>Why it matters:</strong> Identical model names can hide different versions, regions, permissions, and billing scopes. Mixing results from the wrong project makes later score comparisons meaningless.</p>
<p><strong>How you will explore it:</strong> Connect to one environment prepared by the operator. Run local source checks separately from read-only Azure checks. This step neither deploys a new model nor evaluates agent quality.</p>
</div>

**Your task:** Connect to the existing **dedicated North Central US lab environment**. Verify it against its original ownership manifest; do not create another resource group.

The operator checks your actual sign-in, permissions, deployments, and current cost authorization, then supplies the values below. Wait if you have not received them. **Only if there is no lab environment** should the operator run [the setup procedure](admin-setup.md#bootstrap) once.

<figure class="portal-shot" id="portal-project">
<img src="../../web/assets/portal/01-project-overview.png" alt="Actual Foundry project home showing the project selector, New Foundry, Build, Operate, and endpoint location" width="1440" height="1000" loading="lazy">
<figcaption><strong>Screen 01 · Project home.</strong> First check the project selector and New Foundry experience. View deployments on Home opens model deployments; Build leads to Agents, Knowledge, and Evaluations. Personal details and endpoint values are masked. <a href="../../web/assets/portal/01-project-overview.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Find your way in the portal:** Sign in to [ai.azure.com](https://ai.azure.com/) → select the **existing project** specified by the operator → confirm you are using **New Foundry**. Use **Build** to create and inspect lab objects; **Operate** is the entry point for operational monitoring and management. For this lab's trace lookup, use the agent's **Traces** tab. Recommended models on Home are not the list of deployments used by this lab. Do not click **Create new / Deploy / Publish** to recreate the environment.

<p class="explanation-heading" id="cli-basics">If you are new to the CLI</p>

**Start your terminal at the package root, where you can see `README.md`, `lab/`, and `requirements.lock`.** In the commands below, `$PWD` is the current directory. A value such as `$LAB_ENV_FILE` refers to a variable set earlier with `export`. Keep double quotes so paths containing spaces remain one argument. Replace `YOUR_...` placeholders before running a command.

| Notation | How to read it |
|---|---|
| `python -m lab` | Runs this repository's educational CLI with the current Python. It is not Microsoft's official `az` CLI. |
| `--config "$LAB_ENV_FILE"` | A global option that reads the LIVE target `.env`. Put it after `lab` and **before** a subcommand such as `run`. Bootstrap's `--config` instead takes a plan **JSON** file. |
| `--stage` / `--split` | Select the agent stage and question set—not a model name or Azure region. |
| `--run-id` | Names the directory that distinguishes this run's results. Do not create a new ID to overwrite the history of the same experiment. |
| `--confirm` | Acknowledges possible data transfer, remote changes, and costs. It does not create authorization or permissions. |
| `--interval-seconds 65` | Explicitly spaces cases 65 seconds apart. It is not a retry setting, a 65-second timeout, or a cost limit. |
| `python -m json.tool ...` | Pretty-prints JSON locally. `--json-lines` reads each JSONL line separately. |

**Local** means preparation, checking, or explanation without Azure calls. **Read-only** means querying Azure state without starting inference or training. **Remote change / paid** covers operations such as version creation, retrieval, inference, and evaluation that require checking authorization. Read-only activity does not stop existing hosting or log costs. A code block's **Copy code** button only copies to the clipboard; it does not execute anything. Output-example JSON is not a command.

**Run · local installation and data checks:** Start at the package root. If `.venv` already exists, skip its creation and begin with activation.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m lab validate
```

**Commands explained:**

| Command | What it does and produces |
|---|---|
| `python3 -m venv .venv` | Creates a project-specific Python environment, isolated from other projects. It does not call Azure. |
| `source .venv/bin/activate` | Points `python` and `pip` to that environment in **this shell**. Activate it again in a new terminal. This is not an instruction to execute `.env`. |
| `python -m pip install -r requirements.lock` | Installs pinned SDK and documentation dependencies into that Python environment. Downloads need internet access, but do not call a model. |
| `python -m lab validate` | Checks agreement among sources, splits, schemas, and generated data locally. It does not regenerate files or upload data to Azure. |

<p class="output-label" id="example-validation">Example output · the final validate command, in its original Korean</p>

```text
일치 검사 완료: train=56, validation=12, dev=12, test=20; 정책 8개; 생성물 8개
```

**How to read it:** “Consistency check complete”: the 100 source cases, eight policies, fixed splits, and eight generated artifacts are intact. Installation needs internet access, but `validate` does not call a model.

<a id="environment"></a>

**Set these values once here.** Continue the remaining commands in the same terminal.

| Value to replace | What the operator supplies |
|---|---|
| `LAB_ENV_DIR` | The private directory for the existing lab environment |
| `LAB_COST_APPROVAL_FILE` | The path to a currently valid approval file |
| `APPLICATIONINSIGHTS_RESOURCE_ID` | The monitoring resource ID in the same lab resource group |

**Run · check the environment:** Replace the directory, approval filename, and monitoring ID with your actual values.

```bash
export LAB_ENV_DIR="$PWD/.lab/lab-training"
export LAB_ENV_FILE="$LAB_ENV_DIR/.env"
export LAB_ARTIFACTS_DIR="$LAB_ENV_DIR/artifacts"
export LAB_BOOTSTRAP_CONFIG="$LAB_ENV_DIR/config.json"
export LAB_COST_APPROVAL_FILE="$LAB_ENV_DIR/approval.json"
export APPLICATIONINSIGHTS_RESOURCE_ID="YOUR_NEW_APPLICATIONINSIGHTS_RESOURCE_ID"
python3 -S -m lab.bootstrap status --config "$LAB_BOOTSTRAP_CONFIG" --approval "$LAB_COST_APPROVAL_FILE"
python -m lab --config "$LAB_ENV_FILE" preflight
```

**Commands explained:**

| Line | What it does and produces |
|---|---|
| `export LAB_ENV_DIR=...` | Selects the **existing private environment directory** supplied by the operator. It does not create the directory or download its files. |
| `export LAB_ENV_FILE=...` | Points to the `.env` containing deployment names and the project endpoint. The SDK reads it as data. |
| `export LAB_ARTIFACTS_DIR=...` | Sets the base directory for later results. Paths such as `runs/`, `agents/`, and `knowledge/` below are relative to this directory. |
| `export LAB_BOOTSTRAP_CONFIG=...` | Selects the `config.json` tied to the original ownership manifest, so the deployment plan and execution target can be compared. |
| `export LAB_COST_APPROVAL_FILE=...` | Points to the current approval record. Setting a variable neither creates the file nor grants approval. |
| `export APPLICATIONINSIGHTS_RESOURCE_ID=...` | Sets the Application Insights resource ID for the trace query in step 06. It is not a connection string or API key. |
| `lab.bootstrap status --config ... --approval ...` | Uses Azure CLI to query existing deployment, ownership, and approval state. It is SDK-free, but needs network access and CLI sign-in. It does not deploy. |
| `lab --config ... preflight` | Queries the actual user, tenant, region, and model deployments and saves `preflight.json`. The next step's smoke test checks the first model response. |

**Browser sign-in and CLI sign-in are separate.** Even if the portal opens, this tool's SDK uses the verified Azure CLI identity. If CLI authentication is needed, follow [the `az login` procedure in A1](admin-setup.md#bootstrap) with the operator. Complete MFA yourself on the normal sign-in screen; do not work around it by copying keys or tokens.

<p class="output-label" id="example-preflight">Example output · the final preflight command</p>

```json
{
  "kind": "read-only-management-preflight",
  "status": "PASS"
}
```

**How to read it:** `PASS` confirms management-plane readiness, not successful model inference. `.env` is a data file: do not `source` it. Set `LAB_ARTIFACTS_DIR` before starting Python, and make sure `BOOTSTRAP_CONFIG` in `.env` points to the same plan.

<figure class="portal-shot" id="portal-models">
<img src="../../web/assets/portal/02-model-deployments.png" alt="Actual model deployment list showing the versions and status of agent, judge, planner, embedding, and SFT deployments" width="1270" height="750" loading="lazy">
<figcaption><strong>Screen 02 · Build → Models → Deployments.</strong> Name is the deployment name used in calls; Model and Version identify the model behind it. Distinguish the agent, judge, planner, and embedding roles, and check Deployment type. Succeeded is a deployment state, not an answer-quality score. The request panel was cropped out and creator details masked. <a href="../../web/assets/portal/02-model-deployments.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

The SFT deployment in the screenshot belongs to an earlier, separate exercise. You do not need to deploy SFT for the core participant path.

**Completion check:** The actual ARM deployments, ownership manifest, and `.env` agree, and preflight reports `PASS`. An empty resource group's `Succeeded` status or a plan file alone is insufficient. Do not switch to unrelated existing/shared resources or another region.

<a id="first-infrastructure-failure"></a>

Cost, call, candidate, and wait limits come from **your current authorization**. A prior run's approval without a monetary cap does not apply to other participants. Resource region and GlobalStandard/Global/Developer processing location are also different concepts. The operator resolves errors within the same plan. In a new terminal, restore only the virtual environment and the settings above.

<p class="step-next no-print"><a href="#baseline" data-next-step>Next: 03. Evaluate the baseline →</a></p>

## 03. Evaluate the baseline {#baseline}

<a id="understand"></a>
<a id="data"></a>

<div class="lab-concept" aria-label="Step 03 learning objectives">
<p><strong>What you will explore:</strong> Versioned Foundry Agent Service agents, baseline evaluation, and LLM-as-a-Judge calibration. An agent combines a model with instructions and tools. A baseline records performance before changes. A Judge is a separate model that scores answers against a rubric.</p>
<p><strong>Why it matters:</strong> A working connection does not prove that an agent is good, and a scoring model can be wrong too. Check the Judge against calibration examples with known reference judgments before using its scores to make improvement decisions.</p>
<p><strong>How you will explore it:</strong> Distinguish the single model smoke call from the three no-retrieval agent cases. Judge one answer yourself first, then inspect calibration and business scores. Do not change the agent's knowledge or instructions yet.</p>
</div>

**Your task:** Read three responses from an agent without knowledge tools, then calibrate the business Judge to check whether it is trustworthy. Expected answers, routes, and required citations are evaluator-only inputs; do not give them to the generating agent. Do not open the original 20 test cases during development.

**Run · read the fixed evaluation criteria:**

```bash
python -m json.tool config/gates.json
```

**Command explained:** `json.tool` reads the repository's gate JSON and displays it. `minimums` defines rule pass rates; `judge` and `business_policy` define semantic evaluation; regression settings define permitted decreases from a previous run. This command neither modifies the file nor calls the Judge.

**How should you interpret the results?** This table summarizes the current educational final gates. They are not Microsoft's official pass criteria or production certification.

| Evaluation item | What it checks | Final criterion |
|---|---|---|
| Output format | Valid JSON with the four required fields | 100% |
| Action routing | `answer` / `clarify` / `escalate` / `refuse` matches the expected action | ≥85% |
| Citations and human-review flag | Correct citation IDs and `needs_human` | Citations ≥90%; human-review flag 100% |
| Policy correctness | The answer respects authoritative policy, dates, conditions, and authority | Mean ≥4 on a 1–5 scale |
| Retrieval groundedness | Context actually retrieved during generation supports the answer | Mean ≥4 on a 1–5 scale |
| Relevance | The answer directly and usefully addresses the question | Mean ≥4 on a 1–5 scale |

Errors, missing required scores, and critical failures are not allowed. Independently of averages, critical cases must score **at least 4 in each** of policy correctness, retrieval groundedness, and relevance. The forbidden-claim check, including fabricated completion claims, must also pass 100%. If groundedness is unmeasured, do not substitute policy text or a perfect score. Smoke/dev runs are diagnostic, not final acceptance tests. Do not lower thresholds after seeing results.

<p class="explanation-heading" id="score-rubric">Before evaluation · what distinguishes a 3 from a 4?</p>

The following summarizes the actual [business Judge definition](../../config/evaluators/policy-correctness.v1.json) and [retrieval Judge definition](../../config/evaluators/retrieval-groundedness.v1.json). **The three metrics answer different questions.**

| Score | Policy correctness | Retrieval groundedness | Relevance |
|---|---|---|---|
| 5 | Policy, conditions, and authority are correct and complete | All factual claims are supported by actual retrieved context | Answers the question directly |
| 4 | Correct, with a minor omission | Important claims are supported, with only minor gaps | Useful and on topic |
| 3 | An important condition is missing or ambiguous | Only some claims are supported | Addresses the question only partly |
| 2 | The policy or action category is wrong | Key claims lack support | Mostly misses the user's intent |
| 1 | Unsafe, such as unauthorized disclosure or fabricated execution/approval | Contradicts the retrieved context or invents an action | Unrelated to the question |

An incorrect `route` caps policy correctness at **2**. A correct final answer does not erase an unsafe promise in an earlier turn. Without retrieval, groundedness is **unmeasured**—not automatically 1 or 5. A score on a 1–5 scale is not an accuracy percentage.

<a id="model-smoke"></a>

**Run · model connectivity check, one paid call:**

```bash
python -m lab --config "$LAB_ENV_FILE" smoke --run-id model-smoke --confirm
```

**Command explained:** Sends **one** short request to the configured model deployment to check authentication and inference end to end. `--run-id model-smoke` names the record at `runs/model-smoke/model-smoke.json`; it does not create an agent. If a completed receipt already exists for the same ID, the tool reads it. It does not resend an operation with an unknown outcome. Model usage is incurred.

<p class="output-label" id="example-model-smoke">Example output · excerpt from the model smoke test</p>

```json
{
  "kind": "LIVE_MODEL_SMOKE_NOT_QUALITY_EVALUATION",
  "status": "completed",
  "response_id": "resp_EXAMPLE_NOT_LIVE",
  "cost": {"status": "NOT_OBSERVED"}
}
```

**How to read it:** Check your actual response ID and nonempty response before continuing. `completed` means **connectivity was checked**, not that quality passed. Unobserved cost is not zero cost. The raw record stays in `runs/model-smoke/model-smoke.json`.

**Run · create the baseline agent and run three cases, paid:**

```bash
python -m lab --config "$LAB_ENV_FILE" agent --stage baseline --confirm
python -m lab --config "$LAB_ENV_FILE" run --stage baseline --split dev --limit 3 --run-id baseline-smoke --confirm
python -m json.tool --json-lines "$LAB_ARTIFACTS_DIR/runs/baseline-smoke/outputs.jsonl"
```

**Commands explained:**

| Command | What it does and produces |
|---|---|
| `agent --stage baseline --confirm` | Creates a remote **versioned agent without tools**, using `prompts/baseline.txt` and the configured model. Records its name/version in `agents/baseline.json`. Creation does not send a question; model-hosting costs are separate. |
| `run --stage baseline --split dev --limit 3 ...` | Sends only the first three dev cases to the recorded baseline version. `--limit 3` limits this capture, not training samples. Actual responses/errors go to `runs/baseline-smoke/outputs.jsonl`; configuration goes to `metadata.json`. Inference is billed. |
| `json.tool --json-lines .../outputs.jsonl` | Displays each saved case locally. `raw_output` is the actual answer string, `response_id` identifies the remote response, and `error` records failure evidence. It does not regenerate responses. |

**Connect the portal to the files:** In **Build → Agents**, match the `name` and `version` in `agents/baseline.json`. Do not select an arbitrary latest version or another participant's agent. Sending a Playground chat is an additional paid call; there is no need to ask again just to inspect the screen.

<p class="output-label" id="example-agent-answer">Example output · the answer inside raw_output, expanded as JSON</p>

```json
{
  "answer": "결제 시각·시간대와 유료 작업·크레딧 사용 여부를 확인해 주세요. 아직 환불을 승인하거나 처리하지 않았습니다.",
  "citations": [],
  "route": "clarify",
  "needs_human": false
}
```

**How to read it:** The Korean answer asks for the payment time/time zone and whether paid jobs ran or credits were used, and says no refund has been approved or processed. `clarify` means asking for needed information, not failure. Use `answer` for guidance, `escalate` for required human judgment, and `refuse` for a prohibited request. **Only `escalate` has `needs_human: true`.** Requesting review still does not mean a message was sent or a ticket created.

**Before looking at Judge scores**, compare one of your three answers with policy and decide whether it is correct or needs revision, with reasons. Do not alter the output to make it match the example.

<figure class="portal-shot" id="portal-agents">
<img src="../../web/assets/portal/03-agent-versions.png" alt="Actual Agents list showing baseline, iq, and optimized agents and their versions" width="1440" height="750" loading="lazy">
<figcaption><strong>Screen 03 · Build → Agents.</strong> This existing environment shows all three stages together. Match Name, Version, and Type to the local agent records. Running is a service state, not a quality PASS or user approval. It is normal for stages you have not created yet to be absent. <a href="../../web/assets/portal/03-agent-versions.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-baseline">
<img src="../../web/assets/portal/04-baseline-playground.png" alt="Baseline Agent Playground showing Model, Version, Instructions, and a configuration without retrieval tools" width="1440" height="1000" loading="lazy">
<figcaption><strong>Screen 04 · Baseline → Playground.</strong> Check Model and Version above, and Instructions, Tools, and Knowledge on the left. With the same instructions, the tool connection distinguishes the baseline from IQ. The chat is empty because no new message was sent; read LIVE responses in the CLI's outputs.jsonl. <a href="../../web/assets/portal/04-baseline-playground.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<a id="calibration"></a>

**Run · calibrate the business Judge, paid:**

Score 16 synthetic references. The normal plan is 16 policy-Judge requests plus 15 retrieval-Judge requests for references with retrieved context: **31 requests**. This is not an actual bill; check the remaining authorization before running it.

```bash
python -m lab --config "$LAB_ENV_FILE" judge calibrate --calibration-id cal-01 --confirm
```

**Command explained:** Sends fixed calibration answers to the policy and retrieval Judges and measures agreement with the reference pass/fail labels. `--calibration-id cal-01` identifies `calibration/cal-01/`. Results remain in `report.json`. The command neither reruns the agent nor creates new reference answers. **31 is the planned Judge request count**, not the token count or cost. Do not delete the calibration ID and repeat until the score looks good.

<p class="output-label" id="example-calibration">Example output · calibration completed, but quality is HOLD</p>

```json
{
  "execution_status": "completed",
  "sample_count": 16,
  "all_dimensions_agreement_rate": 0.9375,
  "critical_false_accept_count": 0,
  "quality_status": "HOLD"
}
```

**How to read it:** Only 15 of 16 examples agree across all dimensions. Even with zero critical false accepts, **less than complete agreement means HOLD**. Preserve `calibration/cal-01/report.json`, stop paid progression, and record the reason and unrun steps in [the closing record](#cleanup).

<p class="share-checkpoint" id="share-calibration">Discuss · can we trust this scorer for the next evaluation?</p>

- **Actual results:** Share your calibration report's sample count, all-dimensions agreement rate, critical false-accept count, and `quality_status`. Use **your run's values**, not the example.
- **Representative case:** In `rows`, read one answer, score, and explanation where the reference and Judge disagree. If none disagree, explain an agreement using the evidence.
- **Next decision:** Complete: “The scorer can be wrong too, so we will continue/hold because ___.” You are evaluating **scorer reliability**, not measuring agent improvement.

**Continue only after calibration passes.** Confirm **all** of: `execution_status: completed`, `quality_status: PASS`, `all_dimensions_agreement_rate: 1.0`, and `critical_false_accept_count: 0`. Do not proceed on `completed` alone or bypass calibration by changing evaluators or rescoring.

<p class="explanation-heading" id="hold-actions">After evaluation · does HOLD mean continue or stop?</p>

**Read the failed check and its cause before interpreting the word HOLD.** This table is a way to decide what to do next, not a rule for changing gates.

| What you see | Meaning | Next action |
|---|---|---|
| Calibration `quality_status: HOLD` | Insufficient evidence to trust the scorer | Stop paid progression; review reference labels and Judge reasons. Record later steps as not run |
| `heldout_test_only`, `minimum_test_rows`, or `fresh_holdout_bound` on dev/smoke | Development diagnostics, not a final test | Check **other failures**, calibration, and authorization before the next improvement step. Do not relabel the result PASS |
| No critical cases in the diagnostic sample | No evidence about critical cases yet | Do not claim safety passed; inspect them in the prescribed later data scope |
| Unmeasured `groundedness_*` on the no-retrieval baseline | No retrieved evidence was used during generation | Keep it separate from policy correctness/relevance. Inspect actual context after connecting IQ |
| API/JSON errors, unexpected missing scores, or model/data mismatches | Execution, measurement, or contract problem | Stop and inspect raw errors/IDs. Do not hide it with different instructions or a new run ID |
| Noncritical quality failures in baseline/IQ | Specific answers need improvement | Record cases and reasons; decide whether to improve knowledge or instructions. Check calibration, errors, and critical failures separately |
| Critical failure or regression beyond tolerance | A risk that averages cannot offset | Hold the candidate and review the problematic claim, authority, and conditions |
| HOLD on the final fresh test | The candidate was not accepted under the fixed criteria | Preserve results and plan the next experiment. Do not tune against or regenerate the final questions |

**Run · score saved baseline answers with the calibrated Judge, paid:**

```bash
python -m lab --config "$LAB_ENV_FILE" judge score --run-id baseline-smoke --interval-seconds 65 --confirm
python -m lab score --run-id baseline-smoke
python -m lab explain --run-id baseline-smoke
```

**Commands explained:**

| Command | What it does and produces |
|---|---|
| `judge score --run-id baseline-smoke ... --confirm` | The **paid** step that scores the three saved answers. Separates policy correctness/relevance from groundedness when actual retrieval exists, and writes `judge-scores.json` and `business-judge/`. It does not regenerate agent responses. |
| `score --run-id baseline-smoke` | **Locally aggregates** response JSON, routing, citation checks, and saved Judge scores into `summary.json` and `report.md`. It does not call the Judge again. |
| `explain --run-id baseline-smoke` | **Reads only** those aggregates and actual Judge reasons. Run `score` first. It writes no new scores or approvals. |

**Where are the scores?** This path's business-Judge reports are local files. They are not managed evaluations automatically registered in Foundry's **Evaluations** list. Do not resubmit an evaluation because the run is absent from the portal. A separate managed-evaluation exercise appears only in [facilitator diagnostics](facilitator.md#diagnostics).

**The final `explain` command is read-only.** It displays criteria, observed values, scores for every case, and **up to three detailed case explanations**, prioritizing critical, regressed, and problematic cases. It connects the question, answer, policy/retrieved context, scores, Judge reasons, and improvement suggestions. Actual reasons come from **`reasons.policy` / `reasons.retrieval`** in `judge-scores.json`; they are not newly generated. Long context is excerpted for display, while the source is preserved.

`score` produces local scores from saved responses; `explain` reads those results. Running `explain` again neither calls a model nor changes evaluation files. **Exit code 0 means the explanation was displayed successfully, not that quality passed.**

<p class="share-checkpoint" id="share-baseline">Discuss · use the baseline to identify what needs fixing</p>

- **Actual results:** State the **three-case** scope of `baseline-smoke`, format pass rate, route accuracy, policy correctness, **scored rows / total**, and errors. Groundedness unavailable because there was no retrieval is neither zero nor perfect.
- **Representative case:** For one case ID in `explain`, connect **actual response → three scores → two Judge reasons → suggested improvement**. Does your initial judgment agree with the Judge? Which sentence matches or violates policy?
- **Next decision:** Identify one knowledge problem IQ could address. If every answer was appropriate, report that honestly. **You need a before-state to explain later changes.**

<p class="explanation-heading" id="worked-evaluation">Connect the evidence · answer → score → reason → improvement</p>

**The answers, scores, and interpretations below are AI-authored teaching examples, not actual run results.** A real Judge need not assign these scores. Read your results using `explain`.

> Question: “I bought my first monthly subscription on September 10, and today is September 15. Please refund it.”

<table class="worked-comparison">
<thead><tr><th>Observation</th><th>Authored before-example</th><th>Authored after-example</th></tr></thead>
<tbody>
<tr><td>Answer</td><td>“You are within 14 days, so your refund has been approved and the money will arrive tomorrow.”</td><td>“Please confirm the payment time/time zone and whether paid jobs ran or credits were used. No refund has been approved or processed yet.”</td></tr>
<tr><td>Action</td><td><code>answer</code>, asserting approval</td><td><code>clarify</code>, checking missing conditions</td></tr>
<tr><td>Authored policy-correctness score</td><td><strong>1</strong> — invents approval and payment</td><td><strong>5</strong> — asks for required conditions and respects execution authority</td></tr>
<tr><td>Retrieval groundedness</td><td><strong>Unmeasured</strong> — no actual retrieval</td><td><strong>Unmeasured</strong> — no actual retrieval</td></tr>
<tr><td>Reason to inspect</td><td>Turns eligibility to apply into completed approval/payment</td><td>Distinguishes checking conditions from executing an action</td></tr>
<tr><td>Next judgment</td><td>Hold: fabricated completion</td><td>A sensible direction for this case, but overall quality and operational approval remain undecided</td></tr>
</tbody>
</table>

**Improvement rules to look for in the instructions:** Ask the minimum questions needed to establish missing conditions; distinguish eligibility from approval; never promise completion without a real execution tool and evidence. Use these to review candidate instructions, not to overwrite actual instruction or score files with this example.

| Problem in actual results | First place to investigate |
|---|---|
| Retrieved context is outdated or irrelevant | IQ policy documents, effective dates, and retrieval results |
| Evidence is correct but conditions, route, or authority are misinterpreted | Instruction decision rules, informed by actual answers and Judge reasons |
| JSON format or `needs_human` is wrong | Output contract and routing instructions |
| API/evaluation errors or calibration disagreement | Environment, measurement, or evaluator/reference issues—not evidence of answer improvement |

**After a change, check the same dev questions again.** The IQ and Agent Optimizer steps below do this. A polished example or longer instructions do not establish improvement.

**Completion check:** You have inspected the actual agent version, three responses, calibration report, and differences between your judgment and the Judge's. Do not substitute policy text for missing baseline retrieval evidence. Smoke/dev are not final tests: distinguish their `HOLD` from **calibration HOLD**, and never hide errors or missing scores.

<p class="step-next no-print"><a href="#iq" data-next-step>Next: 04. Connect knowledge →</a></p>

## 04. Connect knowledge with IQ {#iq}

<div class="lab-concept" aria-label="Step 04 learning objectives">
<p><strong>What you will explore:</strong> Foundry IQ knowledge bases, Azure AI Search, and agent MCP tool calls. RAG retrieves relevant documents as evidence for an answer. Foundry IQ combines knowledge sources and retrieval planning in a reusable knowledge base.</p>
<p><strong>Why it matters:</strong> The model does not inherently know this company's latest refund rules. Rather than repeatedly copying policies into instructions or memorizing them in model weights, retrieve the real documents and preserve the evidence behind the answer. Successful retrieval alone does not guarantee correct policy interpretation.</p>
<p><strong>How you will explore it:</strong> Keep the instructions and model fixed, make eight policies searchable, and connect IQ as a tool. Check direct retrieval diagnostics, actual agent tool use, and answer scores separately, in that order.</p>
</div>

**Your task:** Add only a real knowledge-retrieval tool to the same instructions. Use the dedicated environment's embedding deployment and the eight synthetic Contoso policies.

| Term | Meaning and what to observe in this lab |
|---|---|
| Embeddings / vector index | Numeric representations help find semantically similar content. This implementation uses actual 1,536-dimensional vectors and an HNSW/cosine index. |
| Vector-only / hybrid | The former uses semantic similarity; the latter combines keyword and vector search. Compare top document IDs, content, and effective dates. Do not treat different retrieval-score scales as comparable quality scores. |
| Knowledge source / knowledge base | A source connects searchable content; a base specifies which sources to search and how. Here, one Search index is connected as one source. |
| Agentic retrieval / planner | Plans subqueries for complex questions and returns sources and activity. This implementation uses `low` reasoning and `extractiveData` so the agent answers from retrieved source material. |
| MCP | Model Context Protocol lets the agent discover and call tools. Here, `knowledge_base_retrieve` retrieves knowledge; it does not issue refunds or execute tickets. |

**The actual flow:** Customer question → versioned agent → IQ MCP tool → knowledge base → Search policy documents → tool output → final answer. `retrieved_context` must be the tool output returned in this run, not evaluator `context` or a reference answer. Project-managed-identity authentication in this lab does not establish that per-user document permission filtering has been tested.

Product background: [Foundry IQ concepts and components](https://learn.microsoft.com/azure/foundry/agents/concepts/what-is-foundry-iq). Portal and preview API support can change; inspect the actual connection method used by this guide.

**Run · prepare knowledge and check retrieval, paid:**

```bash
python -m lab --config "$LAB_ENV_FILE" iq prepare --confirm
python -m lab --config "$LAB_ENV_FILE" iq vectors --query "최초 월 구독 환불에 필요한 조건은 무엇인가요?" --confirm
python -m lab --config "$LAB_ENV_FILE" iq probe --query "이전 구매와 9월 이후 최초 월 구매의 환불 기한 및 심사 신청 조건을 비교해 주세요." --confirm
```

**Commands explained:**

| Command | What it does and produces |
|---|---|
| `iq prepare --confirm` | Embeds source policies and prepares the Search index, knowledge source, knowledge base, and project MCP connection. Preserves `knowledge/setup.json`, `document-embeddings.json`, and configuration/upload records. It changes remote state and incurs embedding usage and Search hosting costs. |
| `iq vectors --query ... --confirm` | Directly compares vector-only and hybrid results for the same query. The Korean query asks, “What are the conditions for refunding a first monthly subscription?” `--query` is a retrieval query, not a question sent to an agent. Results go to `knowledge/probes/`; embedding/search usage is incurred. |
| `iq probe --query ... --confirm` | Sends a complex question to the knowledge base: compare refund deadlines and review-application conditions for earlier purchases versus first monthly purchases from September onward. Inspect `modelQueryPlanning`, activity, and sources. Preserves raw results in `knowledge/probes/` and the first response in `knowledge/retrieve-response.json`. Search/planner usage is incurred. |

Check in order: **actual 1,536-dimensional embeddings and index/KB readiness → vector-only and hybrid retrieval → IQ `modelQueryPlanning`, retrieval activity, and sources**. An index or configuration alone does not prove successful retrieval. Do not copy these diagnostic results into an agent's `retrieved_context`.

<figure class="portal-shot" id="portal-knowledge">
<img src="../../web/assets/portal/05-knowledge-base.png" alt="Actual IQ knowledge base configuration showing the planner, Low reasoning, Extractive data, and an Azure AI Search Index source" width="1440" height="1100" loading="lazy">
<figcaption><strong>Screen 05 · Build → Knowledge → your knowledge base.</strong> Find the name recorded in knowledge/setup.json and compare the planner deployment, Low, Extractive data, and connected source. Active is a source state, not a retrieval or answer-quality score. Do not change the CLI configuration again with Save or Use in an agent. <a href="../../web/assets/portal/05-knowledge-base.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-iq-agent">
<img src="../../web/assets/portal/06-iq-agent-knowledge.png" alt="Actual knowledge base connected under Knowledge in the IQ agent's Playground" width="1440" height="1000" loading="lazy">
<figcaption><strong>Screen 06 · IQ Agent → Playground → Knowledge.</strong> The portal displays the existing MCP connection as a Knowledge card. An empty Tools list does not necessarily mean IQ is disconnected. Instructions were collapsed for readability, not changed. A visible connection is not proof of invocation: inspect the MCP output in runs/iq-dev too. <a href="../../web/assets/portal/06-iq-agent-knowledge.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Run · all 12 IQ dev cases and the same Judge, paid:**

```bash
python -m lab --config "$LAB_ENV_FILE" agent --stage iq --confirm
python -m lab --config "$LAB_ENV_FILE" run --stage iq --split dev --run-id iq-dev --interval-seconds 65 --confirm
python -m lab --config "$LAB_ENV_FILE" judge score --run-id iq-dev --interval-seconds 65 --confirm
python -m lab score --run-id iq-dev
python -m lab explain --run-id iq-dev
```

**Commands explained:**

| Command | What it does and produces |
|---|---|
| `agent --stage iq --confirm` | Creates a version using the baseline's instructions/model plus IQ MCP, recorded in `agents/iq.json`. Creation itself does not send questions. |
| `run --stage iq --split dev --run-id iq-dev ...` | Omitting `--limit` runs **all 12 dev cases**. Preserves actual MCP calls/outputs and responses in `runs/iq-dev/`. Model, search, and planner usage is incurred. |
| `judge score --run-id iq-dev ...` | Pays the same business Judge to score saved answers. Groundedness uses only this run's actual MCP context. |
| `score --run-id iq-dev` | Locally aggregates rule checks and saved scores for 12 cases. Error/missing rows stay in the denominator. |
| `explain --run-id iq-dev` | Reads actual values, HOLD causes, and case reasons. Because this sample is larger, do not directly compare its overall mean with the three-case baseline mean. |

<p class="output-label" id="example-iq-report">Example output · an authored excerpt from explain, in its original Korean</p>

```text
# 평가 결과 해설
- 실행: iq-dev / 단계: iq / 분할: dev / 12건
- 기준: 현재 config/gates.json; 최종 최소 표본 20건
- 게이트 결과: **HOLD** / 운영 승인: **not_granted**

| 평가 항목 | 실제 값 | 기준 | 관측 범위 |
| 업무 정확성 | 4.25 | 평균 ≥4 | 점수 12/12; 누락 0; 척도 [1.0, 5.0] |
| 검색 근거성 | 4.50 | 평균 ≥4 | 점수 12/12; 누락 0; 척도 [1.0, 5.0] |
```

**How to read it:** The example reports `iq-dev`, 12 dev cases, HOLD, and no operational approval. Policy correctness is 4.25 and retrieval groundedness 4.50; both have 12/12 scores and no missing values. High averages alone do not pass the gates. Read the **HOLD causes and next checks** for scope, gaps, errors, and critical failures, then the **case explanations** for actual answers and Judge reasons. Even this illustrative 12-case dev run is not a final test. Inspect your complete report for other failures.

<p class="share-checkpoint" id="share-iq">Discuss · did retrieval also improve the business answer?</p>

- **Actual results:** Read `groundedness` and `policy_correctness` for all **12** `iq-dev` cases, with **their respective scored counts, missing values, and errors**. Citation IDs alone do not establish groundedness.
- **Representative case:** Compare answer and policy decisions for the **three case IDs shared with the baseline**. Inspect the actual MCP context for each response. **Do not compare the overall means of three baseline cases and 12 IQ cases.**
- **Next decision:** Complete: “The retrieved evidence is ___, but the business judgment is ___, so we should improve the instruction about ___.” **An answer faithful to retrieval can still be wrong for the business.**

**Completion check:** You have the actual 12 dev responses, `knowledge_base_retrieve` calls/MCP outputs, business scores, and reasons. **`iq-dev`** is the comparison baseline for the next step. `--interval-seconds 65` spaces cases; it does not retry. Preserve and stop on 429s, 403s, or missing context. Do not rescore the same run through another evaluation path.

<p class="step-next no-print"><a href="#optimize" data-next-step>Next: 05. Improve instructions →</a></p>

## 05. Improve instructions with Agent Optimizer {#optimize}

<div class="lab-concept" aria-label="Step 05 learning objectives">
<p><strong>What you will explore:</strong> Agent Optimizer generates and compares instruction candidates using evaluation data and criteria. It does more than make a prompt longer: it evaluates the selected agent version and candidates on the same task.</p>
<p><strong>Why it matters:</strong> Correct retrieval can still be followed by missing conditions or a wrong action. Instructions may need improvement rather than more knowledge. But an improved average can conceal critical failures or overfitting.</p>
<p><strong>How you will explore it:</strong> Fix the scope at 12 dev cases, the same model and IQ connection, instruction-only changes, one job, and one candidate. Read the service's recommendation, then check it independently with the business Judge on the same questions. This is neither SFT of model weights nor a single-prompt rewriting feature.</p>
</div>

**Your task:** Use the error-free, completed 12-case `iq-dev` run and its actual MCP output for **one Agent Optimizer job with one candidate**. Keep the model and IQ connection fixed; change instructions only.

Compare instructions **before → after**. `baseline` and `iq` use the same [`prompts/baseline.txt`](../../prompts/baseline.txt); `optimized` uses `optimizer/selected-prompt.txt` imported from the actual service result. This is not a choice between prewritten `v1.txt`/`v2.txt` files. Longer instructions are not, by themselves, evidence of improvement.

**Run · prepare input locally:**

```bash
python -m lab optimize --run-id iq-dev
python -m json.tool "$LAB_ARTIFACTS_DIR/optimizer/handoff.json"
```

**Commands explained:**

| Command | What it does and produces |
|---|---|
| `optimize --run-id iq-dev` | Verifies the completed IQ dev run, actual tool output, and source hashes, then **locally prepares** original instructions, `dev-upload.jsonl`, and `handoff.json` in `optimizer/`. Despite its name, it does not submit a service job or incur model costs. Do not recreate an existing handoff. |
| `json.tool .../handoff.json` | Reads the upload data, exact agent name/version, and source hashes. This handoff ties local records to portal selections. |

<p class="output-label" id="example-optimizer-handoff">Example output · excerpt from handoff.json</p>

```json
{
  "kind": "agent-optimizer-handoff",
  "status": "PREPARED_NOT_SUBMITTED",
  "source_run_id": "iq-dev",
  "source_split": "dev",
  "test_data_included": false
}
```

**How to read it:** Only input preparation is complete. **No service job or new agent exists yet.** Use this file's `agent_name` and `agent_version` on the next screen.

**Submit this job and download its candidate in the Foundry portal.** Screens in the other steps are for comparing CLI results, not repeating them. In the same account/project, choose **Build → Agents → the IQ agent in the handoff → Optimize tab → Optimize button → Agent**. These were the actual menu labels at capture time; another UI version may show **Create optimization run**. **Cost** is not this lab's target. Apply the following settings alongside the [official prompt-agent guide](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent).

| Screen | Lab setting |
|---|---|
| Target | The exact IQ agent version in the handoff. Under **Choose targets**, select **Instruction only**. Clear Tool description and Model |
| Models | The actual optimizer/judge deployments from the manifest. **Disable model comparison**, including Compare across models in older UI |
| Max candidates | Set **1**, rather than accepting the default. Submit only one job |
| Data / Dataset | **Select dataset and criteria → Upload dataset** → the actual `$LAB_ARTIFACTS_DIR/optimizer/dev-upload.jsonl` file. Do not use Generate data or another dataset |
| Criteria | **Relevance + Task Adherence**, threshold **4** each. Check input columns `query`, `context`, and `ground_truth` |
| Review | Confirm the same model/IQ MCP, 12 dev cases, and approved cost/task scope before submission |

**Understand the screen:** Relevance checks whether an answer is useful for the question; Task Adherence checks compliance with instructions and constraints. Neither replaces all detailed Contoso policy checks. This wizard has no column mapping, so preserve the prepared JSONL column names. Do not append `context` or `ground_truth` to the agent's question just because an evaluator does not use those columns.

**Immediately before Submit:** A cost estimate is not a spending cutoff. Usage may include original/candidate agent runs, search, Judges, and instruction generation: “one job” does not mean “one model call.” If a completed job already exists, open it rather than submitting another wizard. Agent Optimizer is in preview; if the menu is missing, check access and support with the operator.

<figure class="portal-shot" id="portal-optimizer-target">
<img src="../../web/assets/portal/07-optimizer-target.png" alt="Unsubmitted Agent Optimizer Target screen with Instruction only, one candidate, and planner and judge deployments selected" width="1210" height="968" loading="lazy">
<figcaption><strong>Screen 07 · Target settings, not submitted.</strong> Select Instruction only under Choose targets, then check Max candidates 1 and Evaluation model. At capture time the defaults were two candidates and the agent model for evaluation, so they were not accepted unchanged. “Token cost left free” in Goal means cost is not constrained as an optimization target; it does not mean calls are free. <a href="../../web/assets/portal/07-optimizer-target.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-optimizer-data">
<img src="../../web/assets/portal/08-optimizer-dataset.png" alt="Unsubmitted Agent Optimizer Dataset screen with Select dataset and criteria and the Upload dataset button" width="1210" height="968" loading="lazy">
<figcaption><strong>Screen 08 · After choosing Select dataset and criteria.</strong> The wizard proceeds through Dataset → Criteria → Review. Use Upload dataset on the right for the prepared 12 dev cases. No upload or submission was made for this screenshot. Do not select another run's dataset from the list. Creator details are masked. <a href="../../web/assets/portal/08-optimizer-dataset.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**A common source of confusion:** If Generate data asks for Application Insights access or shows Resolve, do not expand permissions for this lab. Choose **Select dataset and criteria**, since you already have a file. Check its row count and columns before Next. You need not upload again or resubmit a completed job to follow the screenshots.

Wait **no more than 60 minutes per job**, within your current authorization. On timeout or access/support blockers, record the state and stop. Do not claim completion by substituting Prompt Optimizer, handwritten instructions, or another model.

**Once the job is `succeeded`:** Read the original/candidate instruction diff, case scores, and regressions. Service ranking does not replace this lab's business Judge or operational approval. The candidate may include examples derived from dev, so an independent test is necessary.

<figure class="portal-shot" id="portal-optimizer-results">
<img src="../../web/assets/portal/09-optimizer-results.png" alt="Actual completed Agent Optimizer run showing one candidate at 0.708 versus a 0.677 baseline, tokens, downloads, and View changes" width="1440" height="1000" loading="lazy">
<figcaption><strong>Screen 09 · Results from an existing completed run.</strong> 0.677 → 0.708 is the service's Task-weighted average on a 0–1 scale. Read Avg tokens and Avg latency too. Locate View changes, Download JSON, and Download config, but do not click Promote candidate. The existing lab's business-quality decision remains HOLD. <a href="../../web/assets/portal/09-optimizer-results.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-optimizer-diff">
<img src="../../web/assets/portal/10-optimizer-changes.png" alt="Side-by-side comparison of the actual baseline and candidate system_prompt returned by the service" width="1038" height="622" loading="lazy">
<figcaption><strong>Screen 10 · View changes.</strong> Compare the original system_prompt on the left with the candidate on the right. Long green additions do not necessarily improve it. Review dev-derived “built-in policy facts,” route definitions, and authority boundaries too. Do not interpret tools: [] in the export as an instruction to remove IQ. <a href="../../web/assets/portal/10-optimizer-changes.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-evaluation">
<img src="../../web/assets/portal/11-evaluation-results.png" alt="Actual managed evaluation of an Optimizer candidate showing Relevance 12/12, Task adherence 8/12, and individual question results" width="1440" height="1000" loading="lazy">
<figcaption><strong>Screen 11 · Candidate results → Score details → evalrun link.</strong> The existing candidate's service evaluation reports Relevance 12/12 and Task adherence 8/12. Distinguish Completed from each criterion's pass rate. Scroll Detailed metrics result horizontally to read reasons and other metrics. These are not the local Contoso business-Judge scores or final fresh-test results. <a href="../../web/assets/portal/11-evaluation-results.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Do not confuse three different numbers:** screen 09's 0–1 ranking, screen 11's per-criterion pass rates, and the 1–5 business scores from reevaluation below are different aggregates. In this example, important business failures remained despite a recommended candidate. The screenshots are neither expected scores for your run nor acceptance criteria.

<p class="share-checkpoint" id="share-optimizer">Discuss · why did the Optimizer recommend this candidate?</p>

- **Actual results:** Read **original versus candidate** scores by evaluator, with the scales, 12-case dev scope, and job/candidate IDs. Do not combine a 0–1 ranking and this lab's 1–5 Judge scores as if they were the same measure.
- **Representative case:** Connect the instruction diff to a representative response and explain what changed. If the service failed or did not finish, do not invent scores or improvement rates.
- **Next decision:** Complete: “Under the service's criteria, ___, so we will **reevaluate**/hold this candidate.” **An Optimizer recommendation supports candidate selection, not final acceptance or operational approval.**

Save the completed run's **Download JSON** and the candidate's **Download config** to these private filenames. In the file picker, use the **actual directory from step 02**, not the literal text `$LAB_ARTIFACTS_DIR`. Do not promote the portal's active version; the CLI below creates a separate lab version.

| What to save | Path under `$LAB_ARTIFACTS_DIR` |
|---|---|
| Completed run JSON | `optimizer/agent-optimizer-final.json` |
| Candidate config JSON | `optimizer/agent-optimizer-candidate-config.json` |

**Run · import the service candidate:**

```bash
python -m lab --config "$LAB_ENV_FILE" optimizer-agent-result --result "$LAB_ARTIFACTS_DIR/optimizer/agent-optimizer-final.json" --candidate "$LAB_ARTIFACTS_DIR/optimizer/agent-optimizer-candidate-config.json"
```

**Command explained:** `--result` is the completed-job JSON; `--candidate` is that job's actual winning configuration. The importer checks the original agent/version/instruction hash and instruction-only scope, then locally saves `selected-candidate.json`, `selected-prompt.txt`, and `agent-changes.diff`. It does not call the service, promote in the portal, change models, or create a version. The following command creates a separate version using the imported instructions.

<p class="output-label" id="example-optimizer-candidate">Example output · candidate import excerpt</p>

```json
{
  "kind": "AGENT_OPTIMIZER_PORTAL_CANDIDATE_IMPORT",
  "status": "CANDIDATE_CAPTURED_NOT_LAB_APPROVED",
  "job_id": "EXAMPLE_JOB_ID",
  "candidate_id": "EXAMPLE_CANDIDATE_ID",
  "imported_fields": ["system_prompt"],
  "human_operational_approval": "NOT_GRANTED"
}
```

**How to read it:** Instructions from a real job/candidate have been imported to `selected-prompt.txt`; **lab quality has not passed**. Import instructions only. Do not remove IQ MCP because the exported config says `tools: []`. If files are missing or the contract differs, do not fabricate a result.

**Run · create a new version and reevaluate the same 12 dev cases, paid:**

```bash
python -m lab --config "$LAB_ENV_FILE" agent --stage optimized --confirm
python -m lab --config "$LAB_ENV_FILE" run --stage optimized --split dev --run-id optimized-dev --interval-seconds 65 --confirm
python -m lab --config "$LAB_ENV_FILE" judge score --run-id optimized-dev --interval-seconds 65 --confirm
python -m lab score --run-id optimized-dev
python -m lab explain --run-id optimized-dev --baseline iq-dev
```

**Commands explained:**

| Command | What it does and produces |
|---|---|
| `agent --stage optimized --confirm` | Creates a remote **separate candidate version** with the imported `selected-prompt.txt` and the existing model/IQ tools. Records `agents/optimized.json`; does not promote or overwrite the original IQ version. |
| `run --stage optimized --split dev --run-id optimized-dev ...` | Runs the same 12 dev cases against the candidate. Results go to `runs/optimized-dev/`; model/search usage is incurred. |
| `judge score --run-id optimized-dev ...` | Pays the same business Judge to evaluate actual candidate answers. Do not copy portal rankings into business scores. |
| `score --run-id optimized-dev` | Aggregates candidate results locally, preserving the original `iq-dev` report. |
| `explain --run-id optimized-dev --baseline iq-dev` | `--baseline` selects a **saved run ID** for comparison. Computes before/after changes and configured regressions with the same data/Judge locally, without extra model calls. |

**The final command compares saved results for the same questions.** It rejects mismatched datasets, case IDs, Judges, or scales. The existing `compare_runs` engine calculates configured regression tolerances locally without model calls. It does not turn dev's overall HOLD into PASS.

| Automatically calculated diagnostic | Current tolerance |
|---|---|
| Decrease in format, human-flag, or forbidden-claim pass rate | 0 percentage points |
| Decrease in route accuracy or citation pass rate | Up to 5 percentage points each |
| Decrease in mean groundedness or relevance | Up to 0.2 points each |
| Latency increase | No tolerance configured; no automatic verdict |

**Separate automation from human judgment.** `score`/`finalize` checks one run's gates. Before/after regression diagnostics appear only with `explain --baseline`. A person must review **policy-correctness changes, the instruction diff, the validity of actual claims, and final acceptance**. No separate automatic tolerance for a decrease in policy correctness is configured. These diagnostics are not operational approval.

<p class="share-checkpoint" id="share-optimized">Discuss · did the candidate improve under the same business criteria?</p>

- **Actual results:** In `explain --baseline`, read the **same-question automatic regression diagnostics**: original/candidate values, decrease, tolerance, and unmeasured items. Check **scored rows / total**, errors, missing values, and individual critical cases—not just means.
- **Representative case:** Connect each case's **previous final answer, current answer, before/after scores, and current Judge reasons**. Explain an improvement and a regression or remaining weakness. If none is observed, say so. Read the original run's `explain` for its previous reasons.
- **Next decision:** Complete: “___ improved, but ___ remains a risk, so we will freeze/hold the candidate.” **Average gains cannot offset critical failures or regressions.**

**Completion check:** Compare the **same case IDs** in `iq-dev` and `optimized-dev` and explain answer, score, and regression changes. Do not overstate this as the isolated causal effect of prompt wording with retrieval variability fully controlled. If critical regressions, errors, or missing values remain, do not accept or resubmit the candidate; record HOLD.

<p class="step-next no-print"><a href="#decision" data-next-step>Next: 06. Decide and finish →</a></p>

## 06. Decide and finish {#decision}

<div class="lab-concept" aria-label="Step 06 learning objectives">
<p><strong>What you will explore:</strong> Freezing an experiment, evaluating a fresh holdout, and connecting traces and feedback. A freeze is a local contract that fixes candidate/evaluation hashes. A holdout contains questions not used for candidate selection. A trace records the execution path of actual model and tool calls.</p>
<p><strong>Why it matters:</strong> Stop changing the candidate before testing fresh questions, so you do not adopt an agent that only fits the development set. You also need to trace which version answered and what evidence it used when investigating later problems.</p>
<p><strong>How you will explore it:</strong> Only when prerequisites pass, freeze and run fresh12 once. Record the verdict, unrun steps, and absence of human approval separately. This repository's governance commands do not configure Foundry operational policy or authorize a real deployment.</p>
</div>

**Your task:** Freeze the candidate, evaluate it once on new questions, and record its actual state and next action. **If earlier steps are blocked or calibration/candidate evidence is insufficient, skip the paid final test below and complete only [the closing record](#cleanup).** This is not a fallback that turns “not run” into success.

**Run · freeze and create a fresh holdout only after calibration and candidate review:**

```bash
python -m json.tool config/evaluators/fresh-holdout-gates.v1.json
python -m lab --config "$LAB_ENV_FILE" freeze --freeze-id selected-v1 --stage optimized --calibration-id cal-01
python -m lab holdout create --freeze-id selected-v1 --holdout-id fresh-01 --count 12
```

**Commands explained:**

| Command | What it does and produces |
|---|---|
| `json.tool .../fresh-holdout-gates.v1.json` | Reads the fresh-sample contract, separate from original test20, locally. Do not edit thresholds. |
| `freeze --freeze-id selected-v1 --stage optimized --calibration-id cal-01` | Seals the exact agent, calibration, policy, retrieval, evaluator, and gate state in `governance/freezes/selected-v1.json`. `--config` checks environment consistency; no remote query, deployment, or training occurs. The freeze itself is not a quality PASS. |
| `holdout create --freeze-id ... --holdout-id fresh-01 --count 12` | **After freezing**, generates, deduplicates, and registers 12 synthetic questions from fixed authored templates in `governance/holdouts/fresh-01/`. It does not call a model or data-generation service. |

**Check before continuing:** The freeze binds the agent version and prompt/model/search/evaluator/gates/data/calibration hashes. **Fresh12, generated and registered after freezing**, must reference that freeze. Do not replace original test20 or lower `minimum_test_rows: 20` in `config/gates.json`. These synthetic template variations are not independent customer samples.

**Run · final 12-case evaluation of the frozen candidate, paid:**

```bash
python -m lab --config "$LAB_ENV_FILE" run --stage optimized --split test --run-id optimized-fresh --freeze-id selected-v1 --holdout-id fresh-01 --interval-seconds 65 --confirm
python -m lab --config "$LAB_ENV_FILE" judge score --run-id optimized-fresh --interval-seconds 65 --confirm
python -m lab score --run-id optimized-fresh
python -m lab explain --run-id optimized-fresh
python -m json.tool --json-lines "$LAB_ARTIFACTS_DIR/runs/optimized-fresh/outputs.jsonl"
```

**Commands explained:**

| Command | What it does and produces |
|---|---|
| `run ... --split test --freeze-id selected-v1 --holdout-id fresh-01` | Here, `--split test` selects final-test mode using the **specified fresh holdout**, not the ordinary 20 rows in `data/splits/test.jsonl`. Freeze/calibration checks must pass before paid inference begins. |
| `judge score --run-id optimized-fresh ...` | Pays the Judge bound to the freeze to score the actual final responses. Do not rescore with a more favorable evaluator. |
| `score --run-id optimized-fresh` | Aggregates saved results locally into the final report without altering responses or Judge scores. |
| `explain --run-id optimized-fresh` | Reads actual causes under the frozen sample/gate contract. Do not use dev as `--baseline`; those are different questions. |
| `json.tool --json-lines .../outputs.jsonl` | Locally displays all final responses, including first turns and explicit follow-ups. |

This explanation uses **the frozen fresh-sample contract and gates**. Do not substitute current development gates or weaken original test20's criteria. Do not attach the different dev questions as `--baseline`.

There are 12 final cases; an explicit follow-up conversation makes a normal capture **13 turns**. Read the initial `clarify`, scripted-user provenance, and final answer—not only the last turn. `schema_and_clarify_only/not_semantic_safety` describes initial format checks, not assurance of the initial explanation's semantic safety.

Do not change instructions, models, data, or evaluators after freezing, or regenerate the holdout because results are poor. Errors and missing scores remain in the denominator. For an interrupted batch, follow [the facilitator's resume guide](facilitator.md#resume) with the same ID and inputs. Never repeat an uncertain submission or a completed Judge attempt.

<a id="review"></a>

**Run · final verdict, local:**

```bash
python -m lab governance finalize --freeze-id selected-v1 --run-id optimized-fresh
```

**Command explained:** Verifies that the freeze, final responses, Judge, and summary hashes agree, then records **one local verdict** in `governance/results/selected-v1.json`. It neither calls a model, deploys automatically, nor grants human operational approval. Skip it if the final run was blocked and does not exist.

<p class="output-label" id="example-final-verdict">Example output · execution completed while quality remains HOLD</p>

```json
{
  "sample_count": 12,
  "execution_status": "completed",
  "judge_execution_status": "completed",
  "quality_status": "HOLD",
  "manual_operational_approval": "not_granted",
  "production_ready": false
}
```

**How to read it:** API execution, scoring completion, quality, and operational approval are separate states. Here, **execution finished but acceptance is on hold**. Connect `passed: false` checks under `gate.checks` with causes, actual claims, and Judge reasons from `explain`. Do not relabel AI review as human review.

If a final verdict already exists, do not run `finalize` again. Read it with `python -m lab governance status --freeze-id selected-v1`. This `status` command reads the freeze's existing verdict/attempt state locally; it creates neither another verdict nor Azure work. Use [the review format](facilitator.md#review) only for actual human records, without hiding missing approval.

<p class="share-checkpoint" id="share-holdout">Discuss · does it work on new questions, and should we accept it now?</p>

- **Actual results:** Read scores, coverage, missing values, critical results, and final `quality_status` for `optimized-fresh`'s **12 new post-freeze cases**. Report execution completion and human operational approval separately.
- **Representative case:** Compare one appropriate answer and one critical failure or clarification conversation with policy. Inspect initial answers and user follow-ups, not just final answers.
- **Next decision:** Explain acceptance or HOLD with evidence. **The 12 dev and 12 fresh questions differ, so their means do not form a before/after improvement rate.** Strong dev scores do not guarantee generalization; passing a small synthetic test is not production safety certification.

<a id="operate"></a>

**Run · observe the actual final run, read-only:** Reuse the monitoring ID set in step 02.

```bash
python -m lab --config "$LAB_ENV_FILE" control-plane --run-id optimized-fresh --app-insights-id "$APPLICATIONINSIGHTS_RESOURCE_ID"
```

**Command explained:** Queries the specified Application Insights resource for model/tool/evaluation traces tied to this run's actual response IDs and agent version, over **the last day**. Saves timestamped observations under `runs/optimized-fresh/control-plane/`. It starts no inference and creates no monitoring connection or policy. Log ingestion/retention costs are separate. If the final run was not executed, skip this too and record “no final run.”

<p class="output-label" id="example-traces">Example output · traces have not yet been observed</p>

```json
{
  "status": "NOT_VERIFIED_NO_TRACES",
  "observed_rows": 0,
  "error_absence_claim": false,
  "cost": {"status": "NOT_OBSERVED"}
}
```

**How to read it:** Zero traces means **observation is unverified**, not zero errors or zero cost. Partial linkage is `PARTIAL`; confirmed required linkage is `VERIFIED_TRACE_MODEL_TOOL_EVAL_LINKS`. Do not call the model again to manufacture traces. Verify policy enforcement and actual billing separately.

**Find the same response in the portal:** Build → Agents → the relevant agent → **Traces** → choose a **Date range** covering the run → search the actual **response_id** from `outputs.jsonl` → open Trace ID → inspect **Execute Tool / Chat** spans and **Input + Output**. The list may contain several versions and internal Optimizer runs; a matching name alone is insufficient.

<figure class="portal-shot" id="portal-trace-search">
<img src="../../web/assets/portal/12-trace-lookup.png" alt="Actual Foundry Traces screen filtered by an existing iq-dev response ID to find one matching trace" width="1440" height="800" loading="lazy">
<figcaption><strong>Screen 12 · Search by actual response ID.</strong> This lookup uses atlas-dev-001 from an existing iq-dev run to demonstrate the method. It is not the final fresh run. Evaluation is -- for this row; no automatic evaluation linkage is claimed. Estimated cost is not the actual bill. <a href="../../web/assets/portal/12-trace-lookup.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-trace-detail">
<img src="../../web/assets/portal/13-trace-tool-call.png" alt="The same IQ trace's actual MCP knowledge_base_retrieve span with its search question and ATLAS-SUB-001 tool output" width="1440" height="1000" loading="lazy">
<figcaption><strong>Screen 13 · Trace ID → Execute Tool → Input + Output.</strong> This links the same response's MCP query, returned ATLAS-SUB-001 document, and tool/model spans. The trace shows three spans, one chat call, and one tool call. It describes one response's execution path—not a quality PASS or complete observability for the entire run. <a href="../../web/assets/portal/13-trace-tool-call.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

`\u...` in tool output is JSON's Unicode-escape notation. Do not edit raw records to make the screen look cleaner. Check the query, document ID, and stored context together. **If the final test was blocked, keep that state**; do not present these existing IQ screenshots as final-test results.

**Run · record questions for the next improvement cycle, local:**

```bash
python -m lab feedback --run-id iq-dev --feedback-id iq-dev-next-review
```

**Command explained:** Exports actual `iq-dev` failures and response IDs to a **local review queue**, `feedback/iq-dev-next-review.json`. `--feedback-id` names the new review record. It neither authors ground truth nor automatically updates training files, agents, or external services. Skip it if that dev run does not exist.

The queue is tied to real dev failures/response IDs, with empty `ground_truth` and review state `PENDING`. This is not automatic training or deployment. Never move final test/fresh-holdout cases into development or optimization data.

<a id="cleanup"></a>

**Record the outcome and finish—both completed and HOLD paths end here.**

| Record | What to include |
|---|---|
| Examples versus actual execution | DEMO is authored. Label only records with actual version, response, job, or evaluation IDs as LIVE |
| Improvement results | Changed instructions, policy/case/claim evidence, regressions, and missing values |
| Final state | Actual quality result, reasons for HOLD, and blocked steps **not run** |
| Human judgment | Actual review provenance and absence of operational approval. Never label AI as human |
| Observation and retention | Verified/partial/missing traces, the person responsible for checking costs, and the next check time |

**Run · local cleanup plan without deletion:** Read this only if step 02's environment connection succeeded. If you stopped before setup, skip it and record incomplete preparation.

```bash
python -m lab --config "$LAB_ENV_FILE" cleanup
```

**Command explained:** Reads the local ownership ledger and **prints a plan** of cleanup targets and resources that are not automatically deleted. This command invocation has no deletion option and makes no Azure deletion request. Its name does not mean resources or costs have been cleaned up.

**Deletion is not authorized.** Do not add `--confirm-prefix` or delete resources in the portal. Preserve private raw records, experiment contracts, and the new resource group. Closing the terminal may leave Search, logs, and model hosting charges running.

**Completion check:** Finish this sentence with evidence to complete the participant path. Reading checkboxes alone do not establish LIVE completion.

> “We changed ___ in the instructions. Based on policy/response ___ in case ___, we will ___ the candidate. The final test is ___, and human operational approval is ___. The remaining risk and next action are ___.”

**You do not need to complete another lab afterward.** Execution completion is not a quality pass. Explaining a quality HOLD honestly is a valid learning outcome.

If results are absent, report **not run / unmeasured**. Do not present illustrative examples or another run's results as your own. Preserve raw records privately.

<a id="tune"></a>
<a id="troubleshooting"></a>
<a id="sources"></a>

Read references only when needed: [operator setup](admin-setup.md) · [errors, resume, and separate diagnostics](facilitator.md#resume) · [SFT/Frontier appendix](sft-appendix.md) · [data guide](../../data/README.en.md) · [latest verification and sources](verification.md).

The **Dark/Light** control remembers your choice. **Print section** prints the current step; **Save PDF** opens the print dialog for this whole document. Choose Save as PDF there. Print backgrounds always remain light. The footer links to the complete print edition and downloadable PDF, including appendices.

Reference date: **2026-09-30**. Guide version: **v1**. `python -m lab` is this repository's educational tool, not an official Microsoft CLI. Service availability, regions, models, and costs can change. Previous verification does not replace a participant's new run or operational authorization.
