# Verification record and limitations · Foundry Evaluation

The **[latest result JSON](../../evidence/latest.json)** separates documentation checks from the actual English rehearsal. The core workshop is **Foundry Evaluation → Agent Optimizer → same-criteria reevaluation**. It measures changes on the same Contoso business questions, rather than relying on a public benchmark score.

## What is checked {#local}

| Target | Evidence |
|---|---|
| Data | Separate English and Korean corpora; only each language's 12 dev cases are used in this loop |
| Actual evaluation | Foundry managed evaluation/run IDs, all 12 output items, metric scores, reasons, and errors |
| Optimizer | One actual instruction-only job, one candidate, and the original/candidate instruction diff |
| Reevaluation | Same evaluation definition, dataset version, evaluator settings, Judge, agent model, and tools; only instructions/version change |
| Portal | User authentication followed by Playwright Headless in the matching lab tenant, with English UI/data |
| Distribution | Both HTML/print/PDF editions, language switching, mobile layout, links, copying, and reading progress |

A documentation `PASS` is not an Azure quality pass or operational approval. The Korean guide describes the same procedure, but the numbers below are **actual English-data results**, not a Korean-language execution.

## Actual managed-evaluation results {#status}

Versions 1 and 2 of `contoso-eval-en` were evaluated in the newly provisioned dedicated North Central US environment.

| Metric | Baseline v1 | Candidate v2 |
|---|---:|---:|
| Cases | 12 | 12 |
| Cases passing every selected evaluator | 10/12 | 11/12 |
| Relevance passes, threshold 4/5 | 10/12 | 11/12 |
| Mean Relevance, 1–5 scale | 4.42 | 4.33 |
| TaskAdherence passes, binary Pass/Fail | 12/12 | 12/12 |
| Execution errors | 0 | 0 |
| Agent p50 latency | 5.89 s | 7.29 s |
| Agent p95 latency | 8.82 s | 16.04 s |
| Observed agent tokens | 35,187 | 43,751 |

**Adoption is on hold.** One more case passed, but mean Relevance declined and agent latency/token usage increased. The portal's **Compare runs → PairedTTest** also reported **Inconclusive** for both metrics. One small synthetic dev comparison does not establish a meaningful overall improvement or generalization. The dedicated lab agent's active version was **restored to 1**; candidate 2 and its evidence remain available.

The actual evaluation definition is `eval_94feef6f6f644fabb22a5680f5f24fb1`. Baseline run: `evalrun_cde9948ac9d946929661bc3d9e60432a`. Candidate run: `evalrun_f3b710fc835d444fb8aa0d2bb7797bdf`. Local custom-Judge scores were not substituted for these service results.

Optimizer job `opt_e44bcf5701a348deb62a1cd4f9cb3910` succeeded. Its displayed ranking moved from approximately **0.635 to 0.646**, with a displayed delta of **+0.010**. That is an internal 0–1 aggregate, not the same measure as the separate managed-evaluation pass rates or means above. The job reported **264,260 total tokens**; actual billing requires a separate check.

## Model roles and issues found during execution {#models}

| Role | Model used in this rehearsal | Evidence and limitation |
|---|---|---|
| Agent | `gpt-4.1-mini` · `2025-04-14` | Retained the verified working configuration. `gpt-6-luna` Responses and agent probes returned HTTP 500 in this environment and were not labeled successful |
| Foundry Evaluation Judge | `gpt-6-luna` · `2026-09-22` | Verified through Chat Completions and actual managed Foundry evaluations |
| Optimizer generation model | `gpt-5.5` · `2026-04-24` | Retained because `gpt-6-luna` is not in the current [supported optimization-model list](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models) |

Catalog visibility is not runtime verification. The observed HTTP 500 errors do not establish a global lack of agent support. The published [retirement date](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule) for `gpt-4.1-mini` is **2027-04-14**; new subscriptions can face deprecation restrictions. Operators must verify actual model access before class.

The rehearsal identified and addressed these issues:

- **TaskAdherence is binary 0/1 Pass/Fail, not a 1–5 score.** The first generic-threshold UI check was retained as a configuration pilot. The actual comparison started with Relevance 4 and TaskAdherence 1. The pilot was not overwritten or relabeled as the comparison baseline.
- **Portal Add run item-schema error:** The UI returned `Unable to create data source configuration from item schema`. The supplied `scripts/add_foundry_eval_run.py` added the candidate to the **same Foundry evaluation definition and dataset** using the official SDK. This is actual managed evaluation, not local scoring.
- **Honest uncertainty can receive a low Relevance score:** `atlas-dev-011` passed TaskAdherence but received Relevance 3 for declining to assert an unverified feature status. Do not invent policies or capabilities to increase a Judge score; inspect its reasoning against your own business criteria.
- **Separate resource-group policy failure:** The lab ARM deployment succeeded. A separate organization-policy deployment failed because its organization-managed log target was absent. Shared policy was not changed and the failure was not hidden.

## Retention, deletion, and publication boundaries {#checks}

The excluded training exercise's two dedicated jobs, trained model/checkpoint, model deployment, four uploaded files, and two result files were deleted and their absence verified. Its 202 local execution/log files were also removed. Shared models, the Foundry project, Search, and the current evaluation evidence remain. Deletion does not reverse charges already incurred.

Raw evaluation responses and the deletion audit remain private. Public deliverables exclude authentication state, cookies, tokens, approval files, and signed download URLs. No claim is made that Git history or Azure's general activity/billing records were erased.

## Sources {#sources}

Contoso Atlas Cloud policies, questions, and reference responses are synthetic—not actual customer data or provider terms. Earlier design references are preserved at [the archived repository's pinned commit][source-workshop].

The [English capture manifest](../../web/assets/portal/en/captures.json) records actual screen provenance, redactions, dimensions, and hashes. [NOTICE](../../web/assets/NOTICE.txt) records usage boundaries for Microsoft artwork and portal captures. Only cropping and privacy masks are applied; scores, states, and data are not rewritten.

Official procedures: [Evaluate Foundry agents](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent) · [Agent Optimizer](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent) · [Evaluator-specific scales](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators).

## Recheck locally {#update}

```bash
python scripts/build_datasets.py --language ko --check
python scripts/build_datasets.py --language en --check
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -q
```

**Commands explained:** Verify both source corpora without modification, generate both HTML editions, check generated-file freshness, and run local tests. These commands do not start Azure evaluations. Refresh PDFs and the distribution ZIP separately, then record only checks actually performed in the latest JSON.

[source-workshop]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/tree/93bc07e31373c4cfc278a2dc3757785946404cf2
