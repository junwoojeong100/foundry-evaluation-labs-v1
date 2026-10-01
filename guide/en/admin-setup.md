# Operator prerequisites · the fixed Sol v1/v2 pair {#operator-guide}

[Participant guide](handbook.md#start) · [Facilitator](facilitator.md#prepare) · [Latest v2 verification](verification.md)

Prepare the environment before class. The participant exercise is **dataset → evaluators → Foundry Evaluation → case analysis → Agent Optimizer → reevaluation**, not infrastructure construction.

## Use the existing isolated project {#start}

Use the operator-owned North Central US project, its existing policy connection, and the approved synthetic Contoso data. Confirm the actual account, tenant and subscription for the CLI, SDK and portal separately. Do not recreate resources, reuse production traffic or broaden shared permissions because a client is signed in as the wrong identity.

The English target is **`contoso-eval-en-sol`**. The original English and Korean source corpora remain separate. A Korean guide is not proof of a new Korean service run.

<figure class="portal-shot" id="portal-resource-group">
<img src="../../web/assets/portal/en/00-resource-group.png" alt="Earlier resource-group UI capture used only to locate the isolated lab, not current verification" width="1600" height="1000" loading="lazy">
<figcaption><strong>Resource-group orientation only.</strong> This earlier portal picture is not the current v2 result. Verify the actual project and current state from the operator handoff. <a href="../../web/assets/portal/en/00-resource-group.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

## Verify the three model roles {#prepare}

| Role | Actual deployment | Model/version |
|---|---|---|
| Agent | `lab-agent-sol-dea3cec5` | **`gpt-6-sol` / `2026-09-22`** |
| Managed Evaluation Judge | `lab-judge-luna-dea3cec5` | **`gpt-6-luna` / `2026-09-22`** |
| Agent Optimizer instruction generator | `lab-planner-dea3cec5` | **`gpt-5.5` / `2026-04-24`** |

Sol was verified through an actual pinned Foundry prompt-agent invocation and successful `knowledge_base_retrieve` call, not just a model catalog entry. The generated response used the four-field JSON contract. Both versions keep the same model, read-only tools, reasoning setting and structured-output schema.

The Optimizer model is a separate role with its own [supported-model list](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models). Do not assume that a model usable as an Agent or Judge is automatically an allowed optimization model.

<figure class="portal-shot" id="portal-models">
<img src="../../web/assets/portal/en/02-model-deployments.png" alt="Earlier model-deployment list showing where to inspect names and versions, not the current Sol deployment" width="1271" height="820" loading="lazy">
<figcaption><strong>Locate model/version fields.</strong> The picture predates the Sol deployment. Use the role table and current recorded API observations, not this older list, as runtime evidence. <a href="../../web/assets/portal/en/02-model-deployments.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

## Prepare a strong v1, then a controlled v2 {#bootstrap}

Use **`prompts/en/baseline.txt`** for the English baseline. It covers policy evidence, dates, routing, uncertainty and action boundaries. V1 must not be weakened to manufacture an apparent improvement.

**V1 and v2 are complete Foundry Agent versions**, not just document revision labels. In this comparison only their instructions differ. Changing the model, tools, reasoning or output schema requires a new matched experiment, not reuse of old-model scores.

Released versions are immutable. `ensure_fixed_release` in `lab/agents.py` permits only **1 and 2**, reuses a matching existing release, blocks mismatches and never silently creates v3. For development, use explicitly pinned **`draft-…`** versions. Draft support was verified in this subscription; verify it elsewhere because unsupported draft creation can fall back to a regular release.

`native_response_format()` projects the shared response schema into the supported strict-generation subset. Citation uniqueness and `needs_human`/route consistency are still checked after generation; a valid JSON shape alone is not policy correctness.

Keep the English registered dataset **`contoso-eval-en-dev12` version `1`**, all 12 rows from `data/en/optimizer/dev.jsonl`, with the original SHA-256. The Agent receives **`query` only**; reference columns are not injected into generation.

<a id="sdk-prerequisites"></a>

Provide Python 3.11–3.14, Azure CLI, the checked-out source and `requirements.lock`. Use a separate prepared environment, not an unrelated user's environment:

```bash
source .venv/bin/activate
python -m pip install -r requirements.lock
az login
az account show --query "{user:user.name,tenant:tenantId,subscription:id}" -o json
```

Check those values against the approved project. The operator supplies its endpoint, subscription, current evaluation ID and completed baseline run ID. Do not copy historical rehearsal IDs or use an Optimizer job ID as an evaluation ID.

The reevaluation helper clones the baseline data source and validates the **remote** evaluator contract. A stale local `JUDGE_DEPLOYMENT` must not replace the actual Judge in the evaluation definition.

## Freeze the comparison and spending scope {#scope}

<a id="approval"></a>

| Item | Fixed requirement |
|---|---|
| Data | Same English dev12 bytes, registration/version, questions and references |
| Relevance | Managed `builtin.relevance`, scale 1–5, threshold **4** |
| TaskAdherence | Managed `builtin.task_adherence`, binary 0/1, pass **1** |
| Judge | Same explicit Luna deployment in both evaluator definitions |
| Agent | Same Sol model/version, tools, reasoning and strict output schema |
| Change | Instructions only; releases remain v1/v2 |
| Optimizer | Instruction target only, model/tool-description changes off, bounded candidate count |
| Publication | Latest v2 and its frozen v1 control; all 12 sanitized case outcomes |

Catalog evaluator versions are not proof that the private service rubric is fully pinned. Preserve the actual definition, settings and this limitation. A passing gate on reused dev12 does not guarantee future scores, independent generalization or production approval.

## Verify least-privilege access {#rbac}

Use the [current Foundry RBAC guidance](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry). Participants need only the authorized project operations. Role-assignment authority is separate from model or evaluation access.

Keep the policy tool read-only. Do not assign subscription-wide Owner, disable network restrictions, change organization policy or transfer tokens between users as a shortcut.

## Costs and operational boundaries {#cost}

Evaluation invokes the Agent and Judge; optimization makes additional internal calls. Quota is not free usage, and GlobalStandard is not an NCUS-only processing guarantee. Record measured tokens and actual billing separately; unknown billing is not zero.

Name the cost/cleanup owner. Do not publish to production or activate a candidate merely because an Optimizer ranking increased. Keep the baseline active unless the measured decision and authorized operational review justify a change. Closing a browser does not stop resource charges.

## Hand off the current pair {#handoff}

Give participants the current Agent/version IDs, deployment-role map, dev12 hash, exact evaluator settings, SDK context, approval scope and [latest verification record](verification.md). The English report publishes actual responses, scores and reasons for every case.

Raw service files can contain account metadata, tokens or signed URLs. Keep those local; **the synthetic evaluation results themselves are not secret**. Publish only allowlisted fields, including failures, and exclude credentials—not inconvenient outcomes. Historical attempts stay in the private audit, not as additional current-version reports.
