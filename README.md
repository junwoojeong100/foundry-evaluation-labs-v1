# Foundry Learning Loop Lab v1

**[Start in English](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/)** · **[한국어 가이드](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html)** · [한국어 README](README.ko.md)

**Follow ten steps from your first Azure environment checks to authorized cleanup or retention.** Use Microsoft Foundry managed Evaluation and Agent Optimizer to evaluate and improve an Agent against representative business tasks:

> Account, tools, and access → Foundry creation → policies and Agent → dataset → criteria → evaluation → analysis → optimization → reevaluation → verified cleanup

The sample Contoso policies and questions are synthetic. The lesson is **evaluate → learn → improve → reevaluate**, not a public benchmark leaderboard or production certification.

**Every participant builds and runs the complete lab with their own account and computer.** Start at 01: install tools, create a dedicated environment, connect policies, create the Agent, register data, evaluate, optimize, compare, and clean up. The guide includes OS-specific commands, actual input locations, authorization fields, and completion checks. When resuming your own lab, verify its original records instead of duplicating completed work.

**Local prerequisites: Python 3.11–3.14, Git, and Azure CLI.** [Step 01 installation instructions](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/index.html#setup-local) cover Windows WinGet/official installers, macOS Homebrew, and Ubuntu 24.04 LTS, with version checks before creating the virtual environment. Reuse supported tools already installed; resolve PATH or installation restrictions before signing in to Azure.

**New to Azure or Foundry? Read the hands-on guide first.** It explains accounts, subscriptions, projects, and opening a terminal before using them. Steps 04–06 form one evaluation wizard, with ordered actions and score-reading examples. Setup references and checklists support the same path; they do not assign exercises to separate workshop roles. Obtain the required provisioning, role-assignment, and spending authorization before creating Azure resources.

The opening explains what the lab is, why it matters, how it proceeds, and what evidence remains. Each step follows **what → why → how/where → actual screen and execution → completion criteria**.

**Existing lab commands and runtime code are unchanged.** Each step starts with **Action order** links, and every **code ↔ portal** table links to the actual command or portal procedure. **Run in your terminal** blocks have OS labels and command-copy buttons; long commands wrap visually without changing copied text. Code/portal maps become labeled cards on mobile, while desktop and print retain tables. Complete source functions/settings remain available in collapsed, read-only panels and are expanded in the print edition. Labels and action links also work without JavaScript. Dataset registration, baseline submission, and Optimizer execution remain portal actions, not additional terminal commands.

## Fixed model roles and comparison conditions

| Role | Planned model/version |
|---|---|
| Agent | **gpt-6-sol / 2026-09-22** |
| Foundry Evaluation Judge | **gpt-6-luna / 2026-09-22** |
| Agent Optimizer generator | **gpt-5.5 / 2026-04-24** |

New lab Agents use `lab-en-iq` or `lab-ko-iq`, unless a different environment prefix is selected. V1/v2 are complete immutable Agent versions; **only their instructions differ**. Keep models, tools, reasoning, strict JSON output, data and evaluators fixed. Never weaken v1 to manufacture improvement.

`ensure_fixed_release` permits released versions **1 and 2**, reuses equivalent configurations, and rejects silent v3 creation or overwrites. Use the reviewed instructions from your own Optimizer job. Record any manual corrections separately from the original service output. If no different candidate is worth retaining, keep v1 and follow the retention/cleanup branch without inventing a v2 comparison.

## Fixed data and criteria

Use unchanged **`data/en/optimizer/dev.jsonl`** for English and **`data/optimizer/dev.jsonl`** for Korean. Register the selected language as `lab-en-dev12` or `lab-ko-dev12`, version `1`. The **12 JSONL records** contain `query`, `context`, and a JSON-string `ground_truth`. Only `query` reaches the Agent; never mix language corpora or run folders.

| Managed evaluator | Scale and pass rule |
|---|---|
| Relevance | 1–5, threshold **4** |
| TaskAdherence | Binary 0/1 Pass/Fail, pass **1** |

The SDK helper adds a real run to the existing Foundry definition. It checks the remote Judge, thresholds and response mappings, prevents duplicate submissions, and verifies each output's actual pinned version and instructions. It is **not a local Judge**.

`scripts/compare_foundry_eval.py` requires complete matched cases, no lower quality pass counts/means, and at least one strict measured improvement. It does not hide malformed responses or claim that stochastic future results are guaranteed. Native statistical conclusions, latency and token tradeoffs are reported separately.

## Guides

| Guide | English | 한국어 |
|---|---|---|
| Hands-on path | [Start](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/index.html) | [실습](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html) |
| Environment setup reference | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/admin.html) | [환경 설정](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/admin.html) |
| Lab checklist | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/facilitator.html) | [체크리스트](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/facilitator.html) |
| Data contract | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/data-guide.html) | [데이터](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/data-guide.html) |
| Troubleshooting | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/troubleshooting.html) | [문제 해결](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/troubleshooting.html) |
| Complete print edition | [Open](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/print.html) | [인쇄본](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/print.html) |
| PDF | [English](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-EN.pdf) | [한국어](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-KO.pdf) |
| CLI/SDK lab replay | [English MP4](docs/media/Foundry-Lab-Replay-EN.mp4) | [한국어 MP4](docs/media/Foundry-Lab-Replay-KO.mp4) |
| Actual portal walkthrough | [English MP4](docs/media/Foundry-Portal-Walkthrough-EN.mp4) | [한국어 MP4](docs/media/Foundry-Portal-Walkthrough-KO.mp4) |

