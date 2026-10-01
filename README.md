# Foundry Learning Loop Lab v1

**[Start in English](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/#start)** · **[한국어 가이드](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#start)** · [한국어 README](README.ko.md)

Use **Microsoft Foundry managed Evaluation and Agent Optimizer** to improve an Agent against your own representative business tasks:

> Dataset → evaluators → Foundry Evaluation → actual scores and reasons → instruction improvement → same-criteria reevaluation

The sample Contoso policies and questions are synthetic. The lesson is **evaluate → learn → improve → reevaluate**, not a public benchmark leaderboard or production certification.

## One current Sol v1/v2 comparison

| Role | Verified model/version |
|---|---|
| Agent | **gpt-6-sol / 2026-09-22** |
| Foundry Evaluation Judge | **gpt-6-luna / 2026-09-22** |
| Agent Optimizer generator | **gpt-5.5 / 2026-04-24** |

The English Agent is **`contoso-eval-en-sol`**. V1/v2 are complete immutable Agent versions; in this comparison **only their instructions differ**. The model, tools, reasoning, strict JSON output schema, dataset and evaluators stay fixed. V1 is already a strong baseline, not deliberately weakened.

Candidate development uses explicitly pinned drafts. `ensure_fixed_release` permits only released **1 and 2**, reuses identical releases and rejects changes that would silently create v3. The current v2 instructions are [here](prompts/en/optimized.txt), with the [v1 baseline](prompts/en/baseline.txt) kept separately.

**[Latest v2 verification and v1 control](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/verification.html#status)** · **[Complete public case evidence](evidence/latest.json)**

Only this current comparison is reported. It includes all **12 actual questions, both responses, evaluator scores and reasons**, including failures. Old raw receipts remain locally for audit; credentials, cookies, signed URLs and private account metadata are never published.

The actual managed Optimizer retained v1 rather than automatically recommending its generated candidates. The selected v2 is an **operator-reviewed instruction refinement after that Optimizer run**, validated separately by managed Evaluation. It is not mislabeled as the service's automatically recommended candidate.

## Fixed data and criteria

Use unchanged **`data/en/optimizer/dev.jsonl`**, registered as `contoso-eval-en-dev12` version `1`. Its **12 JSONL records** contain `query`, `context`, and a JSON-string `ground_truth`. Only `query` reaches the Agent. Korean data remains separate; current published measurements are English, not a new Korean run.

| Managed evaluator | Scale and pass rule |
|---|---|
| Relevance | 1–5, threshold **4** |
| TaskAdherence | Binary 0/1 Pass/Fail, pass **1** |

The SDK helper adds a real run to the existing Foundry definition. It checks the remote Judge, thresholds and response mappings, prevents duplicate submissions, and verifies each output's actual pinned version and instructions. It is **not a local Judge**.

`scripts/compare_foundry_eval.py` requires complete matched cases, no lower quality pass counts/means, and at least one strict measured improvement. It does not hide malformed responses or claim that stochastic future results are guaranteed. Native statistical conclusions, latency and token tradeoffs are reported separately.

## Guides

| Guide | English | 한국어 |
|---|---|---|
| Participant path | [Start](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/index.html#start) | [실습](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#start) |
| Operator preparation | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/admin.html) | [운영자](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/admin.html) |
| Facilitation and recovery | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/facilitator.html) | [강사](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/facilitator.html) |
| Data contract | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/data-guide.html) | [데이터](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/data-guide.html) |
| Latest v2 evidence | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/verification.html) | [최신 검증](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/verification.html) |
| Complete print edition | [Open](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/print.html) | [인쇄본](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/print.html) |
| PDF | [English](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-EN.pdf) | [한국어](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-KO.pdf) |

English is the default. Language switching preserves the corresponding section, reading progress and theme. Guides work without login or JavaScript. For offline use, download the whole repository/package and keep its folders together.

Portal pictures are labeled **UI illustrations from earlier captures**, not current Sol measurements. The latest report and its actual run IDs are the measurement source.

## Execution boundaries

The operator prepares an isolated project and read-only policy connection before class. No separate knowledge-building, Judge-calibration or governance exercise is required. The Agent advises; it cannot issue refunds, submit tickets, delete data or grant access.

Runtime availability is role-specific. Verify the actual Agent/tool path and the [supported optimization models](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models). Do not change model roles midway through a comparison.

Production publication is not part of the lab. Closing a browser does not stop resource costs. Preserve genuine failures and do not rerun an unchanged candidate until a favorable sample appears.

## Maintain the deliverables

With the locked environment installed, run:

```bash
python scripts/build_datasets.py --language en --check
python scripts/build_datasets.py --language ko --check
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -q
```

English sources are `guide/en/*.md` and `data/README.en.md`; Korean sources are `guide/*.md` and `data/README.md`. Generated HTML belongs in `docs/` and `docs/ko/`. Preserve corresponding section IDs and separate language corpora.

Render both print editions as A4 PDFs with background graphics. Verify them with `scripts/verify_pdf.py` and the dependencies in `requirements-verification.lock`; rebuild the allowlisted ZIP with `python scripts/package_lab.py`. Keep `evidence/latest.json` synchronized with actual service results and checks.

GitHub Pages serves **main / repository root** with `.nojekyll`. Root `index.html` and legacy `docs/english.html` forward to English while preserving query strings and fragments.
