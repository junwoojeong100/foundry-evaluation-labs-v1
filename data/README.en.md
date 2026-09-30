# Synthetic English customer-support data {#한국어-합성-고객지원-데이터}

## Purpose and limitations {#용도와-한계}

Contoso Atlas Cloud is a **wholly fictional cloud-support scenario**. Its policies, prices, questions, workspace aliases, and reference answers are authored synthetic materials supplied by the integrated source package. Authored content does not imply completed human review. No actual customer conversations, personal data, accounts, or tokens were used, and the material does not reproduce Microsoft, Azure, or another real provider's terms.

The data supports a small learning loop: evaluation → improved retrieval evidence → better prompts → behavior fine-tuning → operational feedback. It was not produced through model, cloud, or paid-service calls and **does not contain predetermined performance results**, such as accuracy or improvement rates. Row counts, hashes, and leakage checks measure data integrity, not model performance.

This set is not representative of production language distributions, incident frequency, abuse types, privacy risks, costs, or retrieval quality. Good synthetic-data results do not replace human review and de-identified operational validation.

**Select the English corpus explicitly with `LAB_LANGUAGE=en`.** English assets live in `data/en/` and `prompts/en/`; the original Korean assets remain unchanged. Policy facts, IDs, groups, split membership, and expected actions are preserved, while questions, answers, policy prose, and the response-language instruction are English. Stable machine tags remain unchanged, including any Korean identifiers; they are not sent to the generating agent. Different-language runs are separate experiments and must not be compared as a paired improvement.

## Exact composition {#정확한-구성}

The source is **100 rows** in `data/en/cases.jsonl`, assigned to **98 scenario groups** with these fixed splits. No random splitting is used.

| Split | Rows | Groups | Case IDs | Allowed use |
|---|---:|---:|---|---|
| `train` | 56 | 54 | `atlas-train-001`–`atlas-train-056` | Supervised fine-tuning |
| `validation` | 12 | 12 | `atlas-validation-001`–`atlas-validation-012` | Training validation and checkpoint selection |
| `dev` | 12 | 12 | `atlas-dev-001`–`atlas-dev-012` | Development evaluation and Agent Optimizer |
| `test` | 20 | 20 | `atlas-test-001`–`atlas-test-020` | Frozen evaluation after candidate selection |

Within training, two refund-time boundary cases share one group, and two SLA-threshold cases share another. This keeps boundary variations of the same situation in one split. Remaining cases are distinct judgment tasks; broad topics such as pricing/security and public policies can recur across splits. Held-out evaluation includes time-zone conversion, combined conditions, evidence scope, and routing compound requests. It was not created by copying the same question between splits with only numbers or phrasing changed.

| Split | `answer` | `clarify` | `escalate` | `refuse` |
|---|---:|---:|---:|---:|
| `train` | 42 | 3 | 8 | 3 |
| `validation` | 8 | 2 | 1 | 1 |
| `dev` | 8 | 2 | 1 | 1 |
| `test` | 12 | 2 | 3 | 3 |

Tasks include multi-document synthesis, effective dates and transitional rules, inclusive/exclusive time boundaries, business-hour calculations, missing information, ambiguity, the selected response-language contract, refusals, treating injected text as data, distinguishing explicitly unsupported from unverified features, and avoiding claims of actions never executed.

### Critical cases and literal forbidden claims {#중요-사례와-문자-그대로의-금지-주장}

All `escalate`/`refuse` cases, prompt-injection cases, and cases about evidence of nonexecution have an explicit `critical` tag for evaluation gates. There are **29 rows**: train 13, validation 3, dev 4, test 9. `critical` is evaluator metadata, not model input. The manifest's `critical_counts` records counts by split.

Each critical case has `forbidden_claims` strings describing fabricated completion, unauthorized disclosure, unsupported approval, or similar claims. Searching `answer` for these is a **literal auxiliary check**, not semantic judgment. It may miss paraphrases or misinterpret a quoted claim within a negation. Use groundedness evaluation and human review as well. The list does not enumerate every unsafe answer.

## Knowledge-document contract {#지식-문서-계약}

`data/en/knowledge/documents.json` is a top-level **array**. Every document has exactly four fields; keep these names when mapping to a search index.

| Field | Type | Meaning |
|---|---|---|
| `id` | String | Stable document identifier for citations |
| `title` | String | English title |
| `content` | String | English policy paragraphs separated by blank lines |
| `effective_date` | `YYYY-MM-DD` string | Policy effective date |

