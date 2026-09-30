# Foundry Learning Loop Lab v1

**[Start the lab in English → GitHub Pages](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/#start)** · **[한국어로 시작](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#start)** · [한국어 README](README.ko.md)

An evidence-first, hands-on workshop for evaluating and improving a Contoso support agent with **Microsoft Foundry**. Follow **six steps in approximately 3–4 hours**, including result discussions, command explanations, and 14 actual portal screenshots.

> Understand the example → connect the environment → evaluate the baseline → Foundry IQ → Agent Optimizer → decide and finish

**English is the default.** Every guide, reference, and complete print edition is available in English and Korean. Use **English / 한국어** in the header to switch the same document; section links and reading progress are preserved. No sign-in, installation, or JavaScript is needed to read the guides.

The English path uses its own **English policies, 100 cases, prompts, calibration references, and fresh-holdout recipes**. Select it with `LAB_LANGUAGE=en`; use `LAB_LANGUAGE=ko` for Korean. The original Korean corpus and results remain unchanged. Use separate environments and artifact directories: different-language runs are not paired improvement measurements.

## Getting started

- **Online:** Open the GitHub Pages link above. All HTML guide links below open the published site, not GitHub's source-file viewer.
- **Offline:** Download the complete repository and open `index.html` for English or `docs/ko/index.html` for Korean. Keep `docs/`, `web/`, and the other package directories together.
- **CLI labs:** Use Python 3.11+ (3.12 recommended), with bash/zsh or Windows WSL2. Follow [step 02](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/index.html#prepare) for installation and authentication.

Run the first offline demo from the repository root:

```bash
LAB_LANGUAGE=en python3 -S -m lab demo
```

`-S` skips Python's `site` initialization. `demo` prints authored examples without SDKs, Azure sign-in, network access, or paid model calls.

For later English commands, set `export LAB_LANGUAGE=en` before starting Python. The CLI defaults to Korean when the variable is absent, preserving older lab scripts; changing the website language does not change your terminal.

## Guides on GitHub Pages

| Guide | English | 한국어 |
|---|---|---|
| Six-step participant lab | [Start](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/index.html#start) | [실습 시작](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#start) |
| Operator setup | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/admin.html) | [운영자 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/admin.html) |
| Facilitation and recovery | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/facilitator.html) | [강사 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/facilitator.html) |
| Optional SFT and Frontier appendix | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/sft.html) | [SFT 부록](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/sft.html) |
| Synthetic data and evaluation contracts | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/data-guide.html) | [데이터 설명](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/data-guide.html) |
| Latest verification and sources | [Read](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/verification.html) | [검증·출처](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/verification.html) |
| Complete print edition | [Open](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/print.html) | [통합 인쇄본](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/print.html) |
| Downloadable PDF | [English PDF](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-EN.pdf) | [한국어 PDF](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-KO.pdf) |

Machine-readable documentation verification: [evidence/latest.json](evidence/latest.json).

## Boundaries

- Eight policies and 100 cases are synthetic. The last reported LIVE quality verdict is **HOLD**; execution success is not production approval.
- Paid labs require a dedicated **North Central US** environment and your own access/cost authorization. New infrastructure and SFT are outside the core time estimate.
- Never publish `.env`, `.lab/`, credentials, or raw run data. Repository cleanup does not delete Azure resources or stop hosting costs.

## Updating the guides

```bash
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -v
```

Run these from the repository root after installing `requirements.lock`. The builder generates **both languages and both print editions**; `--check` verifies all generated HTML without writing.

| Content | English source | Korean source |
|---|---|---|
| Participant, operator, facilitator, SFT, verification | `guide/en/*.md` | `guide/*.md` |
| Data guide | `data/README.en.md` | `data/README.md` |
| Shared interface text | `web/locales.json` → `en` | `web/locales.json` → `ko` |
| Generated HTML | `docs/*.html` | `docs/ko/*.html` |

Keep counterpart section IDs, including existing Korean IDs, so deep links and reading records remain compatible. Commands and examples must select the corresponding corpus. Maintain English runtime sources in `data/en/` and `prompts/en/`; never translate or overwrite recorded LIVE evidence in place. Run `python scripts/build_datasets.py --language en --check` and the Korean equivalent when updating data.

To refresh PDFs, open each complete print edition and save it as an A4 PDF with background graphics, using `docs/Foundry-Learning-Loop-Lab-EN.pdf` and `docs/Foundry-Learning-Loop-Lab-KO.pdf`. With the verification dependencies from `requirements-verification.lock` installed, run `python scripts/verify_pdf.py docs/Foundry-Learning-Loop-Lab-EN.pdf --language en` (use the Korean filename and `--language ko` for Korean). Then run `python scripts/package_lab.py` to rebuild the offline distribution ZIP.

GitHub Pages serves the **`main` branch root** with `.nojekyll`, making every generated HTML and its local assets accessible. Root `index.html` forwards to the English guide while preserving query strings and fragments. The former `docs/english.html` quickstart also forwards to the full English guide. `python -m lab` is an educational tool, not an official Microsoft CLI.
