# Great agents start with evaluation · v1 {#좋은-에이전트는-평가에서-시작된다-v1}

<p class="eyebrow">CONTOSO ATLAS CLOUD · ONE LEARNING PATH</p>

**Evaluate your business cases in Foundry, improve instructions with Agent Optimizer, and measure what changed.** Follow these six steps.

<ol class="learning-path" role="list" aria-label="Lab steps">
<li><a href="#start"><strong>01</strong> Prepare the dataset</a></li>
<li><a href="#prepare"><strong>02</strong> Select evaluation criteria</a></li>
<li><a href="#baseline"><strong>03</strong> Run Foundry Evaluation</a></li>
<li><a href="#analyze"><strong>04</strong> Read scores and reasons</a></li>
<li><a href="#optimize"><strong>05</strong> Improve instructions with Agent Optimizer</a></li>
<li><a href="#decision"><strong>06</strong> Reevaluate, compare, and finish</a></li>
</ol>

**Why private/domain evaluations?** Your representative tasks, policy boundaries, and known failures matter more to your application than a public benchmark alone. The synthetic Contoso scenario demonstrates **evaluate → learn → improve → reevaluate**, not production certification.

**Before starting:** The [operator](admin-setup.md#handoff) supplies the isolated project, prepared agent and baseline version, deployment names, and cost/data authorization. Infrastructure is a prerequisite, not another participant lab. Allow processing/discussion time; wait at most **60 minutes per optimization job**.

**Keep one language per experiment.** Use the English file and English agent here, or the separate Korean pair. Switching this website's language does not translate the agent or dataset.

<p class="output-notice" id="portal-screenshots-note"><strong>Real English UI and data:</strong> Screens illustrate the completed English rehearsal, not your own results or a Korean run. Use your own run IDs and read the <a href="verification.md">measured results and limitations</a>. Previewing a wizard is not executing an evaluation.</p>

## 01. Prepare the dataset {#start}

<a id="demo"></a>
<a id="understand"></a>
<a id="data"></a>

<div class="lab-concept" aria-label="Step 01 learning objective">
<p><strong>What:</strong> A small, repeatable set of domain tasks. <strong>Why:</strong> The same questions expose what changed after instruction optimization. <strong>How:</strong> Inspect the supplied JSONL, then upload all 12 cases to an evaluation draft.</p>
</div>

Use **[data/en/optimizer/dev.jsonl](../../data/en/optimizer/dev.jsonl)**, unchanged. It has **12 JSONL rows**, not a JSON array. The source corpus has 100 cases, but only this dev12 file is used in the workshop. Other subsets are unused here.

| Column | Type | Use |
|---|---|---|
| `query` | String | The only input sent to the agent |
| `context` | String | Original policy excerpts kept as evaluator/reviewer reference |
| `ground_truth` | **JSON string** | Structured reference answer, not a generation prompt or precomputed response |

Confirm all 12 records locally and record the file's **SHA-256** from the operator's handoff. Keep the same bytes, registered dataset version, and hash for baseline, optimization, and reevaluation. Do not trim, duplicate, translate, or add a fake `response` column. See the [data contract](../../data/README.en.md#schema).

The prepared agent returns exactly four response keys. These are contract examples, not measured answers:

| Key | Contract |
|---|---|
| `answer` | Nonempty English text; for example, “Please confirm the purchase date.” |
| `citations` | Supporting policy IDs, for example `["ATLAS-REF-001"]` |
| `route` | `answer`, `clarify`, `escalate`, or `refuse` |
| `needs_human` | Boolean; `true` only for `escalate` |

The assistant advises; it does not execute refunds, create tickets, or grant access. A reference to escalation is not evidence that a human was contacted.

**Portal action:** Open [Foundry](https://ai.azure.com/) in the **New experience**, select the operator's project, then **Build → Evaluations → Create → Create new evaluation**.

1. For a fresh baseline agent still at v1, choose **Agent → `contoso-eval-en` → Pin currently latest**, not Latest available, before changes. **Reselect the cleared checkbox and confirm 1 target before Next.** The recorded lab retains candidate v2 but has restored active v1: use explicit versions and the saved baseline, not assumptions about “latest.” The failed `gpt-6-luna` probe was another agent.
2. Set **Scope: Individual turns**, not Full conversations, and **Frequency: One time**, not recurring.
3. Under **Data**, choose **Existing dataset**, not the default Synthetic generation, Benchmarks, or Existing traces.
4. Select **`contoso-eval-en-dev12` version `1`**, registered through this wizard from the unchanged 12-row `data/en/optimizer/dev.jsonl`. Do not upload it again. In a fresh authorized project where it is absent, use **Upload new dataset → name → Choose file → Upload** with that exact file and record the resulting version.
5. Confirm the dataset is selected and previewed, then record its actual registered version. In the observed English wizard, the matching schema **auto-resolved Field mapping**, so the next screen was **Configure agents**. If a schema-dependent mapping screen appears, use **query → query**.

<figure class="portal-shot" id="portal-evaluation-dataset">
<img src="../../web/assets/portal/en/15-evaluation-dataset.png" alt="Foundry evaluation dataset selection and preview for the English dev12 JSONL upload" width="1440" height="1000" loading="lazy">
<figcaption><strong>Dataset selection.</strong> Use Existing dataset and the selected upload. The preview shows only the first five rows; that is not proof that the dataset contains five cases. <a href="../../web/assets/portal/en/15-evaluation-dataset.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Completion signal:** The draft points to the explicit baseline version and the selected 12-row dataset; its local count/hash are recorded. Preview is preparation, not execution. If the file or version differs, correct the draft before proceeding.

<p class="step-next no-print"><a href="#prepare" data-next-step>Next: 02. Select evaluation criteria →</a></p>

## 02. Select evaluation criteria {#prepare}

<a id="environment"></a>
<a id="calibration"></a>
<a id="model-smoke"></a>
<a id="first-infrastructure-failure"></a>

<div class="lab-concept" aria-label="Step 02 learning objective">
<p><strong>What:</strong> Two managed evaluators with different result types. <strong>Why:</strong> A comparison must respect each metric's scale. <strong>How:</strong> Use Relevance threshold 4 and TaskAdherence binary pass 1, with the verified Judge deployment.</p>
</div>

In **Configure agents**, leave the **custom prompt override unset**. Agent input must be **`query` only**. Keep `context` and `ground_truth` separate as evaluator references; do not append either to the question to make an answer look better.

In **Criteria**, the observed portal suggested **23 evaluators**. Remove the extras and retain **Relevance** and **TaskAdherence** only. The Optimizer may display the latter as **Task Adherence**.

| Evaluator | What to inspect | Required setting |
|---|---|---|
| Relevance | Whether the response addresses the question; **1–5** | **Edit Relevance evaluator → Threshold 4 → Update** |
| TaskAdherence | Whether the response follows task instructions; **Binary Pass/Fail, raw 0/1** | **Pass = 1**. If a generic threshold control is shown: **Edit TaskAdherence evaluator → Threshold 1 → Update** |

The [official agent-evaluator definitions](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators) identify TaskAdherence as **binary**. Read its service-returned Pass/Fail; do not interpret a passing `1` as a one-out-of-five score.

In **Model: Judge model**, choose **`lab-judge-luna-dea3cec5`**, not the agent model. Record the two evaluator names, result types, settings, Judge deployment/model version, and dataset version/hash. Keep exactly two evaluators; this correction adds no extra participant exercise.

**Catalog references are not service-version pins.** Catalog links showed `relevance` **v14** and `task_adherence` **v17**, but submitted service criteria had **`evaluator_version` empty/default**. Do not claim that private service rubric versions are fully pinned. Retain the saved evaluation definition and disclose this limit.

**Observe mappings; do not override generated values.** The corrected submission confirmed **Relevance `response={{sample.output_text}}`** and **TaskAdherence `response={{sample.output_items}}`**. UI defaults also showed `query={{item.query}}` and TaskAdherence's `tool_definitions={{sample.tool_definitions}}`. Inspect **Raw JSON**; do not force TaskAdherence back to the UI's earlier output-text binding. These are service bindings, not extra JSONL columns or generation inputs.

**Three model roles are separate.** The request is to use `gpt-6-luna` wherever that role is actually supported, not to force one model into every role.

| Role | Workshop selection boundary |
|---|---|
| Agent answering the questions | **`lab-agent-dea3cec5` → `gpt-4.1-mini` / `2025-04-14`**. Use verified **`contoso-eval-en` v1** with the existing read-only knowledge connection; the `gpt-6-luna` Responses/Agent attempt failed here |
| Evaluation Judge | **`lab-judge-luna-dea3cec5` → `gpt-6-luna` / `2026-09-22`**, verified in the actual managed baseline and candidate evaluations |
| Optimizer instruction generator | **`lab-planner-dea3cec5` → `gpt-5.5` / `2026-04-24`**. The official supported optimization-model list does **not** include `gpt-6-luna` |

**Capability verification is not agent quality.** The earlier `gpt-6-luna` native Relevance check used **one authored compatibility fixture: passed 1 / total 1 / errors 0**; Chat Completions returned READY. That fixture and the completed configuration pilot are separate from the corrected comparison. The [operator model note](admin-setup.md#prepare) records their distinct roles.

Direct Responses and a **pinned `gpt-6-luna` prompt-agent v2** returned **HTTP 500 in this environment**. Keep the verified `gpt-4.1-mini` agent until the provider issue is resolved. This is a failed runtime verification here, not a claim that the model is unsupported everywhere. Catalog visibility is not runtime proof.

The existing `gpt-4.1-mini` model version has an Azure retirement date of **2027-04-14**. Public documentation's **Deprecated** label can mean restrictions for fresh subscriptions; verify the actual account rather than assuming universal availability. The separate Optimizer generator follows the [official allowed model list](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models).

<figure class="portal-shot" id="portal-evaluation-criteria">
<img src="../../web/assets/portal/en/16-evaluation-criteria.png" alt="Foundry evaluation criteria configuration for Relevance and TaskAdherence with an explicit Judge model" width="1440" height="1000" loading="lazy">
<figcaption><strong>Read each metric's own scale.</strong> Relevance uses threshold 4; TaskAdherence uses binary pass 1. Keep only these two evaluators and verify Model: Judge model separately. <a href="../../web/assets/portal/en/16-evaluation-criteria.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Completion signal:** Relevance **1–5 / threshold 4**, TaskAdherence **binary 0/1 / pass 1**, query-only input, and the verified Judge are recorded, together with generated mappings and the service-version limitation. If setup differs, correct it before submission rather than silently changing metrics or models.

<p class="step-next no-print"><a href="#baseline" data-next-step>Next: 03. Run Foundry Evaluation →</a></p>

## 03. Run Foundry Evaluation {#baseline}

<div class="lab-concept" aria-label="Step 03 learning objective">
<p><strong>What:</strong> An actual Microsoft Foundry managed agent evaluation. <strong>Why:</strong> Configuration and model connectivity are not measured task performance. <strong>How:</strong> Review the exact contract, submit once, and follow the real evaluation/run IDs to completion.</p>
</div>

For a fresh authorized workshop, continue to **Review** using the [direct agent-evaluation workflow](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent). The corrected English **`contoso-en-learning-loop`** baseline is already portal-submitted: open its recorded run instead of submitting again. Keep the earlier pilot unchanged and separate from this comparison.

| Review item | Required value |
|---|---|
| Target | **`contoso-eval-en`**, **Pin currently latest** resolved to **version `1` before configuration changes** |
| Scope / frequency | Individual turns / One time |
| Data | **`contoso-eval-en-dev12` version `1`**, all 12 cases, original file hash |
| Agent configuration | `query` only; no custom prompt override |
| Criteria / Judge | **Relevance threshold 4; TaskAdherence binary pass 1** (generic Threshold 1 if shown), generated mappings, **`lab-judge-luna-dea3cec5`** |
| Evaluation name | **`contoso-en-learning-loop`**, the corrected comparison definition; not the retained pilot name |

<figure class="portal-shot" id="portal-evaluation-review">
<img src="../../web/assets/portal/en/17-evaluation-review.png" alt="Foundry evaluation Review screen for a pinned agent version, existing dataset, and selected criteria" width="1440" height="1000" loading="lazy">
<figcaption><strong>Review before submission.</strong> Confirm the corrected definition name, pinned agent, dataset, Relevance 4, TaskAdherence binary pass 1, and Judge. A pilot's old settings are not the corrected contract, and a review screen is not execution evidence. <a href="../../web/assets/portal/en/17-evaluation-review.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

The final action is **Submit**, used once for the authorized baseline. The English submission below already exists; do not submit it again or rewrite the retained pilot.

**Completed canonical portal baseline:** **`contoso-en-learning-loop`**, evaluation `eval_94feef6f6f644fabb22a5680f5f24fb1`, run `evalrun_cde9948ac9d946929661bc3d9e60432a`. The HTTP 201 creation receipt was followed by actual completion on `contoso-eval-en` pinned v1 and `contoso-eval-en-dev12` v1, with Relevance threshold 4, TaskAdherence binary pass 1, and the same `gpt-6-luna` Judge. These are baseline results, not candidate results.

The **EVALUATION details page** provides **Raw JSON** and **Evaluation runs**. Keep the definition/run IDs, URL, and submission time. The older pilot remains in the [operator record](admin-setup.md#bootstrap), not this comparison. The visible Add run candidate wizard currently fails; use step 06 rather than repeating it.

**Completion signal:** The actual run page reports **Completed**, and you can inspect its results. Still account for **all 12 cases**, including failed, errored, or missing rows. A failed or partial run stays failed/partial in your record; a completed run is not automatically a quality pass.

If access, model support, or scoring fails, keep the IDs and error details, use the [facilitator's recovery reference](facilitator.md#resume), and mark later work not run. Do not replace a failed managed evaluation with authored scores.

<p class="step-next no-print"><a href="#analyze" data-next-step>Next: 04. Read scores and reasons →</a></p>

## 04. Read scores and reasons {#analyze}

<a id="iq"></a>
<a id="score-rubric"></a>
<a id="worked-evaluation"></a>

<div class="lab-concept" aria-label="Step 04 learning objective">
<p><strong>What:</strong> Per-metric scores and row-level explanations. <strong>Why:</strong> An average can hide a policy mistake or a missing answer. <strong>How:</strong> Read both evaluator summaries, then compare a failure or lowest-score case with a good case.</p>
</div>

On the **Evaluations run page**, read the summaries and **Detailed metrics result**, including **`Relevance.reason`** and **`TaskAdherence.reason`**; scroll horizontally if necessary. A row's **conversation_id → User view** opens its question and actual JSON response, **not an inline Judge-reason panel**. Return to Detailed metrics result for evaluator reasons.

**Actual canonical baseline only:** Do not substitute pilot aggregates or label these as candidate results.

| Baseline result | Observed value |
|---|---|
| Execution | **Completed; 12 rows** |
| Overall | **10 passed / 2 failed / 0 errored** |
| Relevance | **10/12 passed**, threshold **4** |
| TaskAdherence | **12/12 passed**, binary **1** |

| Record for each evaluator | Interpretation |
|---|---|
| Total scope | **n = 12**, including rows without usable scores |
| Scored / total, missing, errors | Coverage, not extra successful cases; do not silently drop rows |
| Relevance result | **1–5**, threshold **4**. A score of 4/5 is not 80% accuracy |
| TaskAdherence result | **Binary 0/1: 1 = Pass, 0 = Fail**. A missing/error result is not a scored 0 |
| Pass count and score summary | Report separately for Relevance and TaskAdherence; do not merge them into a new accuracy claim |
| Row-level reason | The evaluator's explanation to check against the actual answer and reference |

<figure class="portal-shot" id="portal-evaluation">
<img src="../../web/assets/portal/en/18-evaluation-results.png" alt="Foundry evaluation summary and Detailed metrics result for inspecting the canonical English baseline" width="1440" height="1000" loading="lazy">
<figcaption><strong>Read the canonical baseline.</strong> Match the recorded run ID: 12 rows, 10 passed, 2 failed, 0 errored overall; Relevance 10/12 and binary TaskAdherence 12/12. Read reasons in Detailed metrics result. These are not candidate results. <a href="../../web/assets/portal/en/18-evaluation-results.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Select **at least one failing or lowest-score case and one good case**, if a good case exists. For each, connect the **actual question → actual answer → evaluator score/reason → policy `context` and parsed `ground_truth` reference**. If no good case exists, say so rather than inventing one.

Check concrete domain behavior: Did the answer apply the right policy date? Ask for genuinely missing information? Cite supporting policy? Claim an approval or action that never happened? A reference answer need not match word for word.

**The canonical v1 baseline's two Relevance failures:** TaskAdherence passed for both; these are not candidate regression findings.

| Case | Observed answer and reference distinction |
|---|---|
| `atlas-dev-001` | The subscription-reduction answer was vague; the reference required explicit clarification |
| `atlas-dev-011` | The answer honestly described an undocumented feature as unverified, but Relevance judged it incomplete |

Inspect the actual reasons and reference policy. **Do not change policy facts or replace justified uncertainty with unsupported confidence merely to chase Judge scores.**

<figure class="portal-shot" id="portal-evaluation-case">
<img src="../../web/assets/portal/en/19-evaluation-case.png" alt="Evaluation row conversation_id to User view showing atlas-dev-001 question and actual JSON response, not Judge reasons" width="1440" height="340" loading="lazy">
<figcaption><strong>conversation_id → User view: inspect the actual response.</strong> This shows the atlas-dev-001 question and JSON response, not an inline Judge-reason panel. Return to <strong>Detailed metrics result</strong> for <code>Relevance.reason</code> and <code>TaskAdherence.reason</code>, then compare the reference policy. <a href="../../web/assets/portal/en/19-evaluation-case.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Limits:** Relevance and TaskAdherence are useful, compact criteria, not a complete policy or safety certification. Not every evaluator consumes `context` or `ground_truth`; those columns remain available for supported reference use and your review. Do not claim that selecting two criteria checks every response-contract rule.

<p class="share-checkpoint" id="share-baseline"><strong>Discuss:</strong> State the actual run ID, n = 12, each metric's coverage/pass count, one problematic claim, and one good response. Explain which instruction behavior you want to improve and why.</p>

**Completion signal:** You can support an improvement hypothesis with an actual answer and reason, while keeping errors visible. If no failure is observed, use the lowest-score case and report that result honestly; do not weaken the baseline to manufacture a lesson.

<p class="step-next no-print"><a href="#optimize" data-next-step>Next: 05. Improve instructions with Agent Optimizer →</a></p>

## 05. Improve instructions with Agent Optimizer {#optimize}

<a id="tune"></a>

<div class="lab-concept" aria-label="Step 05 learning objective">
<p><strong>What:</strong> One instruction-only Agent Optimizer candidate. <strong>Why:</strong> A controlled change makes the later comparison interpretable. <strong>How:</strong> Keep the agent model, tools, dataset, and Judge fixed; inspect the proposed instruction diff before creating a separate lab version.</p>
</div>

**Actual English job succeeded:** `opt_e44bcf5701a348deb62a1cd4f9cb3910`, **one candidate**, instruction-only, same dataset, `gpt-5.5` generator, `gpt-6-luna` Judge, no model comparison. Optimizer UI scores were **0.635 → 0.646**, with **UI-reported +0.010** and **264,260 reported tokens**. These are service optimization results, not direct candidate-evaluation scores; do not recalculate a different delta from the displayed values or resubmit the job.

Open **Build → Agents → `contoso-eval-en` → Optimize Preview**. On first use, choose **Optimize my agent → Agent**, not **Cost**. After jobs exist, the menu may read **Optimize → Agent**. The first-run tax-agent benchmark is a **product example**, not Contoso results.

In **Create an optimization run**, follow the [official prompt-agent Optimizer workflow](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent):

| Setting | Exact workshop choice |
|---|---|
| Agent version | **`contoso-eval-en` version `1`**, the same pinned baseline used in direct Evaluation |
| Choose targets | Uncheck **Model**; select **Instruction only**; **Tool description off** |
| Max candidates | **1**. Clear Model first: model-only selection can disable this field |
| Optimization model | **`lab-planner-dea3cec5`**, **`gpt-5.5` / `2026-04-24`** |
| Evaluation model | **`lab-judge-luna-dea3cec5`**, the same verified `gpt-6-luna` Judge used in direct Evaluation |
| Model comparison | Off; do not change the model being optimized |

<figure class="portal-shot" id="portal-optimizer-target">
<img src="../../web/assets/portal/en/07-optimizer-target.png" alt="Agent Optimizer target settings for instruction-only optimization with one candidate and separate optimization and evaluation models" width="1210" height="968" loading="lazy">
<figcaption><strong>Choose the target before the candidate limit.</strong> Instruction only keeps model changes out of the experiment. The optimization model generates instructions; the evaluation model scores responses. <a href="../../web/assets/portal/en/07-optimizer-target.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Choose **Next → Select dataset and criteria** and **`contoso-eval-en-dev12` version `1`**, not Generate data or an edited upload. Use the same Judge and keep exactly Relevance and TaskAdherence.

In Optimizer **Criteria**, if **No custom evaluators available** appears, switch **Custom only OFF** or click **View built-in evaluators**. Selecting either evaluator row opens its **Configure...** dialog: set **Relevance Threshold 4** or **TaskAdherence Threshold 1**, then **Apply**. TaskAdherence remains binary pass 1. Do not create custom evaluators to bypass this filter; record settings without claiming private rubric-version pins.

<figure class="portal-shot" id="portal-optimizer-data">
<img src="../../web/assets/portal/en/08-optimizer-dataset.png" alt="Agent Optimizer dataset and criteria selection using the existing English dev12 dataset" width="1210" height="968" loading="lazy">
<figcaption><strong>Reuse the registered dataset.</strong> Confirm its version and 12-case scope. A five-row preview does not change the full dataset count. <a href="../../web/assets/portal/en/08-optimizer-dataset.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

For a fresh authorized job, review and submit once. For the recorded job, follow its existing ID and wait **at most 60 minutes** within the approved scope. One job can make multiple internal calls; it is not one free model request. If blocked or timed out, record the status and stop rather than submitting a duplicate.

For the succeeded job, read **original versus candidate**, **per-evaluator results**, and **View changes**. The Optimizer's **0–1 ranking** is not the same as Relevance's 1–5 score or a pass percentage. A higher ranking does not establish policy improvement or replace direct reevaluation.

<figure class="portal-shot" id="portal-optimizer-results">
<img src="../../web/assets/portal/en/09-optimizer-results.png" alt="Agent Optimizer original and candidate results with evaluator details and candidate actions" width="1440" height="1000" loading="lazy">
<figcaption><strong>Read the candidate's evidence.</strong> Check actual job/candidate IDs and per-evaluator results. A recommendation is not a promised improvement or production approval. <a href="../../web/assets/portal/en/09-optimizer-results.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-optimizer-diff">
<img src="../../web/assets/portal/en/10-optimizer-changes.png" alt="Agent Optimizer View changes comparing original and candidate instructions" width="1038" height="622" loading="lazy">
<figcaption><strong>Inspect the instruction diff.</strong> Check policy reasoning, clarification, authority boundaries, and the English response contract. Longer instructions are not inherently better. <a href="../../web/assets/portal/en/10-optimizer-changes.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Keep the same model, tools, connections, and response contract. Do not remove tools just because an exported candidate configuration omits them. If the proposed change is not instruction-only, report the mismatch rather than claiming a controlled improvement.

**Actual Promote created `contoso-eval-en` v2**, with exact candidate instructions and unchanged model/knowledge tool verified. Active-version changes affect **all channels**, so this was restricted to the **isolated, unpublished lab, never production**. After HOLD, active v1 was restored; v2 remains available with its evaluation evidence. Do not promote again or delete it.

<p class="share-checkpoint" id="share-optimizer"><strong>Discuss:</strong> Which instruction changed, which failure might it address, and what could regress? The Optimizer's internal result selects a candidate for verification; it does not replace the next direct Evaluation.</p>

**Completion signal:** The real job succeeded and verified lab v2 exists. Its separate native SDK evaluation completed as recorded in step 06; neither promotion nor the Optimizer UI score is production approval.

<p class="step-next no-print"><a href="#decision" data-next-step>Next: 06. Reevaluate, compare, and finish →</a></p>

## 06. Reevaluate, compare, and finish {#decision}

<a id="review"></a>
<a id="operate"></a>
<a id="cleanup"></a>

<div class="lab-concept" aria-label="Step 06 learning objective">
<p><strong>What:</strong> A real Foundry managed evaluation of v2 under the existing definition. <strong>Why:</strong> The portal candidate form currently fails before submission. <strong>How:</strong> Run one Azure AI Projects/OpenAI Evals SDK helper command, then read and compare the remote runs in Foundry.</p>
</div>

**Observed portal blocker:** Add run → Pin v2 → Individual turns led to **Configure agents: Config required → Add custom prompt / User prompt**. Even `{{item.query}}` failed Submit client-side with **`Unable to create data source configuration from item schema`**. **No candidate remote run was submitted by that attempt.** Do not create another evaluation definition to bypass it.

From the repository root in bash/zsh/WSL2, replace **all four placeholders** below. The operator supplies the project endpoint and subscription. Copy **your own baseline's** evaluation/run IDs from its portal URL or **Raw JSON**. Do not copy the IDs from this guide's recorded rehearsal.

```bash
export AZURE_AI_PROJECT_ENDPOINT="OPERATOR_PROJECT_ENDPOINT"
export AZURE_SUBSCRIPTION_ID="OPERATOR_SUBSCRIPTION_ID"
export FOUNDRY_EVALUATION_ID="YOUR_EVALUATION_ID"
export FOUNDRY_BASELINE_RUN_ID="YOUR_BASELINE_RUN_ID"
```

**Prerequisites:** Activate the prepared venv with `source .venv/bin/activate`, install locked dependencies with `python -m pip install -r requirements.lock`, then complete `az login` and the [account/subscription verification](admin-setup.md#sdk-prerequisites). Do not proceed with a different account or missing prerequisites.

**Run this one SDK operation.** It clones the baseline `data_source`, retains existing evaluation criteria, changes only the target version in the run input, verifies the same model/tools, and submits a **real Foundry evaluation run under the same evalID**. It is **not a local Judge or bespoke cloud scoring**.

```bash
python scripts/add_foundry_eval_run.py --endpoint "$AZURE_AI_PROJECT_ENDPOINT" --subscription "$AZURE_SUBSCRIPTION_ID" --evaluation "$FOUNDRY_EVALUATION_ID" --baseline "$FOUNDRY_BASELINE_RUN_ID" --version 2 --name candidate-v2 --out .lab/foundry-evaluations/candidate-v2.json
```

The first submission persists a private **receipt**. Repeat the identical command and `--out` path only to collect that same run. If the receipt is missing but the run name already exists remotely, the helper stops instead of creating a duplicate. Open the existing run or recover its original receipt; do not change names, paths, or evaluation definitions to chase a favorable result.

**Verified SDK result:** under **`eval_94feef6f6f644fabb22a5680f5f24fb1`**, candidate run **`evalrun_f3b710fc835d444fb8aa0d2bb7797bdf`**, `contoso-eval-en` **v2**, is **Completed: 12 rows, 11 passed / 1 failed / 0 errored**, versus v1's **10 passed / 2 failed / 0 errored**. The helper confirmed the same dataset, evaluators, Judge, model, and tools; only instructions/version changed. This is a real Foundry run, not the Optimizer's internal score.

Open **Build → Evaluations → `contoso-en-learning-loop` → Evaluation runs**, select both run checkboxes, then **Compare runs**. **Explicitly select the original `contoso-eval-en` in the Baseline dropdown.** The page defaults to the first selected row—`candidate-v2` in this recorded case—so verify direction before reading differences/tests. The values below use original v1 as Baseline; private rubric-version pinning remains unproven.

| Actual comparison, n = 12 | Original `contoso-eval-en` v1 | `candidate-v2` |
|---|---|---|
| All-criteria pass / fail / error | 10 / 2 / 0 | 11 / 1 / 0 |
| Relevance passes; mean (1–5) | 10/12; **4.4167** | 11/12; **4.3333** |
| TaskAdherence passes; binary mean | 12/12; **1.0** | 12/12; **1.0** |
| Relevance rows 1 / 2 / 6 / 11 | 3 / 5 / 5 / 3 | 4 / 4 / 4 / 3 |
| Latency p50 (ms) | 5,891.09 | 7,287.52 |
| Latency p95 (ms) | 8,817.33 | 16,038.35 |
| Agent tokens | 35,187 | 43,751 |

<figure class="portal-shot" id="portal-evaluation-comparison">
<img src="../../web/assets/portal/en/20-evaluation-comparison.png" alt="Foundry Evaluations comparison of baseline and candidate runs under matching dataset and evaluator settings" width="1440" height="520" loading="lazy">
<figcaption><strong>Actual native comparison.</strong> Set <strong>Baseline → contoso-eval-en</strong>, not the first-selected candidate-v2. PairedTTest is Inconclusive for both metrics. The higher pass count does not erase the lower Relevance mean or higher latency/tokens: adoption remains HOLD. <a href="../../web/assets/portal/en/20-evaluation-comparison.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Decision executed: HOLD adoption; active version restored to 1.** After explicitly selecting the original Baseline in Compare, keeping the original in this lab uses **Agent Details → Agent configuration → Active version → Edit → Version 1**; the operator already completed this. **Keep candidate v2, both evaluation runs, and receipts—do not delete evidence.** Lower mean, row regressions, higher latency/tokens, and Inconclusive tests do not prove overall improvement; do not change policy facts to chase scores.

<p class="share-checkpoint" id="share-optimized"><strong>Closing explanation:</strong> Explain HOLD using the extra passing row, rows 2/6 regressions, lower mean, higher latency/tokens, and Inconclusive tests—not just the Optimizer's +0.010 or native pass count.</p>

**Completion signal:** Actual run IDs, measured tradeoffs, and the HOLD decision are recorded. Further review and new representative cases belong to the next authorized improvement cycle, not an extra required lab or retries until favorable.

Reused dev12 does not establish statistical significance or production approval. **No production Publish was performed and no production channels/traffic are configured.** Foundry still automatically provides **RBAC-only Responses/preview endpoints without Publish**; unpublished does not mean no endpoints.

<a id="troubleshooting"></a>
<a id="sources"></a>

**Finish:** Give the operator the actual run/job/version references, dataset version/hash, observed failures, and remaining blockers. Agree who owns ongoing resource costs and authorized cleanup; closing the browser does not stop charges. Share only approved synthetic examples and redacted summaries, never credentials or private environment files.

[Data contract](../../data/README.en.md) · [Facilitator and recovery](facilitator.md#resume) · [Operator handoff](admin-setup.md#handoff) · [Measured verification and sources](verification.md)
