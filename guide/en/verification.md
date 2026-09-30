# Latest verification record and limitations {#최신-검증-기록과-한계}

The **[latest result JSON](../../evidence/latest.json)** records the verification time, targets, and outcomes for the current distribution. This is the only verification record retained in the public package. Earlier verification, migration, and temporary evidence files remain in Git history, not in the current distribution.

## What is checked {#local}

| Target | Checks |
|---|---|
| Source data | Eight policies, 100 cases, and unchanged splits: train 56 / validation 12 / dev 12 / test 20 |
| Guides | Complete English/Korean guides in `docs/`, English-default root entry, language navigation, CLI syntax/explanations, and relative links |
| Portal screenshots | Fourteen actual screens: provenance, redactions, dimensions, hashes, display, and full-size links |
| Web and print | Desktop/mobile, light/dark themes, localized controls, print contents, and links |
| PDF | English/Korean text and required content; no blank/clipped pages or local-machine links; screenshots included |
| Package | Current files and one verification record only; no private environments, authentication data, or raw run records |

`status: PASS` in the verification JSON means **only the documentation/package checks explicitly listed in that file passed**. It is not Azure execution success, an agent-quality pass, or human operational approval. GitHub Pages serves generated static guides; it does not run the CLI or models.

## Keep verification separate from LIVE outcomes {#status}

The last reported **LIVE quality verdict on 2026-09-30 was HOLD**. Calibration disagreement and critical failures remained, the final fresh test was blocked, and human operational approval was absent. Evaluation definitions—including **retrieval Judge 1.1.0**—gates, and lab data remain unchanged.

This documentation translation/publication does not rerun paid models, evaluations, optimization, or training. Earlier scores/job IDs are not relabeled as new results, and successful documentation checks do not resolve the existing HOLD.

The real portal images were captured from the existing environment using headless Playwright. Check provenance and state in the [capture manifest](../../web/assets/portal/captures.json). Unsubmitted setup screens, existing service results, and the current participant's results are different things.

## Retention boundaries {#checks}

- Keep current runtime code, policies, data, evaluators, all 14 portal screenshots, and current bilingual HTML/PDF in `docs/`.
- Private `.lab/` execution, approval, and ownership records are not repository-cleanup targets.
- Do not change or delete Azure resources/permissions. Hosting/log costs do not stop automatically.
- Update `evidence/latest.json` when publishing new verification; do not add dated copies.

## Sources {#sources}

Contoso Atlas Cloud, its policies, and cases are synthetic materials for this lab—not actual provider terms or customer data.

The earlier workshop design reference is [a pinned commit in foundry-evaluation-labs-v0.9][source-workshop]. That archived repository may require separate access. Detailed migration history remains in this repository's Git history. Public access does not itself grant further reuse rights to referenced source material.

The official Microsoft Foundry icon and portal screenshots are attributed in [NOTICE](../../web/assets/NOTICE.txt), including their permitted usage. Preserve the official icon's original bytes and usage terms.

## Recheck locally {#update}

```bash
python -m lab validate
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -q
```

**Commands explained:** In order: validate source data, generate HTML in both languages, check freshness without writing, and run local tests. These commands do not call Azure. Regenerate/check PDFs and the ZIP separately, then record only the checks actually performed in the latest JSON.

[source-workshop]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/tree/93bc07e31373c4cfc278a2dc3757785946404cf2
