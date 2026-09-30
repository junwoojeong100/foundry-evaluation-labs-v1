# Foundry Learning Loop Lab v1.1 · English quickstart

[한국어](README.md) · **[Open the workshop guide](index.html)** · [Source handbook](guide/handbook.md)

**A fluent answer is not necessarily a correct business answer. Start by finding a mistake, then improve one Contoso support agent using evidence.**

Follow one path:

> Authored wrong answer → offline DEMO → local installation → a new NCUS environment → one model connectivity response → small LIVE agent evaluation → Foundry IQ → separate optimizer checkpoints → freeze and fresh holdout → human decision → observability and the next improvement

SFT and Frontier are gated appendices, not prerequisites for finishing the core learning loop. The policy, cases, prompts and responses remain **Korean**, so all participants use the same experiment.

## 1. Start before Azure setup

A fictional Contoso Atlas Cloud customer asks for a refund five days after their first monthly purchase.

> **Authored wrong answer:** “It is within 14 days, so your refund is approved and will arrive tomorrow.”

The [synthetic policy](data/knowledge/documents.json), `ATLAS-REF-001`, requires more than elapsed days: purchase type, production work and paid-credit use matter. **Eligibility is not approval or payment. This assistant cannot execute refunds.**

With the complete package and Python 3.11+ available locally, run from the package root. Python 3.12 is recommended.

```bash
python3 -S -m lab demo
```

**Checkpoint:** `AUTHORED_DEMO_NOT_LIVE`, `author_type: ai`, and `DEMO_COMPLETED`. The answers, labels and dialogue are AI-authored teaching examples, not claimed human authorship or review. No Azure account, credentials, `.env`, Azure CLI, SDK packages, network connection or paid request is needed.

The DEMO does not measure a live model or grant human approval. If Python is missing, read the guide while preparing Python; do not switch to LIVE commands to bypass a local error.

Continue with the [same handbook path](guide/handbook.md#demo), not a separate experiment.

## 2. What is implemented versus verified?

| Evidence type | Current meaning |
|---|---|
| Offline DEMO | Runnable authored examples, not measured model quality |
| Dataset | Eight synthetic policies; the original 100 cases remain train 56 / validation 12 / dev 12 / test 20 |
| New Azure environment | ARM `Succeeded`; 25 owned resource/connection/role records, including the new Foundry project, four model deployments, Search and telemetry |
| LIVE execution | Model and Agent responses, a 12-case IQ/MCP capture, real embedding/vector/hybrid/agentic retrieval, managed evaluation and separate business Judges executed |
| Quality | **HOLD**, not a fabricated pass: calibration disagreement, invalid output and throttled/missing scores remain visible |
| Optimization/training | Prompt Optimizer produced a real candidate and it was re-evaluated as a new Agent. Actual Agent Optimizer and SFT job IDs and terminal outcomes are tracked in the [verification record](guide/verification.md) |
| Frontier support/access path | **`NOT_VERIFIED`**, not a claim that the product or API does not exist |
| Production approval | A separate human responsibility, never granted by a score or AI-authored review |

See the [verification record](guide/verification.md). Metadata access, mocked tests, completed API calls and quality acceptance are different states.

**The first failure lesson:** gpt-4o-mini / 2024-07-18 showed `Deprecating`,
fine-tuning capability and available quota in catalog metadata, yet the provider
rejected it as deprecated since 2026-03-31. Preserve that failed attempt. The
replacement's `Legacy` catalog state and quota are also not deployment or
training guarantees.

## 3. Install only when moving beyond DEMO

These steps require network access for package installation; they are **not** prerequisites for the offline DEMO.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m lab validate
```

Use bash/zsh on macOS/Linux, or Ubuntu in Windows WSL2. Do not paste `source` into native PowerShell.

**Checkpoint:** local dataset validation succeeds and the original split counts remain unchanged. Then follow [new-environment setup](guide/admin-setup.md). Do not reuse an old account, subscription or resource profile. The bootstrap manifest and private generated `.env` identify each environment; `.env.example` is only a placeholder template.

## 4. Read the right document

| Goal | Document |
|---|---|
| Complete the learning loop | [Handbook](index.html) · [Markdown](guide/handbook.md) |
| New environment, identity, cost, RBAC and recovery | [Operator guide](admin.html) · [Markdown](guide/admin-setup.md) |
| Facilitate the workshop and recognize HOLD | [Facilitator guide](facilitator.html) · [Markdown](guide/facilitator.md) |
| Optional SFT and Frontier boundaries | [Appendix](sft.html) · [Markdown](guide/sft-appendix.md) |
| Dataset and evaluator-input contracts | [Data guide](data-guide.html) · [Markdown](data/README.md) |
| Actual verification scope and gaps | [Verification](verification.html) · [Markdown](guide/verification.md) |
| v1 migration decisions and provenance | [Migration](migration.html) · [Markdown](guide/integration-migration.md) |
| Portable reading | [Print HTML](print.html) · [PDF](Foundry-Learning-Loop-Lab-KO.pdf) |

Keep the complete package together. Reading, local search and copying code work offline; the copy button does not execute commands. Copy shell commands from the web guide rather than visual line wrapping in the PDF.

## 5. Safety and evidence boundaries

- `python -m lab` is this repository's educational tool, not an official Microsoft CLI.
- Use only the newly authorized **North Central US** resources. Do not change existing/shared resources, shared policies or other regions.
- For this coordinated run, the user explicitly removed the monetary ceiling. **Workload bounds remain:** at most 300 calls, one job per optimizer with at most two candidates, one SFT job/epoch, and at most 60 minutes waiting per job. Other operators need their own authorization.
- GlobalStandard/Global/Developer processing is not a promise that processing stays in NCUS. Approval for synthetic data does not cover real customer data.
- **Preserve the new resource group for review. Deletion is not authorized.** Retaining Search or fine-tuned deployments can continue to incur charges.
- Distinguish AI-authored reviews from human reviews. Do not relabel an AI record as human or alter failed evidence to obtain a pass.
- The fresh 12-case holdout is created after freeze under a separate contract. It does not replace the original 20-case test split or silently lower its gate.
- Keep runtime environments, original approval records, credentials and raw run data out of source/publication bundles. Include only allowlisted, sanitized new-run evidence.
- This v1.1 package is self-contained. It does not require the v1 repository's executables or README.

## Maintainer checks

```bash
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -v
```

The builder creates all registered web pages and `print.html`; PDF generation and inspection are separate. The package remains **v1.1**. The integration documentation date is **2026-09-30**, not an assertion that every cloud feature was executed on that date.
