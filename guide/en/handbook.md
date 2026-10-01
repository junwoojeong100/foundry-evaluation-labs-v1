# Great agents start with evaluation · v1 {#좋은-에이전트는-평가에서-시작된다-v1}

<p class="eyebrow">CONTOSO ATLAS CLOUD · ONE LEARNING PATH</p>

**Evaluate your business cases, improve instructions with Agent Optimizer, and verify a better v2 using the same criteria.**

<ol class="learning-path" role="list" aria-label="Lab steps">
<li><a href="#start"><strong>01</strong> Prepare the dataset</a></li>
<li><a href="#prepare"><strong>02</strong> Select evaluation criteria</a></li>
<li><a href="#baseline"><strong>03</strong> Run Foundry Evaluation</a></li>
<li><a href="#analyze"><strong>04</strong> Read scores and reasons</a></li>
<li><a href="#optimize"><strong>05</strong> Improve instructions with Agent Optimizer</a></li>
<li><a href="#decision"><strong>06</strong> Reevaluate and compare v1/v2</a></li>
</ol>

Use **your own representative tasks and business criteria**, not a public benchmark alone. Synthetic Contoso policies demonstrate **evaluate → learn → improve → reevaluate** without publishing private customer data.

The [operator](admin-setup.md#handoff) prepares the isolated project, Agent, policy tool, deployments and cost authorization before class. Infrastructure, Judge calibration and additional governance are not extra participant exercises.

**Version meaning:** v1/v2 are complete Foundry Agent versions. Here both use `gpt-6-sol`; only instructions change. Do not weaken v1 or promise an improvement before measuring it. Develop candidates as drafts and keep released versions at **v1 and v2**.

<p class="output-notice" id="portal-screenshots-note"><strong>How to read the pictures:</strong> These real English portal captures illustrate control locations from an earlier UI session. Their model names, versions and scores are not the current Sol verification. The <a href="verification.md">latest v2 report</a> is the authoritative measured comparison and includes every actual question, response, score and reason. Korean guide text does not mean a Korean run was executed.</p>

## 01. Prepare the dataset {#start}

<a id="demo"></a><a id="understand"></a><a id="data"></a>

Use **[data/en/optimizer/dev.jsonl](../../data/en/optimizer/dev.jsonl)** unchanged: **12 JSONL rows**, not a JSON array. The existing registration is **`contoso-eval-en-dev12` version `1`**. Do not reupload it in the prepared project.

| Column | Type | Use |
|---|---|---|
| `query` | String | The only Agent input |
| `context` | String | Policy reference for supported evaluators and case review |
| `ground_truth` | JSON string | Structured reference answer, never a generation prompt |

Record all 12 rows, the registration/version and file SHA-256. Keep the bytes identical through baseline, optimization and reevaluation. The source has other reserved subsets; they are not part of this workshop.

The Agent returns exactly `answer`, `citations`, `route`, `needs_human`. `answer` is English, citations are supporting policy IDs, route is `answer/clarify/escalate/refuse`, and the Boolean `needs_human` is true only for `escalate`. The Agent cannot actually submit, refund, delete or grant access.

Open **Foundry New experience → Build → Evaluations → Create → Create new evaluation**. For the prepared English target select **Agent → `contoso-eval-en-sol`**, pin the baseline explicitly to **v1**, and confirm one checked target. **Pin currently latest** is safe only while latest really is v1; selecting it can clear the checkbox.

Choose **Individual turns**, **One time**, and **Existing dataset**. Select the registered dev12. In a fresh authorized project only, use Upload new dataset for the exact file. The preview may show five rows; the dataset still has 12.

<figure class="portal-shot" id="portal-evaluation-dataset">
<img src="../../web/assets/portal/en/15-evaluation-dataset.png" alt="Illustrative Foundry Existing dataset selection and five-row preview, not the current run result" width="1440" height="1000" loading="lazy">
<figcaption><strong>Find the dataset controls.</strong> Select the current operator-provided registration. The preview is not proof of the total row count. <a href="../../web/assets/portal/en/15-evaluation-dataset.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Completion signal:** The draft targets explicit v1 and the unchanged 12-row dataset; count, version and hash are recorded. [Data contract](../../data/README.en.md#schema).

<p class="step-next no-print"><a href="#prepare" data-next-step>Next: 02. Select evaluation criteria →</a></p>

## 02. Select evaluation criteria {#prepare}

<a id="environment"></a><a id="calibration"></a><a id="model-smoke"></a><a id="first-infrastructure-failure"></a>

In **Configure agents**, leave the custom prompt override unset. Input is **`{{item.query}}` only**; never append `context` or `ground_truth`. If field mapping appears, use query → query.

Retain exactly these two managed evaluators:

| Evaluator | Meaning | Setting |
|---|---|---|
| Relevance | Addresses the question, **1–5** | **Threshold 4** |
| TaskAdherence | Follows the task, **binary 0/1 Pass/Fail** | **Pass 1**, not threshold 4 |

Choose the explicit Judge deployment and preserve service-generated mappings: Relevance `response={{sample.output_text}}`; TaskAdherence `response={{sample.output_items}}`. Read the definition's Raw JSON rather than substituting old UI bindings.

| Role | Model/version | Deployment |
|---|---|---|
| Agent | **gpt-6-sol / 2026-09-22** | `lab-agent-sol-dea3cec5` |
| Evaluation Judge | **gpt-6-luna / 2026-09-22** | `lab-judge-luna-dea3cec5` |
| Optimizer generator | **gpt-5.5 / 2026-04-24** | `lab-planner-dea3cec5` |

Sol's actual Agent/tool invocation was verified. Model catalog visibility alone is insufficient, and the [Optimizer support list](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models) is role-specific. Catalog evaluator version links do not prove that a private service rubric version is pinned; preserve the actual definition and disclose that limit.

<figure class="portal-shot" id="portal-evaluation-criteria">
<img src="../../web/assets/portal/en/16-evaluation-criteria.png" alt="Illustrative Relevance and TaskAdherence configuration with separate Judge selection" width="1440" height="1000" loading="lazy">
<figcaption><strong>Read each metric's own scale.</strong> Keep Relevance threshold 4, binary TaskAdherence pass 1, and the current Luna Judge. <a href="../../web/assets/portal/en/16-evaluation-criteria.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Completion signal:** The two evaluator scales, thresholds, mappings and actual Judge deployment are recorded. The saved remote definition, not a stale local environment default, determines the Judge.

<p class="step-next no-print"><a href="#baseline" data-next-step>Next: 03. Run Foundry Evaluation →</a></p>

## 03. Run Foundry Evaluation {#baseline}

Review **v1 + original dev12 + query-only input + two evaluators + Luna Judge**. The current prepared comparison is **`contoso-en-sol-learning-loop`**. Use the existing completed baseline when following the recorded rehearsal, not a second submission.

For a new authorized class, **Review → Submit** once. Keep the actual evaluation ID and run ID. Wait for completion and account for all 12 cases, including errors or missing results. A configured draft, HTTP creation receipt or successful model smoke is not a completed evaluation.

<figure class="portal-shot" id="portal-evaluation-review">
<img src="../../web/assets/portal/en/17-evaluation-review.png" alt="Illustrative Foundry evaluation Review page; use the current Sol target and own run identifiers" width="1440" height="1000" loading="lazy">
<figcaption><strong>Review before Submit.</strong> This picture illustrates the controls, not the current Sol run. Confirm the actual pinned version and saved evaluation contract. <a href="../../web/assets/portal/en/17-evaluation-review.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Completion signal:** The real Foundry run is Completed and exposes 12 output items. A failed or incomplete run stays failed/incomplete. No local custom Judge substitutes for this managed Evaluation.

<p class="step-next no-print"><a href="#analyze" data-next-step>Next: 04. Read scores and reasons →</a></p>

## 04. Read scores and reasons {#analyze}

<a id="iq"></a><a id="score-rubric"></a><a id="worked-evaluation"></a>

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

<p class="share-checkpoint" id="share-baseline"><strong>Discuss:</strong> State the run ID, each metric's scale/pass count, a concrete problematic answer and the instruction behavior you want to improve.</p>

**Completion signal:** You can explain a real weakness and a supported improvement hypothesis, not just an average.

<p class="step-next no-print"><a href="#optimize" data-next-step>Next: 05. Improve instructions with Agent Optimizer →</a></p>

## 05. Improve instructions with Agent Optimizer {#optimize}

<a id="tune"></a>

Open **Build → Agents → `contoso-eval-en-sol` → Optimize Preview → Agent**, not Cost. For a fresh job use **Create an optimization run**.

| Setting | Choice |
|---|---|
| Agent version | Explicit baseline **1** |
| Choose targets | **Instruction only**; Model and Tool description off |
| Max candidates | Operator-approved bound; this run uses at most **2**, not more releases |
| Optimization model | `lab-planner-dea3cec5` / gpt-5.5 |
| Evaluation model | `lab-judge-luna-dea3cec5` / gpt-6-luna |
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

Submit once within the approved cost scope; wait at most 60 minutes and then retain the actual state. Reuse the existing job ID on a resumed class. Optimization includes multiple internal calls.

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

**Do not continually create v3, v4 and later releases.** The operator tests the candidate as an explicitly pinned draft. **Promote/create v2 only after the real same-criteria check demonstrates improvement without quality regressions.** Promotion is not permission to publish to production or change production traffic.

<p class="share-checkpoint" id="share-optimizer"><strong>Discuss:</strong> Which instruction behavior changed, what should improve, and what could regress? Identify the actual candidate rather than copying an old screenshot.</p>

**Completion signal:** A real managed Optimizer result and reviewed candidate exist. Independent reevaluation is still required.

<p class="step-next no-print"><a href="#decision" data-next-step>Next: 06. Reevaluate and compare v1/v2 →</a></p>

## 06. Reevaluate and compare v1/v2 {#decision}

<a id="review"></a><a id="operate"></a><a id="cleanup"></a>

Use the **same Foundry evaluation definition**, same dev12 and Luna Judge. In this portal, Add run previously failed with **`Unable to create data source configuration from item schema`**. The official Azure AI Projects/OpenAI Evals helper submits a real managed run; it is not local scoring.

With the operator's prepared venv and verified `az login`, replace these four placeholders with **your own** project and baseline IDs:

```bash
export AZURE_AI_PROJECT_ENDPOINT="OPERATOR_PROJECT_ENDPOINT"
export AZURE_SUBSCRIPTION_ID="OPERATOR_SUBSCRIPTION_ID"
export FOUNDRY_EVALUATION_ID="YOUR_EVALUATION_ID"
export FOUNDRY_BASELINE_RUN_ID="YOUR_BASELINE_RUN_ID"
```

The operator may validate an explicit draft before releasing v2. Once v2 is released, use:

```bash
python scripts/add_foundry_eval_run.py --endpoint "$AZURE_AI_PROJECT_ENDPOINT" --subscription "$AZURE_SUBSCRIPTION_ID" --evaluation "$FOUNDRY_EVALUATION_ID" --baseline "$FOUNDRY_BASELINE_RUN_ID" --version 2 --name candidate-v2 --out .lab/foundry-evaluations/candidate-v2.json
```

The receipt protects against duplicates. Repeat the identical command/path only to collect the same run. The helper also blocks an existing remote name, verifies remote thresholds/Judge/mappings, and confirms the actual version and system instructions in every result row.

In **Evaluation runs**, select both rows and **Compare runs**. Explicitly choose **v1 as Baseline**; selection order must not reverse the comparison.

<figure class="portal-shot" id="portal-evaluation-comparison">
<img src="../../web/assets/portal/en/20-evaluation-comparison.png" alt="Illustrative Compare runs layout; current v1/v2 values and statistical result are in the latest report" width="1440" height="520" loading="lazy">
<figcaption><strong>Confirm the comparison direction.</strong> This capture locates the Baseline control; it is not the current Sol measurement. Use the latest report's exact two run IDs. <a href="../../web/assets/portal/en/20-evaluation-comparison.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

The current [v2 verification](verification.md#status) publishes all 12 case responses, scores and reasons alongside the v1 control. Require no decline in all-criteria passes or either metric's pass count/mean, and at least one strict measured improvement. Check factual truth, routing and response format too. Report latency, tokens and the native statistical conclusion separately.

<p class="share-checkpoint" id="share-optimized"><strong>Explain the result:</strong> Identify the actual gain, unchanged criteria, any regression, and the remaining uncertainty. Observed improvement is not a guarantee that every future stochastic run will improve.</p>

**Completion signal:** The latest v2 has a complete, honest same-model comparison. There is one current report, not accumulating release numbers. Production approval and independent generalization are separate and are not granted by this dev12 exercise.

<a id="troubleshooting"></a><a id="sources"></a>

**Finish:** Give the operator the actual run/job IDs, data hash and measured decision. Preserve raw receipts locally; publish synthetic answers and evaluator reasons without credentials, cookies, signed URLs or private account details. [Facilitator recovery](facilitator.md#resume) · [Data contract](../../data/README.en.md).
