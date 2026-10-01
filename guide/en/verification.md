# Latest v2 verification · gpt-6-sol

**V2 improved the measured quality result over the same-model v1:** all-criteria passes increased **11/12 → 12/12**, mean Relevance **4.8333 → 4.9167**, and TaskAdherence remained **12/12**. This page reports only the current Sol pair, not historical experiments.

**Important limit:** p95 latency increased **10.97 → 42.97 seconds**, and the native statistical comparison is **Inconclusive**. The measured quality gain does not establish production readiness, statistical significance or guaranteed improvement on future runs.

## What was measured {#local}

Both versions of **`contoso-eval-en-sol`** used the same `gpt-6-sol / 2026-09-22` Agent, read-only policy tool, reasoning setting, strict JSON schema and registered **`contoso-eval-en-dev12` version 1**. Only the instructions changed.

All 12 unchanged records came from [data/en/optimizer/dev.jsonl](../../data/en/optimizer/dev.jsonl). Only `query` was sent to the Agent; `context` and `ground_truth` remained references. The two managed evaluators and their Luna Judge were unchanged. Actual version and system instructions were checked in every result item.

These are **actual English-data results**, not a newly executed Korean run. Local unit tests and response-format checks do not replace Microsoft Foundry managed Evaluation.

## Final v1/v2 results {#status}

| Metric | Sol v1 control | Sol v2 |
|---|---:|---:|
| Cases | 12 | 12 |
| All-criteria passes | **11/12** | **12/12** |
| Relevance passes, threshold 4 | 11/12 | 12/12 |
| Mean Relevance, 1–5 | **4.8333** | **4.9167** |
| TaskAdherence, binary pass 1 | 12/12 | 12/12 |
| Execution errors / skipped cases | 0 / 0 | 0 / 0 |
| Agent p50 latency | 8.03 s | 9.71 s |
| Agent p95 latency | 10.97 s | 42.97 s |
| Observed Agent tokens | 46,167 | 55,858 |

Evaluation definition: **`eval_40a593c037e44045a47fe5088438afc5`**.

V1 run: **`evalrun_077d41ff8a534b9caee64f9d6c2a339d`**. Final released v2 run: **`evalrun_6c9e78cfc9de4f1282eb621c6678d8b1`**. The report uses the actual released version **2**, not a draft relabeled as v2.

**Quality acceptance: PASS for this measured lab pair.** No evaluator pass count or mean declined, one additional case crossed the Relevance threshold, and all candidate responses met the JSON/routing/citation checks. Production approval is **not granted**, especially given the observed latency increase.

The isolated unpublished lab Agent now selects **active version 2**. The frozen v1 control remains available for comparison; no production channel or release beyond v2 was created.

## All twelve cases are public {#cases}

The machine-readable **[evidence/latest.json](../../evidence/latest.json)** includes `case_evidence`: all 12 original questions and references, both actual response texts, each evaluator's score/Pass/Fail/reason, response-format findings and latency. No difficult case was dropped.

| Case | Relevance v1 → v2 | TaskAdherence v1 → v2 |
|---|---|---|
| 01 Subscription intent | 5 → 5 | 1 → 1 |
| 02 Refund effective-date transition | 5 → 5 | 1 → 1 |
| 03 Paid-production-job disqualifier | 5 → 5 | 1 → 1 |
| 04 Unsubmitted support inquiry | 5 → 5 | 1 → 1 |
| 05 Suspected access incident | 5 → 5 | 1 → 1 |
| 06 Separate monthly SLA calculations | 5 → 5 | 1 → 1 |
| 07 Beta feature versus production SLA | 5 → 5 | 1 → 1 |
| 08 Availability target versus feature claim | 5 → 5 | 1 → 1 |
| 09 Inclusive/exclusive time boundaries | 5 → 5 | 1 → 1 |
| 10 Unauthorized tenant deletion | 5 → 5 | 1 → 1 |
| 11 Unverified feature and false alternatives | **3 → 4** | **1 → 1** |
| 12 Missing SLA calculation inputs | 5 → 5 | 1 → 1 |

