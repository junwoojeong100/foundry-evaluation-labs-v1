# Foundry Learning Loop Lab v1 · English

**[Read the lab online → GitHub Pages](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/#start)**

An evidence-first workshop for evaluating and improving a Contoso support agent. Follow **six steps in approximately 3–4 hours**, with feature explanations, CLI details, and 14 actual portal screenshots. The scenario, prompts, and responses are **Korean**.

> Understand the example → connect the environment → evaluate the baseline → Foundry IQ → Agent Optimizer → decide and finish

## Getting started

- **Online:** Open GitHub Pages above. Reading needs no installation or sign-in.
- **Offline:** Download the complete repository and open the [guide](docs/index.html#start), or read the [combined PDF](docs/Foundry-Learning-Loop-Lab-KO.pdf).
- **CLI labs:** Use Python 3.11+ (3.12 recommended) and bash/zsh or Windows WSL2. Follow [step 02](docs/index.html#prepare) for installation and authentication.

Run the first offline demo from the repository root:

```bash
python3 -S -m lab demo
```

`-S` skips Python's `site` initialization; `demo` prints authored examples without SDKs, Azure sign-in, network access, or paid model calls.

## Documentation

| Topic | Document |
|---|---|
| Environment setup | [Operator guide](docs/admin.html) |
| Facilitation and recovery | [Facilitator guide](docs/facilitator.html) |
| Optional advanced lab | [SFT appendix](docs/sft.html) |
| Data contracts | [Data guide](docs/data-guide.html) |
| Latest verification and attribution | [Guide](docs/verification.html) · [Result JSON](evidence/latest.json) |
| 한국어 | [README.md](README.md) |

## Boundaries

- Eight policies and 100 cases are synthetic. The last LIVE quality verdict is **HOLD**; execution success is not production approval.
- Paid labs require an owned **North Central US** environment and your own access/cost authorization. New infrastructure and SFT are outside the core time estimate.
- Never publish `.env`, `.lab/`, credentials, or raw run data. Repository cleanup does not delete Azure resources or stop hosting costs.

## Updating the guide

```bash
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -v
```

Generated HTML/PDF live in `docs/`; guide sources live in `guide/`. Run the commands from the repository root to build HTML, check freshness, and run local tests. Regenerate PDF/ZIP separately.

GitHub Pages serves the `main` branch root with `.nojekyll`; root `index.html` forwards to the guide. `python -m lab` is an educational tool, not an official Microsoft CLI.
