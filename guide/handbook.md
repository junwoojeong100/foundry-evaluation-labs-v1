# 좋은 에이전트는 평가에서 시작된다 · v1 {#좋은-에이전트는-평가에서-시작된다-v1}

<p class="eyebrow">CONTOSO ATLAS CLOUD · 하나의 실습 경로</p>

**자사 업무를 평가하고, Agent Optimizer로 지침을 개선한 뒤 같은 기준으로 더 나은 v2인지 확인합니다.**

<ol class="learning-path" role="list" aria-label="실습 순서">
<li><a href="#start"><strong>01</strong> 데이터셋 준비</a></li>
<li><a href="#prepare"><strong>02</strong> 평가 기준 선택</a></li>
<li><a href="#baseline"><strong>03</strong> Foundry Evaluation 실행</a></li>
<li><a href="#analyze"><strong>04</strong> 점수와 이유 읽기</a></li>
<li><a href="#optimize"><strong>05</strong> Agent Optimizer로 지침 개선</a></li>
<li><a href="#decision"><strong>06</strong> 재평가·v1/v2 비교</a></li>
</ol>

공개 벤치마크만 보는 대신 **대표적인 자사 과제와 업무 기준**으로 평가합니다. 합성 Contoso 정책을 사용해 고객 원본 데이터를 공개하지 않고 **평가 → 학습 → 개선 → 재평가**를 경험합니다.

