<p class="eyebrow">PORTAL ONLY · v1.1 · English</p>

# Microsoft Foundry Evaluation and Optimization Lab v1.1

**New resource group → policy-searching Agent → baseline evaluation → instruction optimization → reevaluation under the same conditions.** Complete the lab by clicking and entering values in Azure Portal and Foundry Portal. No terminal, Cloud Shell, installation, or scripts are required.
{: .hero-summary}

<div class="hero-summary">
<div><strong>Azure Portal</strong><span>Create a new resource group and verify the actual resources.</span></div>
<div><strong>Foundry Portal</strong><span>Build the Agent, evaluate it, and run Optimize.</span></div>
<div><strong>Outcome</strong><span>Compare responses, scores, and errors for two Agent versions under the same conditions.</span></div>
</div>

[한국어 가이드](../handbook.v1.1.md) · [Watch the actual portal recording · Korean captions](../../docs/media/portal.v1.1.html) · [Existing v1 guide](handbook.md)

**This is a separate path.** Do not mix in v1 environments, commands, or model settings. The Contoso Atlas Cloud policies and questions are synthetic training material, not Microsoft or real customer terms. Do not publish to production or perform real refunds, deletions, or permission changes.

**This is a teaching comparison.** The baseline is a **basic FAQ draft** with working policy retrieval and valid JSON. Its short, general summaries intentionally leave room for better case-specific calculations and clarification. After optimizing instructions, compare **Relevance and TaskAdherence separately**. Do not change questions, reference answers, models, or evaluation criteria to raise scores. This demonstration is not evidence of production performance or improvement on unseen questions.

The pictures come from existing portal recordings and captures. Some are cropped to make the current control easier to read, with private fields redacted. Product scores, answers, and statuses are unchanged. Historical scores are not your results or guaranteed targets.

**How to proceed:** Follow 01 through 10 from top to bottom: **perform the numbered actions → check the screen directly below → continue to the next number**. Use **View full-size image** to read small text. Both guide languages use the **same Korean policies, questions, Agent instructions, and recorded responses**. Only the guide language changes; no separate English-language evaluation was run or is claimed. Paste the supplied Korean content unchanged rather than mixing in the original v1 English dataset.

## 01. Prepare your account and lab files {#portal-setup}

**You need:** an organizational account, an approved Azure subscription, permission to create resources, deploy models, and run Agents/evaluations/Optimize, plus model quota and spending approval. If access or quota is missing, ask your administrator before continuing. Never share passwords, keys, or tokens for this lab.