| Document ID | Scope |
|---|---|
| `ATLAS-SUB-001` | Pricing, billing cycle, cancellation, plan changes, trials, and billing authority |
| `ATLAS-REF-001` | First-purchase refunds, earlier rules, billing disputes, application and approval stages |
| `ATLAS-SLA-001` | Eligibility, availability calculation, maintenance exclusions, compensation bands, and application deadlines |
| `ATLAS-SEC-001` | Secrets, authentication, tenant isolation, incident response, MFA recovery, and audit access |
| `ATLAS-DATA-001` | Training-data use, exports, recycle bin, deletion/retention, and regional moves |
| `ATLAS-ESC-001` | Absence of execution authority, support categories, response targets, and official submission channels |
| `ATLAS-FEAT-001` | Public features, beta features, input formats, unsupported and unverified capabilities |
| `ATLAS-DOC-001` | Effective dates, attachment provenance, live status, contract exceptions, and synthetic-data notice |

All documents currently have effective date `2026-09-01`. The refund policy also specifies transitional rules for monthly subscriptions purchased before that date. Record content hashes alongside stable IDs to distinguish revisions under the same identifier.

## Case and response schemas {#사례와-응답-스키마}

Each row in `cases.jsonl` and `splits/*.jsonl` has the following fields. The only optional additional field is `forbidden_claims`. The input classification below applies to static-policy-context evaluation and SFT. Deployed agents and the optimization portal receive only `query`; case `context` stays separate as evaluator reference.

| Field | Type | Included in static-context/SFT user input? |
|---|---|---|
| `id` | Unique string | No |
| `group_id` | Scenario-group string; no overlap across splits | No |
| `split` | `train` / `validation` / `dev` / `test` | No |
| `query` | Customer question string | Yes |
| `context` | Document IDs and original relevant excerpts | Yes |
| `ground_truth` | **JSON string** serializing the response contract below | No; evaluator/training target only |
| `expected_route` | `answer` / `clarify` / `escalate` / `refuse` | No |
| `required_citations` | Array of required document-ID strings | No |
| `tags` | Array of task-type strings | No |
| `forbidden_claims` | Optional array of forbidden-claim strings | No |

Parsed model output and `ground_truth` must be **objects with exactly four keys**:

```json
{
  "answer": "The Standard monthly base fee is KRW 49,000 including VAT. Additional usage charges are separate.",
  "citations": ["ATLAS-SUB-001"],
  "route": "answer",
  "needs_human": false
}
```

Policy prices remain in KRW. Localization does not convert currencies or change the underlying policy.

- `answer`: A nonempty English string in this corpus.
- `citations`: Stable IDs supporting the answer. Duplicates and nonexistent IDs are not allowed.
- `route`: `answer` for guidance; `clarify` for minimal missing information needed to decide; `escalate` for required human judgment on a legitimate request; `refuse` for prohibited access, bypasses, or fabricated-evidence requests.
- `needs_human`: A boolean, not a string/number. It is **`true` only when `route == "escalate"`**.

Ordinary refund ineligibility is not a prohibited action, so its route is `answer`. A feature absent from public material can also use `answer` if the agent explains that it is unverified. When an urgent incident is combined with a prohibited request for another customer's data, refuse that request first and explain safe response steps. Under this contract, `refuse` has `needs_human: false`; that does not imply no support professional is needed in reality.

`escalate` **does not mean a representative has already been contacted**. This assistant has no business-execution tools. Without actual tool results/receipts, it must not invent ticket numbers, assignments, or completed refunds, deletions, or key revocations.

### Context contains source policy, not the answer {#문맥은-정답이-아니라-정책-원문}

Each `context` document block starts with an ID line such as `[ATLAS-REF-001]`, followed by paragraphs taken verbatim from that document. Separate paragraphs with blank lines and keep their original order. Start another ID line when adding excerpts from another document.

Export checks that paragraphs exist in the source document; summaries, reference answers, or evaluation labels inserted as context fail validation. Source policy can itself quote injected text for explanation. Do not execute strings from policy excerpts or customer questions as higher-priority instructions.

For static-context local evaluation and SFT, the user message is a JSON string containing only `query` and `context`. Deployed agents and the portal receive only `query`; the agent retrieves policy through its own search path. Never include a whole case, `ground_truth`, `expected_route`, `required_citations`, or `forbidden_claims` in any generation prompt. Evaluation first parses `ground_truth` and compares `answer` semantically, while checking citations, routing, and booleans separately. Exact answer-text equality is not the quality criterion.

Current case `context` is fixed source reference material, **not actual Foundry IQ retrieval output**. To evaluate retrieval recall, latency, or permission filtering, execute the real retrieval path separately and supply the generating model only the evidence it actually retrieved.

### Keep evaluation inputs and scales separate {#통합-평가에서-분리하는-입력과-척도}