[운영자](admin-setup.md#handoff)가 격리 프로젝트·Agent·정책 도구·모델 배포·비용 승인을 준비합니다. 인프라·Judge 교정·별도 governance는 참가자 추가 필수 실습이 아닙니다.

**버전 의미:** v1/v2는 Foundry Agent 전체 구성 버전입니다. 현재 실측은 둘 다 `gpt-6-sol`이며 지침만 다릅니다. v1을 약화하거나 측정 전에 개선을 보장하지 않습니다. 후보는 초안에서 개발하고 정식 버전은 **v1·v2**만 유지합니다.

<p class="output-notice" id="portal-screenshots-note"><strong>화면 읽는 방법:</strong> 실제 영문 포털의 이전 캡처이며 조작 위치를 설명합니다. 화면의 모델·버전·점수는 현재 Sol 검증이 아닙니다. 실제 질문·응답·점수·이유 전체와 현재 비교는 <a href="verification.md">최신 v2 보고서</a>를 기준으로 읽습니다. 한국어 설명이 한국어 실측 완료를 뜻하지 않습니다.</p>

## 01. 데이터셋 준비 {#start}

<a id="demo"></a><a id="understand"></a><a id="data"></a>

한국어 절차는 **[data/optimizer/dev.jsonl](../data/optimizer/dev.jsonl)**의 **JSONL 12행**을 변경 없이 사용합니다. 실제 최신 영어 실행은 별도 `data/en/optimizer/dev.jsonl`과 등록 **`contoso-eval-en-dev12` 버전 `1`**을 사용했습니다. 한국어는 운영자가 확인한 별도 등록·Agent를 사용하며 영어 실행을 한국어 결과로 바꾸어 표시하지 않습니다.

| 열 | 형식 | 용도 |
|---|---|---|
| `query` | 문자열 | Agent에 보내는 유일한 입력 |
| `context` | 문자열 | 지원 평가기와 사례 검토용 정책 참고 자료 |
| `ground_truth` | JSON 문자열 | 구조화 참고 답변이며 생성 프롬프트가 아님 |

12행 전체, 등록·버전과 SHA-256을 기록합니다. 기준선·최적화·재평가에서 같은 바이트를 유지합니다. 원본의 나머지 분할은 이번 필수 실습에 포함하지 않습니다.

응답은 정확히 `answer`, `citations`, `route`, `needs_human`입니다. 한국어 실습의 answer는 한국어, 인용은 근거 정책 ID, route는 `answer/clarify/escalate/refuse`, 불리언 needs_human은 `escalate`일 때만 true입니다. Agent는 제출·환불·삭제·권한 부여를 실제 수행하지 않습니다.

**Foundry New experience → Build → Evaluations → Create → Create new evaluation**을 엽니다. 준비된 언어별 Agent를 선택하고 기준선을 **v1로 명시 고정**한 뒤 대상 한 개가 체크됐는지 확인합니다. 최신이 실제 v1일 때만 **Pin currently latest**를 사용하며 버전 변경으로 해제된 체크박스는 다시 선택합니다. 현재 영어 대상은 **`contoso-eval-en-sol`**입니다.

**Individual turns**, **One time**, **Existing dataset**을 선택합니다. 준비된 dev12 등록을 재사용하며 새 승인 프로젝트에서 등록이 없을 때만 원본을 업로드합니다. 미리 보기가 5행이어도 전체는 12행입니다.

<figure class="portal-shot" id="portal-evaluation-dataset">
<img src="../web/assets/portal/en/15-evaluation-dataset.png" alt="Existing dataset과 5행 미리 보기의 위치를 설명하는 이전 영문 Foundry 화면. 현재 실측이 아님" width="1440" height="1000" loading="lazy">
<figcaption><strong>데이터셋 선택 위치.</strong> 현재 운영자가 지정한 등록을 사용합니다. 미리 보기의 행 수를 전체 데이터셋 건수로 해석하지 않습니다. <a href="../web/assets/portal/en/15-evaluation-dataset.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**완료 신호:** 명시적 v1과 변경 없는 12행 데이터셋을 선택하고 건수·버전·해시를 기록했습니다. [데이터 계약](../data/README.md#schema).

<p class="step-next no-print"><a href="#prepare" data-next-step>다음: 02. 평가 기준 선택 →</a></p>

## 02. 평가 기준 선택 {#prepare}

<a id="environment"></a><a id="calibration"></a><a id="model-smoke"></a><a id="first-infrastructure-failure"></a>

**Configure agents**의 custom prompt override는 비워 둡니다. 입력은 **`{{item.query}}`만**이며 context·ground_truth를 붙이지 않습니다. 필드 매핑 화면이 나타나면 query → query를 사용합니다.

관리형 평가자는 정확히 두 개만 남깁니다.

| 평가기 | 의미 | 설정 |
|---|---|---|
| Relevance | 질문에 관련된 답변인지, **1–5점** | **Threshold 4** |
| TaskAdherence | 과제 지시를 따르는지, **이진 0/1 Pass/Fail** | **통과 1**, 임계값 4가 아님 |

명시적 Judge 배포를 선택하고 서비스 생성 매핑을 유지합니다. Relevance는 `response={{sample.output_text}}`, TaskAdherence는 `response={{sample.output_items}}`입니다. 이전 UI 값으로 덮어쓰지 말고 정의의 Raw JSON을 확인합니다.

| 역할 | 모델·버전 | 배포 |
|---|---|---|
| Agent | **gpt-6-sol / 2026-09-22** | `lab-agent-sol-dea3cec5` |
| 평가 Judge | **gpt-6-luna / 2026-09-22** | `lab-judge-luna-dea3cec5` |
| Optimizer 생성 | **gpt-5.5 / 2026-04-24** | `lab-planner-dea3cec5` |

Sol의 실제 Agent·도구 호출을 확인했습니다. 카탈로그 표시만으로 충분하지 않으며 [Optimizer 지원 목록](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)은 별도입니다. 카탈로그 평가기 버전 링크가 비공개 서비스 루브릭 고정의 증거는 아니므로 실제 정의와 한계를 기록합니다.

<figure class="portal-shot" id="portal-evaluation-criteria">
<img src="../web/assets/portal/en/16-evaluation-criteria.png" alt="Relevance·TaskAdherence와 별도 Judge 선택 위치를 설명하는 이전 영문 화면" width="1440" height="1000" loading="lazy">
<figcaption><strong>지표별 척도 확인.</strong> Relevance 임계값 4, 이진 TaskAdherence 통과값 1과 현재 Luna Judge를 유지합니다. <a href="../web/assets/portal/en/16-evaluation-criteria.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**완료 신호:** 두 평가기 척도·임계값·매핑·실제 Judge를 기록했습니다. 오래된 로컬 환경 기본값이 아니라 저장된 원격 정의가 Judge를 결정합니다.

<p class="step-next no-print"><a href="#baseline" data-next-step>다음: 03. Foundry Evaluation 실행 →</a></p>

## 03. Foundry Evaluation 실행 {#baseline}

**v1 + 원본 dev12 + query 전용 입력 + 두 평가기 + Luna Judge**를 검토합니다. 현재 영어 비교는 **`contoso-en-sol-learning-loop`**입니다. 기록된 리허설을 살펴보는 경우 기존 완료 run을 열고 다시 제출하지 않습니다.

새 승인 수업은 **Review → Submit**으로 한 번 제출하고 실제 evaluation ID·run ID를 기록합니다. 완료를 기다리고 오류·누락까지 전체 12건을 확인합니다. 초안 구성·HTTP 생성 응답·모델 연결 확인이 평가 완료를 뜻하지 않습니다.

<figure class="portal-shot" id="portal-evaluation-review">
<img src="../web/assets/portal/en/17-evaluation-review.png" alt="평가 Review 조작 위치를 설명하는 이전 화면. 현재 Sol 대상과 실제 ID를 별도로 사용" width="1440" height="1000" loading="lazy">
<figcaption><strong>Submit 전 검토.</strong> 이전 조작 예시이지 현재 Sol 실행 결과가 아닙니다. 실제 고정 버전과 저장된 평가 계약을 확인합니다. <a href="../web/assets/portal/en/17-evaluation-review.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**완료 신호:** 실제 Foundry run이 Completed이고 결과 12건을 확인할 수 있습니다. 실패·부분 실행을 그대로 기록하며 관리형 Evaluation을 자체 로컬 Judge로 대신하지 않습니다.

<p class="step-next no-print"><a href="#analyze" data-next-step>다음: 04. 점수와 이유 읽기 →</a></p>

## 04. 점수와 이유 읽기 {#analyze}

<a id="iq"></a><a id="score-rubric"></a><a id="worked-evaluation"></a>

요약과 **Detailed metrics result**의 **`Relevance.reason`**, **`TaskAdherence.reason`**을 읽습니다. `conversation_id → User view`는 실제 질문·응답이며 인라인 Judge 이유 패널이 아닙니다.

실패 또는 최저점 사례와 잘한 사례를 골라 **질문 → 실제 응답 → 점수·이유 → 정책·참고 답변**을 연결합니다. 실패가 없으면 그 사실을 말하며 사례를 만들려고 기준선을 약화하지 않습니다.

<figure class="portal-shot" id="portal-evaluation">
<img src="../web/assets/portal/en/18-evaluation-results.png" alt="평가 요약·상세 지표의 위치 예시. 현재 수치는 최신 v2 보고서에서 확인" width="1440" height="1000" loading="lazy">
<figcaption><strong>점수·이유 위치.</strong> 이전 UI 예시이지 현재 검증이 아닙니다. 현재 run ID와 전체 사례는 최신 보고서를 기준으로 읽습니다. <a href="../web/assets/portal/en/18-evaluation-results.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

Relevance 4/5를 정확도 80%로 해석하지 않습니다. TaskAdherence 1은 통과이지 낮은 5점 척도 점수가 아닙니다. 누락은 0점이나 성공 행이 아니며 범용 평가기가 모든 업무 규칙을 인증하지는 않습니다.

<figure class="portal-shot" id="portal-evaluation-case">
<img src="../web/assets/portal/en/19-evaluation-case.png" alt="질문·JSON 응답을 보여 주는 conversation_id User view의 이전 예시. 채점 이유가 아님" width="1440" height="340" loading="lazy">
<figcaption><strong>응답은 별도로 읽습니다.</strong> 이유는 Detailed metrics result로 돌아가 정책과 대조합니다. 이전 그림의 답을 최신 결과로 복사하지 않습니다. <a href="../web/assets/portal/en/19-evaluation-case.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

날짜 경계 오류, 불필요한 가정, 정책 ID 대신 숫자 검색 ID, 사람 검토 분류 오류, 실행 완료 주장과 근거 없는 확신을 확인합니다. 정직한 불확실성을 높은 점수를 위한 허위 사실로 바꾸지 않습니다.

<p class="share-checkpoint" id="share-baseline"><strong>공유:</strong> 실제 run ID·지표별 척도·통과 건수와 문제 응답을 제시하고 어떤 지침 행동을 개선할지 설명합니다.</p>

**완료 신호:** 평균만이 아니라 실제 약점과 근거 있는 개선 가설을 설명할 수 있습니다.

<p class="step-next no-print"><a href="#optimize" data-next-step>다음: 05. Agent Optimizer로 지침 개선 →</a></p>

## 05. Agent Optimizer로 지침 개선 {#optimize}

<a id="tune"></a>

**Build → Agents → 준비된 언어별 Agent → Optimize Preview → Agent**를 엽니다. Cost가 아닙니다. 영어 대상은 `contoso-eval-en-sol`이며 새 작업에서는 **Create an optimization run**을 사용합니다.

| 설정 | 선택 |
|---|---|
| Agent version | 명시적 기준선 **1** |
| Choose targets | **Instruction only**, Model·Tool description 끄기 |
| Max candidates | 운영자 승인 한도. 이번 작업은 최대 **2**이며 정식 버전 수와 다름 |
| Optimization model | `lab-planner-dea3cec5` / gpt-5.5 |
| Evaluation model | `lab-judge-luna-dea3cec5` / gpt-6-luna |
| Dataset | 같은 언어의 등록 dev12·같은 버전 |
| Criteria | Relevance 4, TaskAdherence 이진 통과 1 |

<figure class="portal-shot" id="portal-optimizer-target">
<img src="../web/assets/portal/en/07-optimizer-target.png" alt="지침 전용 Agent Optimizer 설정 위치의 이전 예시. 현재 Sol 작업 설정이 아님" width="1210" height="968" loading="lazy">
<figcaption><strong>모델 역할을 구분합니다.</strong> 현재 Sol 대상·Luna Judge·지원 생성 모델을 사용합니다. 그림은 조작 위치만 설명합니다. <a href="../web/assets/portal/en/07-optimizer-target.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

Criteria가 **No custom evaluators available**이면 **Custom only OFF** 또는 **View built-in evaluators**를 선택합니다. 각 기본 평가기의 임계값을 설정하고 Apply합니다. 필터를 우회하려고 다른 평가기를 만들지 않습니다.

<figure class="portal-shot" id="portal-optimizer-data">
<img src="../web/assets/portal/en/08-optimizer-dataset.png" alt="기존 영어 dev12를 선택하는 Agent Optimizer 데이터셋 화면의 예시" width="1210" height="968" loading="lazy">
<figcaption><strong>데이터 재사용.</strong> 같은 등록 버전과 12행 전체를 사용합니다. 데이터를 새로 생성하거나 수정 업로드하면 실험 조건이 달라집니다. <a href="../web/assets/portal/en/08-optimizer-dataset.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

승인된 비용 범위에서 한 번 제출하고 최대 60분 기다린 뒤 실제 상태를 남깁니다. 재개 시 기존 job ID를 사용합니다. 작업 하나에도 여러 내부 호출이 포함됩니다.

원본·후보 결과와 **View changes**를 읽습니다. 내부 **0–1 순위**는 별도 관리형 Evaluation 평균·통과율과 다릅니다. 모델·도구·추론·출력 스키마를 유지하며 함수 도구 export가 비었다고 MCP 정책 연결을 제거하지 않습니다.

**현재 실행:** 관리형 Optimizer는 이미 강한 v1을 유지하도록 선택했습니다. 생성 후보를 자동 승격하지 않았고, 운영자가 관측한 실패를 바탕으로 지침을 정리한 뒤 초안을 별도로 검증했습니다. 따라서 현재 v2는 **Agent Optimizer 이후 운영자가 검토한 지침**이며 서비스가 자동 추천한 후보라고 표시하지 않습니다.

<figure class="portal-shot" id="portal-optimizer-results">
<img src="../web/assets/portal/en/09-optimizer-results.png" alt="Optimizer 결과 조작 위치의 이전 예시. 최신 작업의 실측은 별도 보고서에 있음" width="1440" height="1000" loading="lazy">
<figcaption><strong>순위뿐 아니라 후보를 확인합니다.</strong> 이전 UI 예시입니다. 현재 보고서에서 실제 작업·후보 ID를 확인합니다. <a href="../web/assets/portal/en/09-optimizer-results.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-optimizer-diff">
<img src="../web/assets/portal/en/10-optimizer-changes.png" alt="지침을 비교하는 View changes 대화상자의 이전 예시. 현재 Sol 후보 지침이 아님" width="1038" height="622" loading="lazy">
<figcaption><strong>현재 지침의 실제 차이를 검토합니다.</strong> 허위 정책·근거 없는 확신·설정 변경을 거부합니다. 지침이 길다고 더 좋지는 않습니다. <a href="../web/assets/portal/en/10-optimizer-changes.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**v3·v4 등 정식 버전을 계속 만들지 않습니다.** 운영자가 후보를 명시적 초안으로 먼저 평가합니다. **같은 기준의 실제 검증에서 품질 회귀 없는 개선을 확인한 뒤에만 Promote 또는 v2 생성**을 진행합니다. 승격은 운영용 게시·운영 트래픽 변경 승인이 아닙니다.

<p class="share-checkpoint" id="share-optimizer"><strong>공유:</strong> 어떤 지침 행동이 바뀌고 무엇이 개선·회귀할 수 있나요? 이전 그림이 아니라 실제 현재 후보를 제시합니다.</p>

**완료 신호:** 실제 관리형 Optimizer 결과와 검토 후보가 있으며 별도 재평가가 필요함을 이해했습니다.

<p class="step-next no-print"><a href="#decision" data-next-step>다음: 06. 재평가·v1/v2 비교 →</a></p>

## 06. 재평가·v1/v2 비교 {#decision}

<a id="review"></a><a id="operate"></a><a id="cleanup"></a>

**같은 Foundry 평가 정의**, 같은 dev12·Luna Judge를 사용합니다. 이 포털의 Add run에서는 **`Unable to create data source configuration from item schema`**가 관측됐습니다. 공식 Azure AI Projects/OpenAI Evals helper로 실제 관리형 run을 제출하며 로컬 채점이 아닙니다.

운영자가 준비한 venv와 검증된 `az login` 상태에서 다음 네 자리표시자를 **자신의** 프로젝트·기준선 ID로 교체합니다. 한국어 실습에는 별도의 한국어 기준선이 필요합니다.

```bash
export AZURE_AI_PROJECT_ENDPOINT="OPERATOR_PROJECT_ENDPOINT"
export AZURE_SUBSCRIPTION_ID="OPERATOR_SUBSCRIPTION_ID"
export FOUNDRY_EVALUATION_ID="YOUR_EVALUATION_ID"
export FOUNDRY_BASELINE_RUN_ID="YOUR_BASELINE_RUN_ID"
```

운영자는 v2 생성 전에 명시적 초안을 검증할 수 있습니다. 정식 v2가 생성된 뒤에는 다음 명령을 사용합니다.

```bash
python scripts/add_foundry_eval_run.py --endpoint "$AZURE_AI_PROJECT_ENDPOINT" --subscription "$AZURE_SUBSCRIPTION_ID" --evaluation "$FOUNDRY_EVALUATION_ID" --baseline "$FOUNDRY_BASELINE_RUN_ID" --version 2 --name candidate-v2 --out .lab/foundry-evaluations/candidate-v2.json
```

receipt는 중복 제출을 방지합니다. 동일 명령·경로는 같은 run을 수집할 때만 재사용합니다. helper는 같은 원격 이름, 원격 임계값·Judge·매핑과 모든 결과 행의 실제 버전·시스템 지시도 확인합니다.

**Evaluation runs**에서 두 행을 선택하고 **Compare runs**를 엽니다. **Baseline을 v1으로 명시 선택**하며 행 선택 순서 때문에 비교 방향이 바뀌지 않게 합니다.

<figure class="portal-shot" id="portal-evaluation-comparison">
<img src="../web/assets/portal/en/20-evaluation-comparison.png" alt="Compare runs의 이전 화면 예시. 현재 v1/v2 수치와 통계 결과는 최신 보고서에서 확인" width="1440" height="520" loading="lazy">
<figcaption><strong>비교 방향 확인.</strong> Baseline 조작 위치의 예시이지 현재 Sol 실측이 아닙니다. 최신 보고서의 정확한 두 run ID를 사용합니다. <a href="../web/assets/portal/en/20-evaluation-comparison.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

현재 [v2 검증](verification.md#status)은 v1 대조군과 12건 전체의 응답·점수·이유를 공개합니다. 전체 기준 통과와 각 지표의 통과 건수·평균이 낮아지지 않고 하나 이상이 명확히 개선되어야 합니다. 사실·분류·응답 형식도 확인하며 지연·토큰·통계 검정은 구분해 보고합니다.

<p class="share-checkpoint" id="share-optimized"><strong>결과 설명:</strong> 실제 개선, 같은 평가 기준, 회귀와 남은 불확실성을 설명합니다. 관측된 개선이 향후 모든 확률적 실행의 개선을 보장하지는 않습니다.</p>

**완료 신호:** 최신 v2의 동일 모델 비교가 완전하고 정직하게 기록됐습니다. 정식 버전을 누적하지 않고 현재 보고서 하나를 유지합니다. 운영 승인·독립적 일반화는 별개이며 dev12 실습으로 부여되지 않습니다.

<a id="troubleshooting"></a><a id="sources"></a>

**종료:** 실제 run/job ID, 데이터 해시와 실측 결정을 운영자에게 전달합니다. 원본 receipt는 로컬에 보존하고 합성 응답·이유는 인증·쿠키·서명된 URL·비공개 계정 정보 없이 공개합니다. [강사 복구 안내](facilitator.md#resume) · [데이터 계약](../data/README.md).
