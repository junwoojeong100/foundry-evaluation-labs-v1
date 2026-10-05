# Synthetic English evaluation data {#data-guide}

[Dataset step](../guide/en/handbook.md#start) · [Lab worksheet](../guide/en/admin-setup.md#handoff) · [Korean data guide](README.md)

## One unchanged dataset for the comparison {#start}

Use **[data/en/optimizer/dev.jsonl](en/optimizer/dev.jsonl)**, exactly **12 JSONL records**, for Foundry Evaluation, Agent Optimizer, and reevaluation. In the project you created, follow [04](../guide/en/handbook.md#start) to register `lab-en-dev12` version `1`. When resuming your same lab, compare its recorded name, version, and hash before reusing registration.

Keep its exact bytes, SHA-256, questions, references, and language fixed throughout the comparison. Keep Korean and English data separate rather than mixing them in one comparison.

Use [04's code ↔ portal table](../guide/en/handbook.md#dataset-code-portal) to distinguish local count/hash checks from portal registration. [05's remote-settings verification](../guide/en/handbook.md#criteria-code-portal) and [09's actual SDK submission](../guide/en/handbook.md#decision-code-portal) show how data, mappings, and versions stay fixed. Do not run read-only source panels independently.

## Purpose and limits {#scope}

Contoso Atlas Cloud is fictional. Its policies, inquiries and reference answers are synthetic—not private customer data or the terms of Microsoft, Azure or a real provider.

The purpose is **evaluation against your own business tasks and criteria**, not a public benchmark alone. Representative tasks expose policy-date boundaries, ambiguity, unsupported certainty and action claims. A 12-case development set demonstrates the learning loop; it does not certify production or independent generalization.

## Preserve the original source corpus {#composition}

[data/en/cases.jsonl](en/cases.jsonl) contains 100 cases: `train` 56, `validation` 12, `dev` 12 and `test` 20. Only dev12 is used in this workshop. Other source subsets remain available but are not additional participant exercises.

Do not select only easy rows, duplicate questions, merge subsets, or replace references after seeing results. [The eight policy documents](en/knowledge/documents.json) retain stable `ATLAS-*` IDs and effective dates. Prepare policy access yourself with the [commands in 03](../guide/en/handbook.md#agent).

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

On the first attempt, use **Upload new dataset → Browse** to register the exact English file as `lab-en-dev12` version `1`. For resumption, Optimizer, and reevaluation, use **Existing dataset** with the same name/version. The preview may show five rows; the file and evaluation scope still contain 12.

Leave the custom prompt override unset. Use `query → query` if a field-mapping screen appears. Service mappings are **Relevance `response={{sample.output_text}}`** and **TaskAdherence `response={{sample.output_items}}`**. These are not extra JSONL columns.

Keep **Relevance 1–5 / threshold 4**, **TaskAdherence binary 0/1 / pass 1**, and the same Luna Judge. Selecting two evaluators does not mean both consume every reference field or certify every business rule.

## Compare complete evidence {#compare}

Compare the questions, responses, evaluator scores, and reasons for all 12 cases across same-model v1 and v2. Record your actual run IDs and dataset hash to identify the comparison.

The helper checks matching questions/references and actual per-item Agent version/instructions. Missing/error rows cannot become successful rows or disappear from the denominator. JSON/route checks are supplementary validation, **not a replacement local Judge**.

Agent Optimizer's internal ranking is distinct from the separate managed run's means and pass counts. Review the complete candidate instructions and preserve model/tools/reasoning/schema. Compare one reviewed v2 without continually adding releases. Without a candidate worth retaining, record why you keep v1 and continue to 10.

Before sharing results, remove credentials, signed URLs, and private account details. Keep every case, including errors and missing results.

`cleanup` does not remove every registered dataset. Follow [10](../guide/en/handbook.md#cleanup) to preserve results and remove your dedicated group. Only with explicit retention authorization, record remaining registrations/evaluations, cost responsibility, and review date. Never delete shared or external resources.