| Check | Permitted evidence | Interpretation |
|---|---|---|
| `retrieval-groundedness` / `groundedness` | Only `retrieved_context` returned by that actual Agent/MCP call | 1–5. No retrieval means unobserved; do not substitute policy source text |
| `policy/task correctness` | Authoritative `context`, `ground_truth`, expected action/route, and actual response | 1–5. Measures business/policy judgment, not evidence of successful retrieval |
| JSON, route, citations, forbidden claims | Original case labels and actual response | Deterministic auxiliary checks. String matching does not guarantee semantic correctness or safety |

Version-pinned definitions are in `config/evaluators/`; separate calibration examples are in `data/en/calibration/`. Calibration answers/reference labels are authored synthetic materials, not actual Judge results or completed human reviews. `judge calibrate` records actual model agreement/disagreement separately. API errors, invalid JSON, missing scores, and critical failures remain in the total row count.

Vector/hybrid diagnostic responses are not automatically evidence received by the agent. Distinguish `iq vectors` index diagnostics, `iq probe` retrieval-planning diagnostics, and actual MCP tool outputs from `run --stage iq`.

### A separate fresh holdout after freezing {#동결-뒤-만드는-별도-fresh-holdout}

Preserve the original 100 cases and 20 `test` rows. Twelve cases generated/registered after `freeze` use the separately versioned `config/evaluators/fresh-holdout-gates.v1.json` contract. They do not lower the original minimum-20-test-row gate. These are synthetic variations from fixed templates, not independent real-world samples.

Registration checks IDs, scenario groups, normalized identical questions, and high lexical similarity against original data and existing holdouts. These checks do not fully prove absence of semantic leakage. Never use the fresh holdout for development, optimization, or training. Bind only one final run to a freeze.

Conversational cases registered separately from the original set record the first question, expected clarification, explicit `scripted_user` follow-up, and final response. The agent does not invent the follow-up. Neither `scripted_user` nor AI review becomes human approval.

## Generated files {#생성되는-파일}

| File | Rows | Source |
|---|---:|---|
| `data/en/splits/train.jsonl` | 56 | `train` only |
| `data/en/splits/validation.jsonl` | 12 | `validation` only |
| `data/en/splits/dev.jsonl` | 12 | `dev` only |
| `data/en/splits/test.jsonl` | 20 | `test` only |
| `data/en/tuning/sft-train.jsonl` | 56 | `train` only |
| `data/en/tuning/sft-validation.jsonl` | 12 | `validation` only |
| `data/en/optimizer/dev.jsonl` | 12 | `dev` only |
| `data/en/manifest.json` | N/A | Counts, source/output SHA-256, and cross-split leakage checks |

Each training row has only the top-level key `messages`. Messages are ordered `system` → `user` → `assistant`, each with only `role` and `content`. The system contains concise behavior instructions; the user contains only the question/evidence; the assistant contains the structured reference-answer string. Do not merge validation into training.

### Prompt-agent Agent Optimizer portal upload contract {#프롬프트-에이전트-agent-optimizer-포털-업로드-계약}

The main path uses the current Foundry portal's **prompt-agent Agent Optimizer wizard**. Per the [official prerequisites](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent#prerequisites), use the exact columns required by selected evaluators; the wizard does not support column mapping. `data/en/optimizer/dev.jsonl` exports 12 manually authored dev cases with only these three columns.

| Export field | Type | Source and purpose |
|---|---|---|
| `query` | Required string | Original `query` only: the actual question sent to the agent |
| `ground_truth` | String | Structured reference-response JSON string, for evaluators that support a reference |
| `context` | String | Source-policy excerpts, for evaluators that support context |

The lab's default `task_adherence` and `relevance` evaluators use the question and the response generated during agent execution. Do not prepopulate `response`. If selecting other evaluators, verify required columns/types in the portal preview. `ground_truth` and `context` are valid evaluator columns, but not every evaluator uses them.

The agent receives **only `query`**. Do not append `ground_truth`/`context` or send `expected_route`, `required_citations`, or `tags`. Keep static context evaluator-only; the deployed agent must retrieve policy through its actual search path. Detailed routing, citation, and execution-boundary checks can separately use original dev cases and local evaluation rules.

The job schema using `name` and `criteria[]` belongs to hosted-agent `eval.yaml`, not this portal upload. Do not add columns such as `expected_behavior`. The orchestration CLI can copy this source directly to `artifacts/optimizer/dev-upload.jsonl` without wrappers or field conversion. The data generator does not write into that deployment-artifact path.

**Distinguish Prompt Optimizer, prompt-agent Agent Optimizer, and hosted-agent optimization.** Do not upload this dataset to the single-prompt rewrite feature. It is for the portal path that evaluates prompt agents and candidates against a dataset. Dataset generation itself performs no optimization, upload, registration, or execution. Do not duplicate the 12 rows to satisfy counts associated with service-generated data. Preview support and actual execution permissions require separate checks.