1. Open [Azure Portal](https://portal.azure.com/) and [Foundry Portal](https://ai.azure.com/) in separate browser tabs.
2. Sign in to **both portals with the same organizational account**. If you have several accounts, use the one with access to the Azure subscription you selected.
3. Save the following two files to your computer. In the web guide, right-click each link and choose **Save link as**. On GitHub, use **Download raw file** on the file page. Keep the original file extensions.

| File to save | Where it is used | Contents |
|---|---|---|
| [documents.v1.1.json](../../data/knowledge/documents.v1.1.json) | 05 · File search upload | Eight synthetic policies |
| [dev.v1.1.jsonl](../../data/optimizer/dev.v1.1.jsonl) | 06 · Evaluation dataset upload | Twelve questions and evaluation references |

Do not edit the files or remove selected questions. These versioned files preserve the original Korean policies and evaluation cases.

**Naming:** Include `v1.1` in each new name you choose. Where periods are not allowed, use `v1-1`. The dates below are examples; substitute your date or a short identifier if needed. Automatically assigned run IDs, numeric versions, and internal managed-object names are not names you enter.

**Done when:** You are signed in to both portals and have both files locally. Closing the browser does not stop Azure charges.
{: .completion-check}

## 02. Create a new resource group in Azure Portal {#portal-resource-group}

**Where to act:** Azure Portal → top search → **Resource groups**.
{: .step-route}

1. Select **Create**.
2. Under **Basics**, enter the following values.

| Field | Enter or select |
|---|---|
| Subscription | Your approved subscription |
| Resource group name | `rg-foundry-eval-v1.1-20261104` |
| Region | **(US) North Central US** |

<figure class="portal-shot" id="shot-resource-group-v1-1">
  <img src="../../web/assets/portal/v1.1/01-resource-group-basics.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Basics fields for creating a new resource group">
  <figcaption><strong>Check the subscription, new group name, and region.</strong> This creates a new group rather than selecting an existing one. <a href="../../web/assets/portal/v1.1/01-resource-group-basics.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

3. Open **Tags** and locate the **Name** and **Value** fields.
   {: value="3"}

<figure class="portal-shot" id="shot-resource-group-tags-v1-1">
  <img src="../../web/assets/portal/v1.1/29-resource-group-tags.v1.1.png" width="830" height="310" loading="lazy" decoding="async" alt="Empty Name and Value fields on the Tags tab">
  <figcaption><strong>Enter the name on the left and value on the right.</strong> This capture is before entry; fill both fields in the next numbered action. <a href="../../web/assets/portal/v1.1/29-resource-group-tags.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

4. Enter `lab-version` as **Name** and `v1.1` as **Value**, then select **Review + create**.
   {: value="4"}

<figure class="portal-shot" id="shot-resource-group-review-v1-1">
  <img src="../../web/assets/portal/v1.1/30-resource-group-review.v1.1.png" width="920" height="650" loading="lazy" decoding="async" alt="Pre-creation review showing the new group name, North Central US, and lab-version v1.1">
  <figcaption><strong>Check the group name, region, and tag before submission.</strong> The name must match your entry. This is review, not completed creation. <a href="../../web/assets/portal/v1.1/30-resource-group-review.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

5. Check the values and validation result, then select **Create** at the bottom once.
   {: value="5"}
6. Open the new group. Under **Overview**, verify its name and that it has no lab resources yet.

<figure class="portal-shot" id="shot-empty-group-v1-1">
  <img src="../../web/assets/portal/v1.1/02-empty-resource-group.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="New resource group showing zero resources and No deployments">
  <figcaption><strong>Check zero resources, No deployments, and the v1.1 tag.</strong> Foundry has not been created yet. Also check that the resource filters include everything. <a href="../../web/assets/portal/v1.1/02-empty-resource-group.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Do not reuse an existing lab group. If the name already exists, append `-02` and select that group in every later step.

**Done when:** Azure Portal shows the **new empty resource group**.
{: .completion-check}

## 03. Create the Foundry resource and project {#portal-project}

**Where to act:** Foundry Portal → **Create new → Create a project**. Use the classic screen only for this creation step, then switch to New Foundry.
{: .step-route}

1. If **New Foundry** is on, turn it off.
2. From the home page, open the project creation screen through **Create new**.
3. For **Project**, enter `proj-foundry-eval-v1-1`.
4. Expand **Advanced options** and check the values below. Do not accept an automatically selected different subscription or resource group.

| Field | Enter or select |
|---|---|
| Microsoft Foundry resource | `ai-foundry-eval-v1-1-20261104` |
| Subscription | The subscription selected in 02 |
| Resource group | **The new group created in 02** |
| Region | **North Central US** |

<figure class="portal-shot" id="shot-project-create-v1-1">
  <img src="../../web/assets/portal/v1.1/05-foundry-project-create.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Foundry project creation with the new resource group selected in Advanced options">
  <figcaption><strong>Check the resource group under Advanced options.</strong> Use the group, subscription, and region from 02. <a href="../../web/assets/portal/v1.1/05-foundry-project-create.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

5. Select **Create** once and wait for the project home page. If the Foundry resource name is taken, append a short identifier.
   {: value="5"}
6. Turn on **New Foundry**. If prompted to choose an account, select the same account used in Azure Portal.
7. Verify that the top project selector shows `proj-foundry-eval-v1-1`.

<figure class="portal-shot" id="shot-project-home-v1-1">
  <img src="../../web/assets/portal/v1.1/06-project-home.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="New Foundry project home with Agents, Models, and Evaluations in the left navigation">
  <figcaption><strong>Check the top project selector and New Foundry switch.</strong> Agents, Models, and Evaluations are in the left navigation. Do not deploy extra models suggested on the home page. <a href="../../web/assets/portal/v1.1/06-project-home.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

8. Switch to the **Azure Portal tab**, open the new group, and select **Refresh**. Verify the **Foundry resource and Foundry project**.
   {: value="8"}

<figure class="portal-shot" id="shot-created-resources-v1-1">
  <img src="../../web/assets/portal/v1.1/15-created-resources.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Dedicated resource group containing a Foundry resource and a Foundry project">
  <figcaption><strong>Look for Foundry and Foundry project in the Type column.</strong> These are two different resources despite their similar names. This verifies creation in the same environment; it is not an instruction to create more resources. <a href="../../web/assets/portal/v1.1/15-created-resources.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**If creation fails:** Successful input validation is not successful deployment. Check the group's **Overview and Deployments**. If an object already exists, inspect it before creating duplicates. This guide uses the Foundry Portal route above instead of Azure Portal's Foundry creation dialog.

**Done when:** The new group contains both resources and New Foundry opens the new project home page.
{: .completion-check}

## 04. Deploy models for three roles {#portal-models}

**Where to act:** **Foundry Portal tab** → New Foundry → **Catalog → Models**.
{: .step-route}

Use **different deployment names**, even when two roles use the same model. The Agent answers, the Judge evaluates, and the Optimizer generates improved instructions.

| Role | Model / model version | Deployment name | Capacity |
|---|---|---|---|
| Agent | **gpt-5.5 / 2026-04-24** | `agent-v1-1` | 150K TPM |
| Judge | **gpt-6-luna / 2026-09-22** | `judge-v1-1` | 100K TPM |
| Optimizer | **gpt-5.5 / 2026-04-24** | `optimizer-v1-1` | 150K TPM |

1. On the **Models** tab, search for `gpt-5.5` and open it.
2. Select **Deploy → Custom settings**.
3. Enter the first row's **Deployment name**. Select **Global Standard** and the model version shown in the table.
4. Open **Model version settings → Model version upgrade policy** and select **Opt out of automatic model version upgrades**.

<figure class="portal-shot" id="shot-model-deploy-v1-1">
  <img src="../../web/assets/portal/v1.1/07-agent-model-deploy.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Agent deployment name, pinned model version, and automatic upgrades disabled">
  <figcaption><strong>Check the deployment name, pinned version, and upgrade opt-out.</strong> Agent and Optimizer deployment names differ even when their models match. <a href="../../web/assets/portal/v1.1/07-agent-model-deploy.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

5. Check Capacity and select **Deploy**.
   {: value="5"}
6. In **Catalog → Models**, open `gpt-6-luna` and select **Deploy → Custom settings**. Set name `judge-v1-1`, **Global Standard**, version **2026-09-22**, automatic upgrades **Opt out**, and Capacity **100000 TPM**.

<figure class="portal-shot" id="shot-judge-model-settings-v1-1" data-capture-layout="dialog">
  <img src="../../web/assets/portal/v1.1/31-judge-model-settings.v1.1.png" width="592" height="1000" loading="lazy" decoding="async" alt="Judge deployment panel with judge-v1-1, gpt-6-luna, a pinned version, and 100000 TPM">
  <figcaption><strong>Use a separate model and name for the Judge.</strong> Only the deployment panel is shown. The numeric field's 100000 is this deployment's TPM, not the maximum quota shown to its right. <a href="../../web/assets/portal/v1.1/31-judge-model-settings.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

7. Select **Deploy** for the Judge. Then open `gpt-5.5` in Catalog and choose **Deploy → Custom settings**. Set name `optimizer-v1-1`, **Global Standard**, version **2026-04-24**, automatic upgrades **Opt out**, and Capacity **150000 TPM**.
   {: value="7"}

<figure class="portal-shot" id="shot-optimizer-model-settings-v1-1" data-capture-layout="dialog">
  <img src="../../web/assets/portal/v1.1/32-optimizer-model-settings.v1.1.png" width="592" height="1000" loading="lazy" decoding="async" alt="Optimizer deployment panel with optimizer-v1-1, gpt-5.5, a pinned version, and 150000 TPM">
  <figcaption><strong>The model matches the Agent, but the name is optimizer-v1-1.</strong> Create the Optimizer deployment rather than reusing the Agent deployment. <a href="../../web/assets/portal/v1.1/32-optimizer-model-settings.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

8. Select **Deploy** for the Optimizer. Open **Models** in the left navigation, compare all three names, models, and versions, and wait until all show **Succeeded**.
   {: value="8"}

<figure class="portal-shot" id="shot-models-succeeded-v1-1">
  <img src="../../web/assets/portal/v1.1/08-models-succeeded.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="agent-v1-1, judge-v1-1, and optimizer-v1-1 deployments showing Succeeded">
  <figcaption><strong>Match the three named deployments, models, versions, and Succeeded states.</strong> This same-environment capture was taken after File search preparation, so it also shows an automatically created text-embedding-ada-002 deployment. It does not tell you to deploy a fourth model manually. <a href="../../web/assets/portal/v1.1/08-models-succeeded.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Support requirements:** This path uses `gpt-5.5` with File search. Do not substitute v1's `gpt-6-sol`. If deployment, File search, or quota is unavailable, stop and resolve the support or quota issue. Do not switch models or versions during comparison. Global Standard is a global deployment type; do not upload real customer data with regional restrictions.

Managed features such as File search can create internal datasets or embedding deployments automatically. Distinguish them from your three deployments. Do not delete an unidentified managed object just to tidy its name.

**Done when:** All three role deployments show Succeeded and automatic model-version upgrades are disabled.
{: .completion-check}

## 05. Connect instructions and File search to the Agent {#portal-agent}

**Where to act:** **Agents → New agent → Build an agent**.
{: .step-route}

1. Enter `atlas-support-v1-1` as the **Agent name** and select **Text**. Leave the Microsoft Copilot harness unselected.

<figure class="portal-shot" id="shot-create-agent-v1-1">
  <img src="../../web/assets/portal/v1.1/09-create-agent.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Agent name, Text mode, and an unselected Microsoft Copilot harness option">
  <figcaption><strong>Check the name, Text, and unselected harness.</strong> Then use the creation button below. <a href="../../web/assets/portal/v1.1/09-create-agent.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

2. Select **Create agent and open playground**.
   {: value="2"}
3. Under **Model**, select **gpt-5.5 / agent-v1-1**. Do not leave an automatically selected different model.
4. Paste the complete **instruction v1 (baseline)** below into **Instructions**. The [same instruction file](../../prompts/baseline.v1.1.txt) is also available. This is portal input, not a command. It asks for a Korean, one-sentence JSON FAQ summary within 80 characters, without case-specific calculations or follow-up questions. Paste the Korean block unchanged to reproduce the recorded workload.

```text
Contoso Atlas Cloud의 고객지원 도우미입니다. 한국어로 친절하게 답합니다.
정책 질문은 연결한 File search에서 근거를 찾아 답합니다.
answer는 한 문장, 80자 이내로 작성하고 찾은 정책의 일반 규칙만 짧게 요약합니다.
날짜·기한·금액·비율의 개별 계산이나 여러 조건을 함께 비교하는 판단은 하지 않습니다.
조건이 모호하거나 부족해도 추가 확인 질문을 하지 않고 안내 가능한 일반 정책을 설명합니다.
응답은 다음 네 필드만 가진 JSON 객체 하나로 작성합니다. 마크다운은 쓰지 않습니다.
{"answer":"답변","citations":["실제로 사용한 정책 문서 ID"],"route":"answer","needs_human":false}
route는 answer, clarify, escalate, refuse 중 하나입니다. needs_human은 route가 escalate일 때만 true입니다.
이 도우미는 안내만 합니다. 실제 접수, 승인, 환불, 데이터 삭제, 권한 변경을 수행했다고 주장하지 않습니다.
권한 없는 타인 데이터 접근이나 인증 우회 요청은 거절하고, 비밀번호·키·토큰 등 비밀정보를 요청하지 않습니다.
구체적인 평가 문항, 날짜, 정답 예시를 지침에 저장하지 않습니다.
```

<figure class="portal-shot" id="shot-baseline-instructions-v1-1" data-capture-layout="dialog">
  <img src="../../web/assets/portal/v1.1/33-baseline-instructions.v1.1.png" width="460" height="195" loading="lazy" decoding="async" alt="Beginning of the baseline instructions in the Playground Instructions field">
  <figcaption><strong>Paste the entire block above into Instructions.</strong> This focused view shows the input location and only part of its content. Do not copy a few sentences from the image. Do not select Improve instructions. <a href="../../web/assets/portal/v1.1/33-baseline-instructions.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

5. If **Tools** includes a default **Web search** tool, use that tool's menu → **Remove**. Keep the uploaded policies as the fixed source.
   {: value="5"}
6. Select **Tools → Add → Add tools** to open **Select a tool**.

<figure class="portal-shot" id="shot-select-file-search-v1-1">
  <img src="../../web/assets/portal/v1.1/34-select-file-search.v1.1.png" width="1200" height="800" loading="lazy" decoding="async" alt="File search at the top left of Select a tool and Add tool at the bottom right">
  <figcaption><strong>Select File search at the top left.</strong> Do not choose Azure AI search or Web search. Selecting a tool enables Add tool at the bottom right. <a href="../../web/assets/portal/v1.1/34-select-file-search.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

7. Select **File search → Add tool**. Under **Attach files**, set **Index option** to **Create a new index** and **Vector index name** to `atlas-policy-v1-1`.
   {: value="7"}

<figure class="portal-shot" id="shot-create-vector-index-v1-1" data-capture-layout="dialog">
  <img src="../../web/assets/portal/v1.1/35-create-vector-index.v1.1.png" width="690" height="253" loading="lazy" decoding="async" alt="Attach files with Create a new index, atlas-policy-v1-1, and browse for files">
  <figcaption><strong>Name the new index, then use browse for files.</strong> The crop shows only entry and file-selection controls, not a completed upload or connection. <a href="../../web/assets/portal/v1.1/35-create-vector-index.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

8. Under **browse for files**, select **only** `documents.v1.1.json`. When upload status is **Success**, select **Attach**.
   {: value="8"}
9. Verify that **File search** is connected under Tools and select **Save**.
10. Open the **Tools → File search** card. Confirm that `atlas-policy-v1-1` contains one **Completed** policy file.

<figure class="portal-shot" id="shot-policy-upload-v1-1">
  <img src="../../web/assets/portal/v1.1/10-policy-upload.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="One policy file connected to the File search index with Completed status">
  <figcaption><strong>Check one file and Completed.</strong> This is your saved File search connection. Do not upload or Attach the file again. <a href="../../web/assets/portal/v1.1/10-policy-upload.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

11. Close the verification dialog with **Cancel**. Record the top **Version** number as your **baseline version**. It depends on prior saves and does not have to be 1.
   {: value="11"}
12. Send **“Standard 요금제에서 조직 SSO를 사용할 수 있나요?”** in the chat. It means “Can the Standard plan use organizational SSO?”
13. Expand the response's tool indicator and verify a **File search call**, model `agent-v1-1`, and a JSON response. SSO is available only in Pro, with source ID `ATLAS-FEAT-001`.

<figure class="portal-shot" id="shot-agent-retrieval-v1-1">
  <img src="../../web/assets/portal/v1.1/11-agent-retrieval.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Baseline v6 using File search and returning valid JSON citing ATLAS-FEAT-001">
  <figcaption><strong>Check the model, File search, and JSON evidence together.</strong> The Korean response says Standard lacks organizational SSO and Pro provides it, citing ATLAS-FEAT-001. Version 6 is this recording's baseline, not a number you must reproduce. <a href="../../web/assets/portal/v1.1/11-agent-retrieval.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Avoid confusion:** **Knowledge → Add** is the Foundry IQ connection route. This v1.1 path uses **File search under Tools**; do not create a separate Search resource or Foundry IQ configuration. If File search is disabled, first check the Agent's actual selected model.

The starting Agent does not fail every question. Keep basic retrieval and JSON working while improving **application of general rules to individual cases and requests for missing information**. Later, change only instructions, not policies, tools, or models. Lab edition **v1.1** and the portal's numeric **Agent Version** are different concepts.

**Done when:** A baseline version is saved with one policy file, and the basic question produces a File search call and valid JSON.
{: .completion-check}

## 06. Run the baseline evaluation on twelve cases {#portal-evaluation}

**Where to act:** Agent → **Evaluation → Automatic Evaluation**. Continue through one evaluation creation wizard.
{: .step-route}

1. Open the Agent's **Evaluation → Automatic Evaluation** tab. Locate **Create** on the right.

<figure class="portal-shot" id="shot-open-automatic-evaluation-v1-1">
  <img src="../../web/assets/portal/v1.1/36-open-automatic-evaluation.v1.1.png" width="1174" height="209" loading="lazy" decoding="async" alt="Agent Evaluation and Automatic Evaluation tabs with Create on the right">
  <figcaption><strong>Start with Create under Automatic Evaluation.</strong> Do not choose the Create evaluator banner button or Human Evaluation. <a href="../../web/assets/portal/v1.1/36-open-automatic-evaluation.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

2. Select **Create**. Under **Target**, choose `atlas-support-v1-1` and use **Version → Pin v[number]** for the **baseline version** recorded in 05. Select **Next**, then **Scope: Individual turns**.
   {: value="2"}

<figure class="portal-shot" id="shot-individual-turns-v1-1">
  <img src="../../web/assets/portal/v1.1/37-individual-turns.v1.1.png" width="1184" height="499" loading="lazy" decoding="async" alt="Individual turns selected in the evaluation Scope step with Next">
  <figcaption><strong>Evaluate each question-response pair independently.</strong> Select Individual turns, not Full conversations. <a href="../../web/assets/portal/v1.1/37-individual-turns.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

3. Continue with **Next → Frequency: One time → Next**. Open **Data → Existing dataset → Upload new dataset**. Enter `atlas-dev12-v1-1` as **New dataset name**, use **Choose file** for `dev.v1.1.jsonl`, and select **Upload**.
   {: value="3"}

<figure class="portal-shot" id="shot-upload-evaluation-dataset-v1-1" data-capture-layout="dialog">
  <img src="../../web/assets/portal/v1.1/38-upload-evaluation-dataset.v1.1.png" width="520" height="394" loading="lazy" decoding="async" alt="Upload new dataset with atlas-dev12-v1-1 and dev.v1.1.jsonl while upload is processing">
  <figcaption><strong>Match the dataset name and selected file.</strong> Upload is still processing in this capture. Do not submit again; wait for the dataset to appear in the list. <a href="../../web/assets/portal/v1.1/38-upload-evaluation-dataset.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

4. Select `atlas-dev12-v1-1`, version `1`, in the list. Verify the preview's `query`, `context`, and `ground_truth` columns. `ground_truth` is reference material stored as a JSON string. **Top 5 rows is a preview limit**, not the dataset's size. Verify all **12 rows** after execution in 07.
   {: value="4"}

<figure class="portal-shot" id="shot-evaluation-dataset-preview-v1-1">
  <img src="../../web/assets/portal/v1.1/39-evaluation-dataset-preview.v1.1.png" width="1184" height="859" loading="lazy" decoding="async" alt="Selected existing dataset atlas-dev12-v1-1 version 1 and preview columns context, ground_truth, and query">
  <figcaption><strong>Check the selected name, version, and preview columns.</strong> Do not upload again. Displaying three columns does not mean all three belong in the Agent input. <a href="../../web/assets/portal/v1.1/39-evaluation-dataset-preview.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

5. Open **Next → Configure agents → Configure**. Put **only this value** in the **USER** field.
   {: value="5"}

```text
{{item.query}}
```

<figure class="portal-shot" id="shot-query-only-v1-1">
  <img src="../../web/assets/portal/v1.1/12-query-only-mapping.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Evaluation USER input mapped only to item.query">
  <figcaption><strong>USER receives only the question.</strong> Match the field to the value above before saving. Do not add a reference answer or context. <a href="../../web/assets/portal/v1.1/12-query-only-mapping.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

Do not append `context` or `ground_truth` to this field. The Agent must retrieve policies through File search rather than read the answer in advance. Inspect **Configure agents** explicitly even if mapping appears to have been skipped automatically.

6. Select **Save** to close the mapping dialog, then **Next** to **Criteria**. Set **Judge model** to **judge-v1-1**. Use **Clear selection**, then select only **Relevance** and **Task adherence**.
   {: value="6"}
7. Open **Relevance** first. Match its column below: Judge **judge-v1-1**, Threshold **4**, and the input mappings.

| Setting | Relevance | Task adherence |
|---|---|---|
| Result metric name | Relevance | TaskAdherence |
| Judge deployment | `judge-v1-1` | `judge-v1-1` |
| Threshold | **4** | **1** |
| Probability_threshold | Not applicable | **0.5** |
| Query | `{{item.query}}` | `{{item.query}}` |
| Response | `{{sample.output_text}}` | `{{sample.output_text}}` |
| Tool definitions | Not applicable | Keep default `{{sample.tool_definitions}}` |

<figure class="portal-shot" id="shot-relevance-settings-v1-1">
  <img src="../../web/assets/portal/v1.1/40-relevance-settings.v1.1.png" width="1038" height="447" loading="lazy" decoding="async" alt="Relevance settings with Judge judge-v1-1 and Threshold 4">
  <figcaption><strong>Relevance uses Threshold 4.</strong> Check Query and Response under Advanced settings against the table too. Apply with Update in the next action. <a href="../../web/assets/portal/v1.1/40-relevance-settings.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

8. Select **Update** for Relevance, then open **Task adherence**. Check Judge **judge-v1-1**, Threshold **1**, Probability_threshold **0.5**, and the table's input mappings.
   {: value="8"}

**TaskAdherence warning:** This is a binary 0/1 metric. If the shared Threshold field defaults to 3, change it to **1**. Check **0.5** in the Probability_threshold numeric field.

<figure class="portal-shot" id="shot-task-adherence-v1-1">
  <img src="../../web/assets/portal/v1.1/13-task-adherence-settings.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Task-Adherence settings with judge-v1-1, Threshold 1, and Probability_threshold 0.5">
  <figcaption><strong>Check the Judge, 1, and 0.5 separately.</strong> These are two different thresholds. Match Query and Response under Advanced settings to the table, then confirm with Update or Apply. <a href="../../web/assets/portal/v1.1/13-task-adherence-settings.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

9. Apply with **Update / Apply**, then select the **Criteria** step's **Next** button, not the evaluator catalog's next-page control.
   {: value="9"}
10. Under **Review**, enter `atlas-portal-eval-v1-1` and recheck the Agent version, dataset, and two evaluators.

<figure class="portal-shot" id="shot-baseline-review-v1-1">
  <img src="../../web/assets/portal/v1.1/14-baseline-review.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Review showing the baseline Agent version, dataset, and two evaluators">
  <figcaption><strong>Check the baseline version, data, and two evaluators.</strong> Review summarizes settings before submission; it is not a successful evaluation or a score screen. <a href="../../web/assets/portal/v1.1/14-baseline-review.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

11. Select **Submit** once and wait for the run to finish. Do not create the same evaluation again.
    {: value="11"}

**Done when:** An evaluation definition and actual run exist, and you can inspect per-case responses, scores, or errors. Successful submission does not mean all twelve cases succeeded.
{: .completion-check}

## 07. Read responses and errors before scores {#portal-analysis}

**Where to act:** **Evaluations → atlas-portal-eval-v1-1**.
{: .step-route}

1. In the run list, check the baseline version under **Target**, **Status**, and the pass counts and denominators for Relevance and TaskAdherence.

<figure class="portal-shot" id="shot-baseline-results-v1-1">
  <img src="../../web/assets/portal/v1.1/16-baseline-results.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Baseline Agent v6 showing Partial, Relevance 7/11, and TaskAdherence 8/11">
  <figcaption><strong>Read Partial and each metric's denominator first.</strong> This baseline has Relevance 7/11 (64%) and TaskAdherence 8/11 (73%). Overall 68%, or 15/22, combines judgments from two metrics; it does not mean 22 questions. Your results may differ. <a href="../../web/assets/portal/v1.1/16-baseline-results.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

2. Open that run and select **Detailed metrics**. Inspect the first page's **Index 0–9**, scores, and errors.
   {: value="2"}

<figure class="portal-shot" id="shot-baseline-detailed-metrics-v1-1">
  <img src="../../web/assets/portal/v1.1/41-baseline-detailed-metrics.v1.1.png" width="1174" height="752" loading="lazy" decoding="async" alt="Baseline Detailed metrics Index 0 through 9 with Relevance failures and Index 9 Error">
  <figcaption><strong>Read individual cases, not just averages.</strong> This first page has ten rows and Next at the bottom right. Only conversation/trace identifier cells are masked; questions, scores, and Error are unchanged. <a href="../../web/assets/portal/v1.1/41-baseline-detailed-metrics.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

3. Inspect **Error** first when that column exists. A page without errors may omit it. Distinguish response-generation failures from Judge-scoring failures.
   {: value="3"}
4. For a low-**Relevance** row, scroll horizontally to `sample.output_text` and open **View JSON**. Read the question, actual response, **Relevance.reason**, **TaskAdherence**, and its reason, then close the dialog. Following instructions and providing a sufficient business answer are different criteria.
5. Use **Next** at the table's bottom right. Inspect **Index 10 and 11** too, covering scores and errors for all **12 submitted rows**.

<figure class="portal-shot" id="shot-baseline-final-cases-v1-1">
  <img src="../../web/assets/portal/v1.1/42-baseline-final-cases.v1.1.png" width="1174" height="400" loading="lazy" decoding="async" alt="Detailed metrics next page with Index 10 and 11 and Relevance scores 2 and 3">
  <figcaption><strong>The final two rows belong to the same evaluation.</strong> This baseline scores 2 and 3 on Relevance at Index 10 and 11. Both pages cover twelve submitted cases, but one error leaves eleven scored cases. <a href="../../web/assets/portal/v1.1/42-baseline-final-cases.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

6. Privately record the baseline version, evaluation definition, dataset version, evaluator settings, and error cases.
   {: value="6"}

| Question to ask | What to inspect |
|---|---|
| Did it summarize general rules but miss the question's conditions? | Look for missing calculations, condition comparisons, or necessary clarification. |
| Did it apply policy deadlines or amounts to this case? | Check whether it ended with only “contact support.” |
| Did it ask for essential missing information? | Examples include plan, monthly/annual billing, or the relevant month. |
| Did it mark undocumented features as unconfirmed? | Do not replace uncertainty with a false promise to improve a score. |
| Did it claim to complete an approval, submission, or deletion? | An advisory Agent must not claim actions it cannot perform. |
| Does the scoring reason match the displayed answer? | If not, inspect the full conversation and tool history before deciding. |

**Partial / provider blocking:** A run detail may show **Completed** while the definition list shows **Partial**. Record successful cases and errors together. A pass rate over eleven scored cases is not a pass rate over all twelve. Distinguish provider blocks such as `cyber_policy` from an Agent refusal or ordinary wrong answer. Do not disable safeguards or rewrite questions to bypass a block.

**Done when:** You have read an actual low-scoring response and its reasons, and separated instruction improvements from service errors. If errors remain, **withhold an overall improvement conclusion**.
{: .completion-check}

## 08. Optimize instructions only {#portal-optimize}

**Where to act:** **Agents → atlas-support-v1-1 → baseline version → Playground → Optimize at the bottom left**.
{: .step-route}

The benchmark examples on the introduction screen are not your lab results.

1. Open **Optimize** at the bottom left of the **Playground**.

<figure class="portal-shot" id="shot-optimize-agent-menu-v1-1" data-capture-layout="dialog">
  <img src="../../web/assets/portal/v1.1/43-optimize-agent-menu.v1.1.png" width="306" height="265" loading="lazy" decoding="async" alt="Optimize menu with Agent, Cost, and Prompt options">
  <figcaption><strong>Continue with Agent at the top.</strong> This is not Cost, Prompt, or Improve instructions beneath the Instructions field. <a href="../../web/assets/portal/v1.1/43-optimize-agent-menu.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

2. Select **Agent**. If an introduction appears, continue with **Optimize my agent**. Under **Target**, check the baseline version, then select **Optimization approach → Choose targets** and set the values below.
   {: value="2"}

| Field | Setting |
|---|---|
| Instruction | **Selected** |
| Tool description | **Unselected** |
| Model / Compare across models | **Unselected / off** |
| Optimization model | **optimizer-v1-1** |
| Max candidates | **1** |
| Evaluation model | **judge-v1-1** |

<figure class="portal-shot" id="shot-optimizer-settings-v1-1">
  <img src="../../web/assets/portal/v1.1/17-optimizer-settings.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Instruction-only optimization with optimizer-v1-1, judge-v1-1, and one candidate">
  <figcaption><strong>Change only Instruction; keep models and tools fixed.</strong> Match the generation model, evaluation model, and Max candidates 1 to the table. <a href="../../web/assets/portal/v1.1/17-optimizer-settings.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

3. Select **Next → Data source → Select dataset and criteria**. Do not use Generate data or production traces.
   {: value="3"}
4. Search the right-hand **Dataset** field for `atlas-dev12-v1-1`. Check the result's name and version `1`.

<figure class="portal-shot" id="shot-optimizer-dataset-search-v1-1">
  <img src="../../web/assets/portal/v1.1/44-optimizer-dataset-search.v1.1.png" width="1148" height="338" loading="lazy" decoding="async" alt="Select dataset and criteria with atlas-dev12-v1-1 version 1 and an unselected row radio button">
  <figcaption><strong>Find the same dataset used for the baseline.</strong> The row is not selected yet, so Next is disabled. Select its radio button in the next action. Do not upload a new file or use generated data. <a href="../../web/assets/portal/v1.1/44-optimizer-dataset-search.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

5. Select the dataset row's **radio button → Next**. Under **Criteria**, turn off **Custom only** if enabled. Search for the two evaluators below. If a settings dialog opens, check its values and select **Apply**.
   {: value="5"}

| Optimizer evaluator | Version | Settings |
|---|---|---|
| Relevance-Evaluator | 15 | Threshold **4** |
| Task-Adherence-Evaluator-(Preview) | 18 | Threshold **1**, Probability_threshold **0.5** |

<figure class="portal-shot" id="shot-optimizer-evaluator-selection-v1-1">
  <img src="../../web/assets/portal/v1.1/45-optimizer-evaluator-selection.v1.1.png" width="1148" height="287" loading="lazy" decoding="async" alt="Optimizer Criteria with Custom only off and selected Task-Adherence and Relevance chips">
  <figcaption><strong>Verify both selections in the chips above the list.</strong> Both remain selected even while the search shows only Relevance. Do not add other evaluators. <a href="../../web/assets/portal/v1.1/45-optimizer-evaluator-selection.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

6. Verify that no other evaluators were added and select **Next**.
   {: value="6"}
7. Under **Review**, verify **Optimization targets: Instruction**, the same dataset and Judge, and **one candidate**. Read **Estimated cost** too; it is not an actual bill or guaranteed spending cap.

<figure class="portal-shot" id="shot-optimizer-review-v1-1">
  <img src="../../web/assets/portal/v1.1/18-optimizer-review.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Optimizer Review summarizing Instruction, the same dataset, Judge, and candidate count">
  <figcaption><strong>Recheck the change scope before Submit.</strong> This capture still says Estimating cost. Read your estimate when available and confirm it is authorized. If no estimate is provided, do not submit without an approved cost basis. <a href="../../web/assets/portal/v1.1/18-optimizer-review.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

8. Select **Submit** once. Open the automatically assigned **Run ID** in the run list. There is no separate run-name field; keep the ID privately.
   {: value="8"}
9. Under **Additional settings**, verify the instruction target, models, and candidate count, then wait for completion.
10. Under **Candidate results**, compare baseline and candidate scores and read score details.

<figure class="portal-shot" id="shot-optimizer-results-v1-1">
  <img src="../../web/assets/portal/v1.1/19-optimizer-results.v1.1.png" width="1172" height="362" loading="lazy" decoding="async" alt="Original Optimizer candidate result cards showing Task-weighted average increasing from 0.625 to 0.781">
  <figcaption><strong>Verify the original Optimizer candidate's actual 0.625 → 0.781.</strong> This separate run used one candidate and took 6m 23s. It is not the Relevance or TaskAdherence pass rate of the manually reviewed v2 in 09. The image is cropped to result cards to exclude run identifiers; product scores are unchanged. <a href="../../web/assets/portal/v1.1/19-optimizer-results.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Review candidates:** Do not adopt a higher-scoring instruction that memorizes policy numbers or reference answers, promises unconfirmed features, or claims actions that were never performed. Permission bypass and requests for secrets remain prohibited. Accept only **general instruction improvements**, such as answer structure, evidence use, and necessary clarification.

11. Open the candidate's **Changes / View changes**. Compare baseline and original candidate instructions against the review criteria above.
   {: value="11"}

<figure class="portal-shot" id="shot-review-candidate-v1-1">
  <img src="../../web/assets/portal/v1.1/20-review-candidate.v1.1.png" width="1038" height="622" loading="lazy" decoding="async" alt="Instruction changes comparing the baseline with the original Optimizer candidate">
  <figcaption><strong>The Changes dialog shows the original candidate, not final v2.</strong> The Korean text on the right still includes policy examples and restrictions on calculations and follow-up questions. Green highlighting or a higher score is not a reason to Promote. Do not copy instructions from this picture; distinguish it from the reviewed file in 09. The image is cropped to the change dialog for privacy. <a href="../../web/assets/portal/v1.1/20-review-candidate.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

12. Close the change dialog with **Close**. Do not select **Promote candidate**. In the next step, save the reviewed correction as a new version.
   {: value="12"}

The Optimizer's **Task-weighted average (0–1)** is not an individual evaluator pass rate. Higher scores on the same twelve optimization cases do not establish generalization or production quality.

**Done when:** You have read the actual candidate instructions and scoring reasons and decided whether a candidate is worth retaining. Preserve errors if the job fails. Do not rerun identical settings until a favorable score appears.
{: .completion-check}

## 09. Save the reviewed instructions as a new version and compare {#portal-compare}

**Where to act:** Agent → **Playground → Instructions → Save**, then the existing evaluation definition → **Add run / Compare runs**.
{: .step-route}

An Optimizer candidate can embed dates or reference answers from evaluation cases. Do not promote such an original unchanged, even if its score rises. This path uses **[instruction v2 · reviewed.v1.1.txt](../../prompts/reviewed.v1.1.txt)**, which generalizes response, retrieval, and routing improvements. It is a **human-authored, reviewed correction, not the original Optimizer output**. A human also removed the original's character-limit, calculation, and clarification restrictions. The reviewed instructions allow grounded calculations and specific questions for essential missing information while preserving JSON, evidence, and safety boundaries. Do not attribute the original candidate's scores to this file or describe the improvement as the Optimizer's effect alone.

| Comparison condition | Keep fixed |
|---|---|
| Questions and references | `atlas-dev12-v1-1`, same version, all twelve cases |
| Agent input | Only `{{item.query}}` |
| Agent model, policies, and tools | `agent-v1-1`, the same File search and policy file |
| Judge and evaluators | `judge-v1-1`, Relevance 4, TaskAdherence 1 / 0.5 |
| Only intentional change | Reviewed Agent instructions |

1. In the Agent **Playground → Version**, open your recorded **baseline version**. Check the original FAQ instructions, model, and File search.

<figure class="portal-shot" id="shot-baseline-preserved-v1-1">
  <img src="../../web/assets/portal/v1.1/25-baseline-preserved.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Baseline v6 with its original FAQ instructions, model, and File search">
  <figcaption><strong>Check the baseline before editing.</strong> The recording uses v6. The next Save creates a new version while preserving these original instructions and existing evaluation results. <a href="../../web/assets/portal/v1.1/25-baseline-preserved.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

2. Replace **Instructions** with the complete linked instruction v2 file and select **Save**. Do not select **Publish**.
   {: value="2"}
3. Record the new Agent number as the **comparison version**. Verify that only instructions changed: model `agent-v1-1`, File search, and the policy file are unchanged.

<figure class="portal-shot" id="shot-reviewed-agent-v1-1">
  <img src="../../web/assets/portal/v1.1/21-reviewed-agent.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Reviewed Agent v7 retaining model agent-v1-1 and File search">
  <figcaption><strong>Only instructions changed in the new version.</strong> This run's comparison version is 7, with the same model and File search. This is a saved Agent, not a published production deployment. <a href="../../web/assets/portal/v1.1/21-reviewed-agent.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

4. Select **Evaluations → atlas-portal-eval-v1-1 → Add run**. Do not create another evaluation definition.
   {: value="4"}

<figure class="portal-shot" id="shot-add-run-target-version-v1-1">
  <img src="../../web/assets/portal/v1.1/46-add-run-target-version.v1.1.png" width="1184" height="264" loading="lazy" decoding="async" alt="Add run with atlas-support-v1-1 selected and Version still set to Latest available">
  <figcaption><strong>Pin the comparison version using the Version dropdown.</strong> This initial Add run screen still says Latest available. Do not submit that default unchanged. <a href="../../web/assets/portal/v1.1/46-add-run-target-version.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

5. Under **Target**, select the same Agent and use **Pin v[number]** for your recorded comparison version, not **Latest available**. Continue with **Next → Scope: Individual turns → Next**. Under **Data → Existing dataset**, select the same `atlas-dev12-v1-1`, version `1`.
   {: value="5"}

<figure class="portal-shot" id="shot-add-run-existing-dataset-v1-1">
  <img src="../../web/assets/portal/v1.1/47-add-run-existing-dataset.v1.1.png" width="1184" height="608" loading="lazy" decoding="async" alt="The existing atlas-dev12-v1-1 version 1 selected again for Add run">
  <figcaption><strong>Reselect the same registered version.</strong> Do not use Upload new dataset or Synthetic generation. Wait for the preview to load and Next to become enabled. <a href="../../web/assets/portal/v1.1/47-add-run-existing-dataset.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

6. Open **Next → Configure agents → Configure**. Enter only `{{item.query}}` as **User prompt** and verify that Target uses your comparison version.
   {: value="6"}

<figure class="portal-shot" id="shot-add-run-query-only-v1-1">
  <img src="../../web/assets/portal/v1.1/22-add-run-query-only.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Add run using v7 with only item.query in USER">
  <figcaption><strong>Reevaluation remains query-only.</strong> Check both v7 on the left Target card and the USER input. Reusing the definition does not remove the need to inspect input mapping. <a href="../../web/assets/portal/v1.1/22-add-run-query-only.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

7. Select **Save → Submit** and wait for completion. Reuse the definition's Judge and evaluators.
   {: value="7"}
8. Open the **comparison-version run** and its first **Detailed metrics** page. Compare responses, scores, reasons, and errors at the **same Index** with your baseline records from 07. Record latency, token usage, and means too.

<figure class="portal-shot" id="shot-reviewed-detailed-metrics-v1-1">
  <img src="../../web/assets/portal/v1.1/48-reviewed-detailed-metrics.v1.1.png" width="1174" height="752" loading="lazy" decoding="async" alt="Reviewed v7 first-page passing rows with Index 9 still showing Error">
  <figcaption><strong>Inspect both better valid responses and the remaining error.</strong> The 100% summaries cover eleven valid cases. Index 9 still has Error; only identifier cells were masked. <a href="../../web/assets/portal/v1.1/48-reviewed-detailed-metrics.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

9. Use **Next** to inspect the final two rows. After comparing all **12 rows**, open the definition's run list. Check **Target**, status, and both evaluator pass rates and denominators.
   {: value="9"}

<figure class="portal-shot" id="shot-evaluation-runs-v1-1">
  <img src="../../web/assets/portal/v1.1/23-evaluation-runs.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Two runs of the same evaluation comparing Agent v6 and v7 pass rates and Partial status">
  <figcaption><strong>Compare Target, Partial, and denominators in both rows.</strong> The rise from v6's 64% and 73% to v7's 100% and 100% is an observed pass-rate increase on eleven common valid cases, not success on all twelve submitted cases. <a href="../../web/assets/portal/v1.1/23-evaluation-runs.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

**Actual results in this recording · 2026-11-04**

| Metric | Instruction v1 · Agent v6 | Reviewed instruction v2 · Agent v7 |
|---|---|---|
| Relevance pass rate | **7/11 · 64%** | **11/11 · 100%** |
| TaskAdherence pass rate | **8/11 · 73%** | **11/11 · 100%** |
| Relevance mean | 3.64 | 4.91 |
| TaskAdherence mean | 0.73 | 1.00 |
| P50 / P95 response latency | 5.4s / 7.7s | 4.6s / 6.8s |

10. Select the **left-hand row checkbox** for both baseline and comparison. Verify **2 runs selected**.
    {: value="10"}

<figure class="portal-shot" id="shot-select-comparison-runs-v1-1">
  <img src="../../web/assets/portal/v1.1/49-select-comparison-runs.v1.1.png" width="2348" height="660" loading="lazy" decoding="async" alt="Selected Agent v6 and v7 row checkboxes and 2 runs selected">
  <figcaption><strong>Select row checkboxes, not the name links.</strong> Match Target versions 6 and 7 with both selection marks. Both runs still show Partial. <a href="../../web/assets/portal/v1.1/49-select-comparison-runs.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

11. When **Compare runs** above the list becomes enabled, select it. Set **Baseline** to the original baseline run. **The portal may default to the newest run.** If names are identical, match your recorded means with the Baseline column.
    {: value="11"}

<figure class="portal-shot" id="shot-compare-runs-v1-1">
  <img src="../../web/assets/portal/v1.1/24-compare-runs.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Statistical comparison showing baseline means, Relevance Improved, and TaskAdherence Inconclusive">
  <figcaption><strong>Read baseline direction and statistical conclusions together.</strong> This run shows Relevance Improved by 1.27 and TaskAdherence Inconclusive. Higher observed pass rates are not proof that both metrics improved statistically. <a href="../../web/assets/portal/v1.1/24-compare-runs.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

12. Read **mean scores and statistical conclusions**. Apply the criteria below, including the errors and actual responses you inspected, and record your conclusion.
    {: value="12"}

Both runs are **Partial: the same Index 9 of twelve cases was blocked by `cyber_policy`**. The denominators above are the **eleven common valid cases**. The statistical screen reports **Improved by 1.27** for Relevance and **Inconclusive** for TaskAdherence. **Both observed pass rates rose, but improvement over all twelve cases or statistical significance for both metrics was not established.**

**Choose one of three conclusions.** If every case is valid, neither quality metric regresses, at least one improves, and the actual answers are correct, record observed improvement on this sample. If scores are unchanged or either metric worsens, retain the baseline and investigate. **If Partial, missing cases, or provider blocks remain, record that overall improvement has not been established.** Higher Overall does not cancel a regression in another quality metric. Saving a teaching comparison version is not production adoption.

Do not copy reference answers into instructions, remove failed cases, or overwrite baseline results to manufacture a comparison.

The separate Optimizer job generated **one candidate** in **6m 23s**, with Task-weighted average **0.625 → 0.781**. The original still contained policy examples and restrictions and was not promoted unchanged. The table above measures the **human-corrected v2 again under the same evaluation definition**, not that original candidate. From a baseline with working retrieval and JSON, v2 also improved real responses, including clarifying cancellation versus downgrade intent and calculating refund deadlines.

**Done when:** You have compared two actual runs under fixed conditions or recorded why no candidate was adopted. Do not publish to production or promise statistical improvement.
{: .completion-check}

## 10. Preserve results and clean up resources {#portal-finish}

**Where to act:** Foundry Portal results and your dedicated resource group in Azure Portal.
{: .step-route}

1. If you plan to resume, privately record the project and Agent names, baseline/comparison versions, dataset version, evaluation and Optimizer run IDs, errors, and conclusions.
2. Use **Download results / Download JSON** in the portal when downloading results. Do not publish signed download URLs, account/subscription identifiers, keys, or tokens.
3. In Foundry Portal, open **Models** and inspect the lab deployments. This is the inventory to retain or clean up; do not deploy it again.

<figure class="portal-shot" id="shot-retained-models-v1-1">
  <img src="../../web/assets/portal/v1.1/28-retained-models.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Three role deployments and automatic embedding remaining at the end of the lab">
  <figcaption><strong>Check the deployments remaining at the end.</strong> This demo retains three roles and automatic embedding. Decide on retention or authorized deletion below. <a href="../../web/assets/portal/v1.1/28-retained-models.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

4. Switch to **Azure Portal tab → Resource groups → your new group → Refresh**. Verify the group name and lab resources.
   {: value="4"}

<figure class="portal-shot" id="shot-retained-group-v1-1">
  <img src="../../web/assets/portal/v1.1/27-retained-resource-group.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Dedicated group with the Foundry resource and project remaining at the end of the lab">
  <figcaption><strong>The group and two resources remain.</strong> This is not completed deletion. Verify that it is your own dedicated lab group before making the final decision. <a href="../../web/assets/portal/v1.1/27-retained-resource-group.v1.1.png" target="_blank" rel="noopener">View full-size image</a></figcaption>
</figure>

5. Complete **one** of the final actions below, verify the outcome, and finish the lab.
   {: value="5"}

| Final decision | Action and verification |
|---|---|
| **Retain** | Record cost responsibility and the next review/deletion date, then keep the group. Do not unnecessarily recreate resources or rerun evaluations. |
| **Authorized deletion** | In your own dedicated group, select **Delete resource group → enter the group name → Delete**. After completion, use **Resource groups → Refresh** to verify the group is gone. Do not separately delete shared or external resources. |

The environment in this recording was **retained** for review and resumption. The end of the video does not mean resources were deleted. Check the applicable pricing for File search storage, model usage, and other services.

**Resume:** Open your group in Azure Portal and select the same project in Foundry Portal. Inspect existing Agent versions and evaluation runs before performing only the necessary next action.

**Common blockers**

| Symptom | What to check in the portal |
|---|---|
| New project is missing | Same organizational account and subscription; correct project in the top selector. |
| Validation succeeded but no resource exists | Group Overview, Deployments, and errors. Validation alone is not creation. |
| File search is disabled | The actual Agent model is `gpt-5.5 / agent-v1-1` for this path. |
| Cannot find file upload under Knowledge | Use **Tools → File search**, not Foundry IQ. |
| Policy file appears twice | Remove duplicate entries before Attach and verify one successful file. |
| TaskAdherence fails every case | Binary Threshold is **1**, Probability_threshold is **0.5**. |
| Partial or `cyber_policy` error | Preserve Error and success/failure denominators. Do not bypass safeguards or rewrite questions. |
| A deleted model still appears | Refresh the page and inspect the actual deployment list. |

**Done when:** Results and errors are preserved and retention or deletion is verified. Closing the browser is not cleanup.
{: .completion-check}

Official references: [Create a project](https://learn.microsoft.com/azure/foundry/how-to/create-projects) · [Evaluation](https://learn.microsoft.com/azure/foundry/how-to/evaluate-generative-ai-app) · [File search](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/file-search) · [Agent Optimizer](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview).
