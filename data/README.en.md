# Synthetic English evaluation data {#data-guide}

[Participant dataset step](../guide/en/handbook.md#start) · [Operator handoff](../guide/en/admin-setup.md#handoff) · [Korean data guide](README.md)

## Use the workshop file unchanged {#start}

The English workshop uses **[data/en/optimizer/dev.jsonl](en/optimizer/dev.jsonl)** for direct Microsoft Foundry managed Evaluation, Agent Optimizer, and separate direct reevaluation. It contains **exactly 12 JSONL records** with `query`, `context`, and `ground_truth`. Despite the directory name, it is the shared dataset for the entire evaluation loop.

**`contoso-eval-en-dev12` version `1` is registered through the native Evaluation wizard** from that original 12-row file. Use it with **`contoso-eval-en` version `1`**; do not create a duplicate. Retain the dataset version and original file **SHA-256** across baseline, optimization, and reevaluation. Registration is not an evaluation result.

The Korean path uses operator-prepared **`contoso-eval-ko`** and `data/optimizer/dev.jsonl`, with separate **`contoso-eval-ko-dev12`** registration to confirm. **Korean was not re-executed in this rehearsal and has no new measured results here.** English responses must be English; Korean responses must be Korean. Switching a guide's language does not translate the selected dataset or agent. Cross-language runs are not paired evidence of instruction improvement.

The earlier **`contoso-en-baseline-luna-judge`** remains a **CONFIGURATION PILOT**. Canonical **`contoso-en-learning-loop`** is **Completed: 12 rows, 10 passed / 2 failed / 0 errored; Relevance 10/12, TaskAdherence 12/12 (binary 1)**, on the same pinned agent/data v1 and `gpt-6-luna` Judge. Actual IDs are in [step 03](../guide/en/handbook.md#baseline). These are baseline-only results, not candidate improvement.

Instruction-only job **`opt_e44bcf5701a348deb62a1cd4f9cb3910`** succeeded with **one candidate**, same dataset, `gpt-5.5` generation / `gpt-6-luna` Judge, no model comparison. UI **0.635 → 0.646**, **UI-reported +0.010**, **264,260 reported tokens** are Optimizer results, not direct candidate scores. Promote created lab-only v2 with exact candidate instructions and unchanged model/knowledge tool. **Latest active version affects all channels: only isolated unpublished lab agents, never production.**

## Purpose and limits {#scope}

Contoso Atlas Cloud is **wholly fictional**. Its eight policies, questions, reference answers, and workspace examples are synthetic. They contain no actual private customer conversations, accounts, credentials, or production approval and do not represent a real provider's terms.

The method is **evaluate → learn from failure → improve → reevaluate**. For an application, representative company-owned tasks, policy edge cases, and known failures are more useful than a public benchmark score alone. This corpus demonstrates how to inspect those decisions without using a company's private data.

Synthetic authorship is not completed human review. Counts and hashes measure data integrity, not model quality. Twelve development cases cannot certify production behavior, generalization, policy compliance, or safety.

## Source composition and workshop boundary {#composition}

The source [data/en/cases.jsonl](en/cases.jsonl) contains **100 cases** with fixed source labels:

| Source subset | Rows | Use in this workshop |
|---|---:|---|
| `train` | 56 | Unused/reserved source subset |
| `validation` | 12 | Unused/reserved source subset |
| `dev` | 12 | The only selected cases; exported to `data/en/optimizer/dev.jsonl` |
| `test` | 20 | Unused/reserved source subset |

Do not upload the 100-case source in place of dev12, merge subsets, select only easy questions, or duplicate rows. Preserve the original source assets; no other subset is a participant exercise.

The [English policy documents](en/knowledge/documents.json) supply stable `ATLAS-*` IDs and original policy excerpts. The prepared agent's policy access is an operator prerequisite, not a separate dataset or knowledge-construction lab.

## Upload and response contracts {#schema}

Each line is one JSON object with exactly these three columns:

| Column | Type | Boundary |
|---|---|---|
| `query` | String | **Only this field is sent to the agent** |
| `context` | String | Source-policy excerpts for supported evaluators and reviewer reference; not appended to generation |
| `ground_truth` | **JSON string**, not a nested object | Reference answer for supported evaluators and review; never a generation input |

There is **no prefilled `response`**. Foundry runs the selected agent version to obtain an actual response. Do not invent `response`, rename columns, wrap records in a JSON array, or add an alternative job schema.

`ground_truth` decodes to an object with exactly four keys. The agent uses the same response contract:

| Key | Expected value |
|---|---|
| `answer` | Nonempty **English** text; a short contract example is “Please confirm the purchase date.” |
| `citations` | Supporting stable policy-ID array, such as `["ATLAS-REF-001"]`; no fabricated IDs |
| `route` | `answer` for guidance, `clarify` for needed information, `escalate` for required human judgment, or `refuse` for prohibited requests |
| `needs_human` | Boolean; `true` **only when `route` is `escalate`** |

These are schema examples, not actual generated answers. An `escalate` response does not mean a person has already been contacted. The agent has no business-execution tools and must not invent approvals, ticket IDs, refunds, deletions, or completed access changes.

Source-case IDs, route labels, and other metadata stay in source records; they are not extra generation inputs. Match evaluation rows by their actual question and stable row position/source case when reviewing results.

Policy excerpts are reference material, not proof of what an agent tool actually retrieved. Do not turn a quoted instruction in a question or document into a higher-priority command. Compare meaning and policy decisions, not exact answer-text equality.

## Register once and select the same version {#upload}

For a fresh agent still at v1, use **Foundry New experience → Build → Evaluations → Create → Create new evaluation → Agent**. Pin before changes, reselect the cleared checkbox and confirm **1 target before Next**; choose Individual turns / One time / Existing dataset. Recorded `contoso-eval-en` retains v2 but has restored active v1. Reuse the explicit saved v1 baseline/data rather than assuming “latest” means active.

Do not upload the registered English file again. Only in a fresh authorized project without that registration, use **Upload new dataset → name → Choose file** for `data/en/optimizer/dev.jsonl` **→ Upload**. Confirm the selected dataset and preview. The preview shows **only the first five rows**; retain **all 12 records** and confirm the source file's SHA-256.

In the observed English wizard, the matching schema **auto-resolved Field mapping**, proceeding directly to **Configure agents**. Leave **custom prompt override unset**, keep agent input to **`query` only**, then continue to **Criteria**. If a mapping screen appears for the selected schema, use **query → query**.

Remove extras from the **23 suggestions**, retaining exactly **Relevance + TaskAdherence** with **`lab-judge-luna-dea3cec5`**. **Relevance is 1–5, threshold 4. TaskAdherence is Binary Pass/Fail, raw 0/1, pass 1**; if its generic control appears, set **Threshold 1**, then Update. The [official definitions](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators) confirm the binary type. The recorded **Evaluation name `contoso-en-learning-loop` → Submit** already succeeded with HTTP 201; open that run instead of submitting again.

**Inspect, do not override, generated mappings.** The corrected submission confirmed **Relevance `response={{sample.output_text}}`** and **TaskAdherence `response={{sample.output_items}}`**. UI defaults also showed **`query={{item.query}}`** and TaskAdherence's **`tool_definitions={{sample.tool_definitions}}`**. Read **Raw JSON**; do not restore TaskAdherence's earlier UI output-text value. The upload still has no prefilled `response`, and generation receives only `query`.

**Version limit:** Catalog links showed `relevance` **v14** and `task_adherence` **v17**, but actual service criteria had **`evaluator_version` empty/default**. Record evaluator names/configuration, Judge and dataset versions, and that private service rubric versions are not proven pinned.

Agent Optimizer uses **Next → Select dataset and criteria** and the **same registered dev12 version**, not Generate data or an edited upload. If Criteria says **No custom evaluators available**, switch **Custom only OFF** or click **View built-in evaluators**. Selecting a row opens **Configure...**: set **Relevance 4 / TaskAdherence 1**, then **Apply** for each. Keep binary pass 1 and the same Judge; no custom evaluator is required. See the [Optimizer step](../guide/en/handbook.md#optimize).

## Compare without changing the evidence {#compare}

| Keep identical | Record from each actual run |
|---|---|
| All 12 questions, references, language, dataset version, file SHA-256 | Same evaluation definition ID, distinct run IDs, explicit agent versions, final status |
| Same corrected definition; Relevance threshold 4; TaskAdherence binary pass 1; recorded configuration | Relevance 1–5 scores and TaskAdherence 0/1 results, per-metric pass counts/coverage/errors, and service-version limits |
| Judge deployment/model version, agent model, tools and connections | Actual answers and reasons, instruction diff, and per-case regressions |

Read a failing/lowest-Relevance case and a good case when available. **n = 12** includes missing/errors. **Relevance's 1–5 score is not percent accuracy; TaskAdherence's 0/1 is Fail/Pass**, not a five-point score. A missing score is not 0, and Completed is not a quality pass.

For an actual answer, open the row's **conversation_id → User view**. That is a question/JSON-response view, not an inline Judge-reason panel. Return to **Detailed metrics result** for **`Relevance.reason` / `TaskAdherence.reason`** and compare the reference policy; never change policy facts just to raise a score.

**Portal candidate submission is blocked:** Add run → Pin v2 / Individual turns required Config required → Add custom prompt / User prompt; even `{{item.query}}` failed client-side with **`Unable to create data source configuration from item schema`**. No candidate remote run was submitted by that attempt. Do not alter the dataset, add a fake response, or create a new evaluation definition to work around it.

After [venv/`requirements.lock` and `az login` account verification](../guide/en/admin-setup.md#sdk-prerequisites), use the [single SDK command](../guide/en/handbook.md#decision) in `scripts/add_foundry_eval_run.py`. The operator supplies endpoint/subscription; copy evaluation/baseline-run IDs from the baseline portal URL or Raw JSON. The Azure AI Projects/OpenAI Evals helper clones baseline `data_source`/existing criteria, changes only target version to **2**, verifies the same model/tools, and submits a **real Foundry run in the same evalID**, not local Judge scoring.

**Verified native result:** the helper submitted **`evalrun_f3b710fc835d444fb8aa0d2bb7797bdf`** for `contoso-eval-en` v2 under the same **`eval_94feef6f6f644fabb22a5680f5f24fb1`**. It completed **12 rows: 11 passed / 1 failed / 0 errored**, versus baseline **10 passed / 2 failed / 0 errored**. Dataset/evaluators/Judge/model/tools matched; only instructions/version changed.

Keep the original receipt and collect only the existing run. Select both rows in **`contoso-en-learning-loop` → Evaluation runs → Compare runs**, then **choose the original `contoso-eval-en` in the Baseline dropdown**. It defaults to the first selected row, which was `candidate-v2` here; do not read before/after directions until the baseline is correct.

Final v1→v2 observations: **Relevance 10/12→11/12 passes but mean 4.4167→4.3333**; **TaskAdherence 12/12 both, binary mean 1.0**; zero errors in both runs. Relevance row 1 improved **3→4**, rows 2/6 declined **5→4**, and row 11 stayed **3** for honest uncertainty rather than an unsupported definitive answer. Keep policy facts unchanged.

Latency **p50 5,891.09→7,287.52 ms**, **p95 8,817.33→16,038.35 ms**, and Agent tokens **35,187→43,751** increased. Native **PairedTTest is Inconclusive for both metrics**. **HOLD adoption; keep pinned v1 pending further review/new representative cases.** Pass count alone or Optimizer +0.010 is not proven overall improvement.

This same-dev12 observation does **not establish statistical significance, independent generalization, or production approval**. The actual SDK run proves remote execution; manifests and local files alone do not. Keep the original data assets unchanged.

**Final lab state:** adoption HOLD; active version restored to **1**, with candidate v2 and evaluation/receipt evidence retained—not deleted. No production Publish or production channels/traffic were configured. Foundry still automatically exposes **RBAC-only Responses/preview endpoints without Publish**; these are not evidence of production deployment.