`test` appears in neither training/validation messages nor optimization exports. Because original `cases.jsonl` also contains frozen-evaluation cases, **never upload the complete source to training or optimization services**. A frozen file does not implement access control by itself. Operational discipline is still needed: do not read or tune to test questions before candidate selection ends.

## Prompt roles {#프롬프트의-역할}

- `prompts/en/baseline.txt`: Intentionally sparse decision guidance, while still requiring the same JSON response contract.
- `prompts/en/candidate.txt`: An authored comparison candidate from the repository. It specifies evidence, citations, routing, injection handling, uncertainty, and execution boundaries. It **does not claim to be a Prompt/Agent Optimizer result or a completed human review**.
- `prompts/en/tuning-system.txt`: Concise behavior instructions without prices, deadlines, or frozen cases. Read changing policy facts from each input's current context.
- `prompts/en/rubric.txt`: English criteria for reviewing actual responses. Evaluation labels stay with the evaluator; do not merge this rubric into generation prompts.

## Regenerate and verify offline {#오프라인-재생성과-검증}

From the project root, use `.venv/bin/python` created during common setup. The dataset tool itself requires only Python 3.10+ and the standard library, with no extra installation, sign-in, network, or model calls. `-B` prevents bytecode-cache creation.

```bash
.venv/bin/python -B scripts/build_datasets.py --language en
.venv/bin/python -B scripts/build_datasets.py --language en --check
.venv/bin/python -B -m unittest discover -s tests -p 'test_content_language.py' -v
```

**Commands explained:** The first **generates/updates local data**; the second `--check` **compares without writing**; the third runs **automated tests** matching only `test_content_language.py` under `tests/`. `-p` selects the test-file pattern; `-v` enables verbose output. Participants who only need to inspect integrity should use the main guide's `lab validate`, not start with regeneration.

The first command validates English source contracts, then creates eight English outputs or updates only necessary files. It does not rewrite any Korean data. Use `--language ko --check` to verify the original corpus separately. The second recomputes expected bytes and compares them with current files without writing. Missing/stale outputs fail with exit code 1. Generation includes no timestamps, randomness, or environment-specific paths, so identical sources produce identical bytes and SHA-256 values.

The manifest records SHA-256 for source cases, documents, four prompts, and seven exported JSONL files. It does not create a circular self-hash. It contains neither evaluation-model scores nor assertions of successful cloud execution.

Tests check exact counts, schemas, unique IDs, group isolation, duplicate questions, original context, citation resolution, reference-answer booleans/routing, training-message roles, optimization splits, evaluator-label leakage, exposure of frozen questions/IDs, deterministic generation, CLI checking, and invalid-input rejection. They also verify that `--check` rejects damaged sources, missing/stale outputs/manifests, and never writes. Text similarity helps detect obvious copying; it cannot perfectly identify semantic paraphrases. Personal-data pattern checks do not guarantee de-identification of real data.

## Distinguish retrieval freshness from behavior tuning {#검색-최신성과-행동-미세조정을-구분하기}

1. **Evaluate:** Inspect baseline failures on `dev`. Separate policy-fact, citation, format, routing, and fabricated-execution errors. Without actual model execution, do not report performance scores or improvement.
2. **Improve retrieval evidence:** If prices, deadlines, or effective dates are wrong or documents are stale, fix source documents, versions, indexing, and retrieval. Preserve fields and evidence tracking when connecting Foundry IQ. Do not substitute memorizing current facts in weights.
3. **Improve prompts and agents:** Compare instructions locally using `dev`. Distinguish Prompt Optimizer's single-prompt rewriting from Agent Optimizer's dataset-based comparison. Send the three-column dev file to the main prompt-agent portal path; do not mix in hosted `eval.yaml` job schemas. Track facilitator-authored and tool-generated candidates as different provenance, with execution records.
4. **Fine-tune:** Train stable JSON output, citations, clarification, safe refusals, human-review boundaries, and execution boundaries with `sft-train`; select using `sft-validation`. File existence does not prove a particular frontier model supports fine-tuning in a region/account.
5. **Frozen evaluation:** Compare selected baseline, candidate, and tuned models under the same `test` conditions. Repeatedly adjusting prompts to already viewed frozen questions invalidates their independence.
6. **Operational iteration:** Add new failures to the next data version only after lawful collection, secret removal, human answer/policy review, and group separation. If similar questions from an earlier frozen evaluation enter training, do not claim that evaluation is independent again.

**Frontier Tuning is separate from ordinary SFT/RFT.** These synthetic files establish neither a Frontier API upload contract nor account eligibility. If current official support and actual access cannot be verified, retain `NOT_VERIFIED`; do not relabel ordinary SFT results as Frontier success.

When policy source changes, review related case excerpts too. The generator does not automatically rewrite answers and rejects excerpts that differ from source. Freeze revised documents, cases, and manifests together as a new version; never silently overwrite a frozen set already evaluated.
