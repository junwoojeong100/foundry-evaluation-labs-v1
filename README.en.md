# Foundry Learning Loop Lab v1 · English

**[Read the lab online → GitHub Pages](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/#start)**

Reading the guide needs no installation. For a downloaded package, open [index.html](index.html#start). GitHub Pages serves static documentation only; it does not sign in to Azure, run CLI commands, or execute paid labs.

**Follow six steps on one page, in order.** You do not need to choose a document, evaluator path, or optimizer.

> Understand the example → connect the environment → evaluate the baseline → connect Foundry IQ → improve instructions with Agent Optimizer → decide and finish

**Plan for approximately 3–4 hours, including result discussions**, with an existing environment and successful calibration. This is an estimate, not a measured guarantee; new environment provisioning and SFT are excluded. Each step follows **understand the feature → command and explanation → sample output → discuss your results and decision → next step**. Samples illustrate the format and are not evidence of a successful live run.

Every lab now explains **what the feature is, why it matters, and how to use it**. Command explanations cover options, inputs, output files, cloud/cost boundaries, and safe continuation. New CLI users can start with the [command-reading primer](index.html#cli-basics).

**Fourteen actual Foundry Portal screenshots** accompany the relevant steps and SFT appendix. They were captured through **headless Playwright MCP** after user authentication, covering the existing project, deployments, agents, IQ, optimizer, evaluations, MCP traces, and SFT job. Start at the [project screen](index.html#portal-project); each caption explains navigation and interpretation and links to the full-size image. Personal/endpoint fields are redacted. Wizard screenshots are unsubmitted drafts, result screens are existing runs, and no new paid jobs were started for these captures.

At each evaluation, share **actual results → a representative case → the next decision**. Calibration, baseline diagnosis, IQ, optimizer ranking, candidate re-evaluation, and the fresh holdout answer different questions. These checkpoints use existing reports; they add no paid evaluation calls or automatic external sharing.

The local `explain` command connects **criteria, measured scores, saved Judge reasons, HOLD causes, and improvement suggestions**. For strictly paired runs it also computes the configured regression diagnostics. The guide includes score-level rubrics, a worked teaching example, and next-action rules; explanations never rewrite existing evaluation evidence or grant approval.

**This is the same lab and environment.** Keep the existing dedicated NCUS resources, Contoso data, models, and evaluation criteria. Do not redeploy or rerun completed experiments because the guide changed. The former 15 chapters are grouped into six steps; the underlying tools remain available.

## Before starting

Keep the complete package in one folder and open `index.html`. Use Python 3.11+ (3.12 recommended) and bash/zsh on macOS/Linux or Ubuntu in Windows WSL2. The policy, cases, prompts, and responses remain **Korean** so participants use the same experiment.

The top-right **어둡게/밝게** control remembers light/dark mode in this browser. **현재 인쇄** prints the current step; **전체 PDF** opens the entire current document in the print dialog, where you can choose Save as PDF. Printing always uses a light background. The footer links to the combined PDF including appendices.

Step 01 is an **AI-authored offline DEMO**. It needs no Azure login, `.env`, Azure CLI, SDK installation, network, or paid requests. Subsequent installation and commands are in the handbook, not a second quickstart.

Before LIVE work, the operator verifies the participant's actual identity, permissions, dedicated environment, and current cost authorization, then supplies the private environment folder. Follow [operator setup](admin.html) **only if no lab environment exists yet**. Otherwise reconnect using the original ownership manifest; do not create another resource group.

## The only participant path

| Step | Evidence to keep |
|---|---|
| 01. Understand the example | Your judgment about the false refund promise and missing information |
| 02. Connect the environment | Ownership/preflight checks and the original dataset validation |
| 03. Evaluate the baseline | Actual Agent responses and business Judge calibration |
| 04. Connect knowledge | Actual IQ retrieval/MCP output and all 12 dev cases |
| 05. Improve instructions | One Agent Optimizer candidate and paired dev evidence |
| 06. Decide and finish | Frozen fresh12 results or reasons for not running them, HOLD decisions, and preservation responsibility |

**Stop at step 06.** Prompt Optimizer, separate managed evaluation, SFT, and Frontier remain reference/advanced material, not requirements for completing this path. On errors or failed calibration, stop paid progression and record the evidence and unexecuted steps. Learning completion, actual API success, quality acceptance, and human production approval are distinct.

## Boundaries

- Preserve eight synthetic policies and 100 cases: train 56 / validation 12 / dev 12 / test 20. Create the separate fresh12 only after freeze; never lower the original test20 gate.
- Use only the owned, dedicated **North Central US** environment. Do not switch to unrelated existing/shared resources, shared policies, or other regions.
- Each participant needs current authorization for cost, processing, and workload. The earlier run's explicit removal of a monetary ceiling is not transferable authorization. Finite call, job, candidate, and waiting bounds still apply.
- **Preserve resources and raw evidence. Deletion is not authorized.** Search, logs, and model hosting can keep incurring costs after the terminal closes.
- Keep AI authorship/review separate from human review and approval. Never change failed evidence or thresholds to obtain a pass.
- Keep private environments, approval records, credentials, and raw run data out of source, ZIP, and PDF bundles. Publish only sanitized, allowlisted evidence.

## Reference only — not additional participant steps

| Topic | Document |
|---|---|
| Source handbook | [Markdown](guide/handbook.md) |
| Identity, resources, cost, recovery | [Operator guide](admin.html) |
| Facilitation, recovery, separate diagnostics | [Facilitator guide](facilitator.html) |
| Optional SFT and Frontier | [Advanced appendix](sft.html) |
| Data contracts | [Data guide](data-guide.html) |
| Existing LIVE evidence and gaps | [Verification](verification.html) |
| Migration decisions and provenance | [Migration](migration.html) |
| Korean entry point | [한국어](README.md) |
| Portable reading | [Print HTML](print.html) · [PDF](Foundry-Learning-Loop-Lab-KO.pdf) |

Existing LIVE evidence includes actual Agent, IQ, optimizer, and SFT results alongside **HOLD**, calibration disagreements, execution errors, and missing human approval. This guide revision does not alter those results or claim a new successful run. Copying code does not execute it.

## Maintainer checks

The directory and [GitHub repository](https://github.com/junwoojeong100/foundry-evaluation-labs-v1) are named **`foundry-evaluation-labs-v1`**, and the guide edition is **v1**. In the existing development environment, the previous path is a compatibility symlink for virtualenv and frozen-record absolute paths, not a second copy. New installations do not need this link.

```bash
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -v
```

**Command details:** The first command renders the registered HTML pages and combined print HTML from Markdown. `--check` verifies freshness without writing. The final command runs the local test suite with verbose output (`-v`); it does not execute Azure labs or regenerate the PDF. Screenshot updates must also update the route, redactions, dimensions, and hash in `web/assets/portal/captures.json`.

The builder generates HTML and the print book; regenerate PDF and ZIP separately. `python -m lab` is this repository's educational tool, not an official Microsoft CLI. The guide edition is **v1** and the documentation date is **2026-09-30**.

**Online publishing:** GitHub Pages uses the `main` branch and `/ (root)`. The root `.nojekyll` file serves the generated HTML and relative assets without Jekyll processing. Rebuild HTML/PDF, commit, and push to update the site. Public repository access does not publish private `.lab/` environments, credentials, approvals, or raw execution records, and does not grant Azure access.
