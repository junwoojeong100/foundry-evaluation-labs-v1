# Foundry Learning Loop Lab v1

**[Start in English → GitHub Pages](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/#start)** · **[한국어로 시작](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#start)** · [한국어 README](README.ko.md)

A hands-on workshop using **Microsoft Foundry managed Evaluation and Agent Optimizer**:

> Prepare your dataset → select evaluators → run Foundry Evaluation → inspect scores and failures → optimize instructions → reevaluate and compare

The purpose is **evaluation against your own business tasks and criteria**, not a public benchmark score alone. Synthetic Contoso policies and questions demonstrate the loop: **evaluate → learn from failure → improve → reevaluate**.

## Start the workshop

The operator prepares an isolated project, sample agent, model deployments, and authorization before class. Participants use the Foundry portal for the baseline and Optimizer, then one official-SDK helper for a second **managed Foundry run** and the portal's **Compare runs** view. No local custom-Judge exercise substitutes for Foundry Evaluation.

Use all **12 cases** from `data/en/optimizer/dev.jsonl` for English or `data/optimizer/dev.jsonl` for Korean. Keep the same dataset version, evaluator settings, Judge, agent model, and tools before/after. Only instructions and the pinned agent version change.

| Evaluation criterion | Interpretation |
|---|---|
| Relevance | 1–5; pass threshold **4** |
| TaskAdherence | Binary 0/1, **Pass/Fail**; pass **1**, not one out of five |

**English is the default; every guide has a Korean counterpart.** Header language links retain the corresponding section and reading progress. Guides work without sign-in or JavaScript. For offline reading, download the complete repository and open `index.html` or `docs/ko/index.html`; keep the package folders together.

## Guides on GitHub Pages

| Guide | English | 한국어 |
|---|---|---|
| Six-step participant path | [Start](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/index.html#start) | [실습 시작](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#start) |
| Operator prerequisites | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/admin.html) | [운영자 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/admin.html) |
| Facilitation and recovery | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/facilitator.html) | [강사 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/facilitator.html) |
| Dataset contract | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/data-guide.html) | [데이터 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/data-guide.html) |
| Actual verification and sources | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/verification.html) | [검증·출처](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/verification.html) |
| Complete print edition | [Open](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/print.html) | [통합 인쇄본](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/print.html) |
| Downloadable PDF | [English PDF](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-EN.pdf) | [한국어 PDF](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-KO.pdf) |

## Verified models and outcome

| Role | Verified selection |
|---|---|
| Agent | `gpt-4.1-mini` / `2025-04-14`; retained after `gpt-6-luna` Responses/Agent probes returned HTTP 500 in this environment |
| Foundry Evaluation Judge | **`gpt-6-luna` / `2026-09-22`**, used in actual managed baseline and candidate evaluations |
| Optimizer generator | `gpt-5.5` / `2026-04-24`; `gpt-6-luna` is not in the current [supported optimization-model list](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models) |

The existing agent model's [retirement date](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule) is **2027-04-14**; fresh subscriptions can face deprecation restrictions. Operators must verify a working runtime before class. Catalog visibility is not a successful agent invocation.

**Actual English rehearsal:** 12 cases passed through native Foundry Evaluation, one instruction-only Optimizer job, and same-definition reevaluation. All-criteria passes increased **10/12 → 11/12**, but mean Relevance fell **4.42 → 4.33** and p95 latency increased **8.82 → 16.04 seconds**. Foundry's statistical comparison was **Inconclusive**. Adoption is **HOLD**, with active version restored to v1 and candidate v2 retained.

Read the [verification record](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/verification.html) or machine-readable [evidence/latest.json](evidence/latest.json). These are English-data results, not a newly executed Korean run, a production approval, or proof of generalization.

## Execution boundaries

- The agent gives advice; it does not execute refunds or grant business access. Use only an isolated lab agent, not production traffic.
- For this portal version, **Add run** hit an item-schema error. Step 06 uses `scripts/add_foundry_eval_run.py` to submit to the **same Foundry evaluation**, preserving its dataset/criteria. The helper records the run ID and prevents duplicate submissions.
- Replace placeholders with **your own** endpoint, subscription, evaluation, and baseline-run IDs. Do not copy rehearsal IDs as new evidence or rerun until scores improve.
- Never publish `.env`, `.lab/`, credentials, raw private telemetry, or signed download URLs. Closing a browser does not stop resource costs.

## Maintain the guides

Run from the repository root with `requirements.lock` installed:

```bash
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -v
```

English sources are `guide/en/*.md` and `data/README.en.md`; Korean sources are `guide/*.md` and `data/README.md`. Shared UI strings are in `web/locales.json`. Generated English HTML is in `docs/`, Korean HTML in `docs/ko/`. Preserve corresponding section IDs and the separate original language corpora.

Regenerate each print edition as an A4 PDF with background graphics. With the dependencies in `requirements-verification.lock`, check English using `python scripts/verify_pdf.py docs/Foundry-Learning-Loop-Lab-EN.pdf --language en` and Korean with its filename and `--language ko`. Rebuild the offline ZIP with `python scripts/package_lab.py`.

GitHub Pages serves the **`main` branch root** with `.nojekyll`. Root `index.html` and the legacy `docs/english.html` entry forward to the full English guide, preserving query strings and fragments.