Both video types include narration, subtitles and chapter markers and remain separate from the reusable guides. The CLI/SDK videos replay execution records. The portal walkthroughs record the authenticated Azure/Foundry UI, with personal fields redacted, using existing resources and completed runs without resubmitting evaluations or optimization. External subtitles: CLI/SDK [English](docs/media/Foundry-Lab-Replay-EN.srt) · [한국어](docs/media/Foundry-Lab-Replay-KO.srt); portal [English](docs/media/Foundry-Portal-Walkthrough-EN.srt) · [한국어](docs/media/Foundry-Portal-Walkthrough-KO.srt).

English is the default. Language switching preserves the corresponding section, reading progress and theme. Guides work without login or JavaScript. For offline use, download the whole repository/package and keep its folders together.

Hands-on sidebars show only the ten main steps. Detailed headings and direct links remain in the body; reference documents keep their own navigation. Existing reference filenames and section links remain valid.

Portal pictures illustrate UI locations; they are not a claim about your own run. English and Korean use their respective image sets, while subscription/access controls share `web/assets/portal/shared/`. Asset sources, privacy edits and illustration metadata are documented in [NOTICE](web/assets/NOTICE.txt) and the capture manifests.

## Execution boundaries

You prepare your own isolated project and read-only policy connection in 01–03. Separate Judge calibration and governance are not required exercises. The Agent advises; it cannot issue refunds, submit tickets, delete data, or grant access.

Runtime availability is role-specific. Verify the actual Agent/tool path and the [supported optimization models](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models). Do not change model roles midway through a comparison.

Production publication is not part of the lab. Closing a browser does not stop resource costs. Preserve genuine failures and do not rerun an unchanged candidate until a favorable sample appears.

Step 10 preserves results and checks ownership and authorization. The default path deletes your dedicated lab group and verifies `az group exists` returns `false`. `cleanup` is an optional object-only path when retaining the group: without confirmation it only displays a plan; confirmed cleanup does not remove all Search/model/group hosting. Explicit retention requires the remaining inventory, cost responsibility, review date, and subsequent deletion plan. Shared or external resources are never automatic deletion targets.

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

`<!-- source-code: lab/agents.py:create_native_agent -->` includes the complete named symbol; `<!-- source-code: schemas/response.schema.json -->` includes the complete file. The guide builder reads and escapes source without importing/executing it, preserving original comments, identifiers, and messages. Keep source directives reciprocal across languages and rebuild web/print/PDF output after relevant implementation changes. Do not copy source into independent runnable examples or edit original code just to simplify its presentation.

Korean documentation, guidance, and error messages use a consistent formal register. Preserve verbatim measured responses, evaluator reasons, and evaluation-data quotations rather than editing evidence for prose style.

Render both print editions as A4 PDFs with background graphics. With the dependencies in `requirements-verification.lock`, verify the actual PDF paths:

```bash
python -m scripts.verify_pdf docs/Foundry-Learning-Loop-Lab-EN.pdf --language en --out .lab/guide-checks/pdf-en.json
python -m scripts.verify_pdf docs/Foundry-Learning-Loop-Lab-KO.pdf --language ko --out .lab/guide-checks/pdf-ko.json
```

Build the allowlisted ZIP with `python scripts/package_lab.py`.

Keep execution-specific scores, run IDs, validation logs and raw results in ignored private run folders, not in reusable guide sources. Correct a guide only when its instructions are wrong. Keep necessary ownership/configuration records for retained resources; remove superseded reports and temporary output without deleting cloud resources.

GitHub Pages serves **main / repository root** with `.nojekyll`. Root `index.html` and legacy `docs/english.html` forward to English while preserving query strings and fragments.
