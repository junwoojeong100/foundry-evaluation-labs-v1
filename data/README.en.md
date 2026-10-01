# Synthetic English evaluation data {#data-guide}

[Dataset step](../guide/en/handbook.md#start) · [Operator handoff](../guide/en/admin-setup.md#handoff) · [Korean data guide](README.md)

## One unchanged dataset for the comparison {#start}

Use **[data/en/optimizer/dev.jsonl](en/optimizer/dev.jsonl)**, exactly **12 JSONL records**, for Foundry Evaluation, Agent Optimizer and reevaluation. The existing registered dataset is **`contoso-eval-en-dev12` version `1`**. Reuse that registration rather than uploading a duplicate.

Keep its exact bytes and SHA-256, all questions and references, and language fixed. The current Agent is **`contoso-eval-en-sol`**, with released instruction variants v1/v2 on the same `gpt-6-sol` model. The original Korean corpus is separate and has not been newly executed as part of this English measurement.

## Purpose and limits {#scope}

Contoso Atlas Cloud is fictional. Its policies, inquiries and reference answers are synthetic—not private customer data or the terms of Microsoft, Azure or a real provider.

The purpose is **evaluation against your own business tasks and criteria**, not a public benchmark alone. Representative tasks expose policy-date boundaries, ambiguity, unsupported certainty and action claims. A 12-case development set demonstrates the learning loop; it does not certify production or independent generalization.

## Preserve the original source corpus {#composition}

[data/en/cases.jsonl](en/cases.jsonl) contains 100 cases: `train` 56, `validation` 12, `dev` 12 and `test` 20. Only dev12 is used in this workshop. Other source subsets remain available but are not additional participant exercises.

Do not select only easy rows, duplicate questions, merge subsets or replace references after seeing results. [The eight policy documents](en/knowledge/documents.json) retain stable `ATLAS-*` IDs and effective dates. Policy access is prepared by the operator; participants do not build a separate knowledge system.

## Upload and response schema {#schema}

Each JSONL line has exactly three columns:

| Column | Type | Purpose |
|---|---|---|
| `query` | String | The **only** Agent input |
| `context` | String | Source-policy reference for supported evaluators and case review |
| `ground_truth` | JSON **string** | Structured reference answer, not a generation prompt |

There is no prefilled `response`. Foundry invokes the pinned Agent to obtain one. Do not turn the file into a JSON array, rename columns, append references to the user message or precompute answers.

The reference answer and Agent response use exactly four keys:

| Key | Contract |
|---|---|
| `answer` | Nonempty English string |
| `citations` | Unique stable IDs of supporting policy documents |
| `route` | `answer`, `clarify`, `escalate` or `refuse` |
| `needs_human` | Boolean; true exactly when route is `escalate` |

The source [response schema](../schemas/response.schema.json) also checks routing consistency. Native structured output controls the JSON shape, not the factual truth of an answer. Numeric retrieval IDs are not policy citations.

The Agent cannot actually submit tickets, change subscriptions, approve credits or delete records. Classification as `escalate` does not mean a person was contacted. A request for unsupported certainty does not authorize fabricated facts.

## Register once; pin the same version {#upload}

Use **Foundry → Build → Evaluations → Create → Agent**, an explicit baseline version, **Individual turns / One time / Existing dataset**. Reselect the target checkbox if version selection clears it.

Choose the existing dev12 registration. In a fresh authorized project only, upload the exact language-specific file and record its new dataset version. The preview may show five rows; the file and evaluation scope still contain 12.

Leave the custom prompt override unset. Use `query → query` if a field-mapping screen appears. Service mappings are **Relevance `response={{sample.output_text}}`** and **TaskAdherence `response={{sample.output_items}}`**. These are not extra JSONL columns.

Keep **Relevance 1–5 / threshold 4**, **TaskAdherence binary 0/1 / pass 1**, and the same Luna Judge. Selecting two evaluators does not mean both consume every reference field or certify every business rule.

## Compare complete evidence {#compare}

The [latest report](../guide/en/verification.md) publishes the current v2 and its frozen same-model v1 control, including all 12 synthetic questions, actual answers, evaluator scores and reasons. Older raw runs are retained for audit, not mixed into the current comparison.

The helper checks matching questions/references and actual per-item Agent version/instructions. Missing/error rows cannot become successful rows or disappear from the denominator. JSON/route checks are supplementary validation, **not a replacement local Judge**.

Agent Optimizer's internal ranking is distinct from the separate managed run's means and pass counts. Review the candidate instructions and preserve model/tools/reasoning/schema. Use drafts during development; do not continually increment the released workshop versions beyond v1/v2.

Public evaluation evidence excludes authentication, signed URLs and private account metadata. The synthetic responses and failure reasons themselves may be shared. Publish failures as faithfully as successes.