Case 11 improved without pretending to inspect the user's screen or inventing a feature status. V2 gave a clear verdict that **neither asserted conclusion was established**, distinguished missing evidence from absence, and provided an authenticated verification path.

An excerpt from the actual v2 response:

> Neither conclusion is established. You don’t see a GPU model selection menu, but I haven’t inspected your screen or the live service.

The full response and unedited managed-evaluator reasons are in the public JSON. Evidence means actual execution data—not credentials. Tokens, cookies, signed URLs, account identifiers and raw conversation/tool payloads are excluded.

## Model roles and instruction provenance {#models}

| Role | Model/version | Boundary |
|---|---|---|
| Agent | **gpt-6-sol / 2026-09-22** | Actual Agent and knowledge-tool runtime verified; same in v1/v2 |
| Evaluation Judge | **gpt-6-luna / 2026-09-22** | Used by both real managed runs |
| Optimizer generator | **gpt-5.5 / 2026-04-24** | Separate role following the supported optimization-model list |

Actual managed Optimizer job: **`opt_87805603c0d74b7897f997502aaea080`**, instruction-only, at most two generated candidates. The service **retained the strong v1 baseline** rather than recommending either generated candidate.

V2 was an **operator-reviewed refinement after that job**, not a falsely attributed automatic Optimizer promotion. It preserved the strong baseline and clarified how to answer unsupported alternatives with a factual verdict and verification path. It contains no embedded evaluation questions, reference answers, policy rates or worked dataset examples.

Source: [v1 instructions](../../prompts/en/baseline.txt) · [v2 instructions](../../prompts/en/optimized.txt). Candidate development used explicit drafts; the released workshop Agent has **only versions 1 and 2**. Immutable versions are not overwritten or silently incremented.

## Statistical and operational limits {#checks}

The real Foundry comparison used **PairedTTest**:

| Evaluator | Mean difference | p-value | Service result |
|---|---:|---:|---|
| Relevance | +0.08333 | 0.33880 | Inconclusive |
| TaskAdherence | 0 | 1.00000 | Inconclusive |

The descriptive gain is real in these saved results, but the sample is small and reused during instruction development. Do not claim independent generalization, statistical significance, lower cost or faster operation. The p95 and token increases remain visible rather than being hidden behind the improved pass rate. Actual billing was not observed and is not reported as zero.

`scripts/compare_foundry_eval.py` enforces matched complete results, unchanged conditions, no lower aggregate quality counts/means and at least one strict improvement. It also retains malformed outputs as failures. This is a validation gate over **service-returned scores**, not a new local Judge.

## Sources and publication boundaries {#sources}

Only the latest v2 and its same-model v1 control appear in this current report. Earlier raw records remain in the local audit; they were not relabeled or erased from Azure/Git history.

The [capture manifest](../../web/assets/portal/en/captures.json) and [NOTICE](../../web/assets/NOTICE.txt) describe the real portal images. Those earlier images are **UI illustrations only**, not current Sol scoring evidence. Use the current run IDs and full public case record for the measurement.

Official references: [Agent evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent) · [Agent Optimizer](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent) · [Optimization-model roles](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models) · [Evaluator definitions](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators).

Contoso data is synthetic. Earlier design attribution remains at the [archived source commit][source-workshop]; it is not another current verification report.

## Recheck local deliverables {#update}

```bash
python scripts/build_datasets.py --language en --check
python scripts/build_datasets.py --language ko --check
python scripts/build_guide.py --check
python -m unittest discover -s tests -q
```

These commands check files and tests without submitting another Azure evaluation. The latest JSON separately records document, browser, PDF and service checks.

[source-workshop]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/tree/93bc07e31373c4cfc278a2dc3757785946404cf2
