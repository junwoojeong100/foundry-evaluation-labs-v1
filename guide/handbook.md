# 좋은 에이전트는 평가에서 시작된다 · v1 {#좋은-에이전트는-평가에서-시작된다-v1}

<p class="eyebrow">CONTOSO ATLAS CLOUD · 하나의 실습 경로</p>

**Foundry에서 자사 업무를 평가하고, Agent Optimizer로 지시를 개선한 뒤 무엇이 바뀌었는지 확인합니다.** 아래 여섯 단계만 진행합니다.

<ol class="learning-path" role="list" aria-label="실습 순서">
<li><a href="#start"><strong>01</strong> 데이터셋 준비</a></li>
<li><a href="#prepare"><strong>02</strong> 평가 기준 선택</a></li>
<li><a href="#baseline"><strong>03</strong> Foundry Evaluation 실행</a></li>
<li><a href="#analyze"><strong>04</strong> 점수와 이유 읽기</a></li>
<li><a href="#optimize"><strong>05</strong> Agent Optimizer로 지시 개선</a></li>
<li><a href="#decision"><strong>06</strong> 재평가·비교·종료</a></li>
</ol>

**왜 자사 데이터로 평가하나요?** 공개 벤치마크만으로는 우리 업무의 정책 경계와 알려진 실패를 확인하기 어렵습니다. 합성 Contoso 사례로 **평가 → 실패에서 학습 → 개선 → 재평가**를 경험합니다. 운영 안전을 인증하는 실습은 아닙니다.

**시작 전:** [운영자](admin-setup.md#handoff)가 격리된 프로젝트, 준비된 에이전트와 기준선 버전, 배포 이름, 비용·데이터 승인 범위를 제공합니다. 인프라는 사전 준비이지 추가 실습이 아닙니다. 처리·토론 시간을 확보하며 최적화 작업은 **최대 60분** 기다립니다.

**한 실험은 한 언어로 진행합니다.** 한국어 파일과 한국어 에이전트를 짝지어 사용합니다. 문서 언어를 바꿔도 에이전트나 데이터셋은 번역되지 않습니다.

<p class="output-notice" id="portal-screenshots-note"><strong>실제 영문 화면·데이터:</strong> 완료한 영문 리허설의 조작 예시이며 한국어 실행 결과나 현재 참가자의 결과는 아닙니다. 자신의 run ID를 사용하고 <a href="verification.md">실측 결과와 한계</a>를 확인합니다. 마법사 미리 보기는 평가 실행이 아닙니다.</p>

## 01. 데이터셋 준비 {#start}

<a id="demo"></a>
<a id="understand"></a>
<a id="data"></a>

<div class="lab-concept" aria-label="01 학습 목표">
<p><strong>무엇:</strong> 작고 반복 가능한 도메인 과제 집합입니다. <strong>왜:</strong> 같은 질문으로 지시 개선 전후의 변화를 확인합니다. <strong>어떻게:</strong> 제공된 JSONL을 살펴본 뒤 12건 전체를 평가 초안에 업로드합니다.</p>
</div>

**[data/optimizer/dev.jsonl](../data/optimizer/dev.jsonl)**을 변경 없이 사용합니다. JSON 배열이 아닌 **12행 JSONL**입니다. 원본에는 100건이 있지만 이 워크숍에서는 dev12 파일만 사용하며 나머지 분할은 사용하지 않습니다.

| 열 | 형식 | 용도 |
|---|---|---|
| `query` | 문자열 | 에이전트에 보내는 유일한 입력 |
| `context` | 문자열 | 평가자·검토자 참고용 정책 원문 발췌 |
| `ground_truth` | **JSON 문자열** | 구조화된 모범 응답. 생성 프롬프트나 미리 만든 응답이 아님 |

로컬에서 12개 레코드를 모두 확인하고 운영자 인수 자료의 파일 **SHA-256**을 기록합니다. 기준선·최적화·재평가에서 같은 바이트, 등록 데이터셋 버전, 해시를 유지합니다. 행을 줄이거나 복제하거나 번역하지 않으며 가짜 `response` 열도 추가하지 않습니다. 자세한 형식은 [데이터 계약](../data/README.md#schema)을 확인합니다.

준비된 에이전트는 정확히 네 응답 키를 반환합니다. 아래는 계약 예시이지 측정된 답변이 아닙니다.

| 키 | 계약 |
|---|---|
| `answer` | 비어 있지 않은 한국어 문장. 예: “구매일을 확인해 주세요.” |
| `citations` | 근거 정책 ID. 예: `["ATLAS-REF-001"]` |
| `route` | `answer`, `clarify`, `escalate`, `refuse` 중 하나 |
| `needs_human` | 불리언. `escalate`일 때만 `true` |

도우미는 안내할 뿐 환불·티켓 생성·접근 권한 부여를 실행하지 않습니다. 사람 판단이 필요하다는 설명도 실제로 담당자에게 연락했다는 증거는 아닙니다.

**포털 조작:** [Foundry](https://ai.azure.com/)의 **New experience**에서 운영자가 지정한 프로젝트를 선택한 뒤 **Build → Evaluations → Create → Create new evaluation**을 엽니다.

1. 최신이 아직 v1인 새 기준선 Agent에서 **Target → `contoso-eval-ko` → Pin currently latest**로 구성 변경 전에 고정하고 **해제된 체크박스 재선택·Next 전 대상 1개**를 확인합니다. 실제 영어 Agent는 후보 v2를 보존한 채 활성 v1으로 복원됐으므로 “최신”을 추정하지 말고 명시적 버전·저장된 기준선을 사용합니다. 실패한 `gpt-6-luna` v2는 다른 Agent입니다.
2. **Scope: Individual turns**로 설정합니다. Full conversations가 아닙니다. **Frequency: One time**으로 설정하며 반복 실행은 선택하지 않습니다.
3. **Data**에서 **Existing dataset**을 선택합니다. 기본값인 Synthetic generation, Benchmarks, Existing traces는 사용하지 않습니다.
4. 운영자가 이미 등록한 **`contoso-eval-ko-dev12`**가 있으면 같은 버전을 선택하고 중복 업로드하지 않습니다. 없다면 **Upload new dataset**에서 이름을 지정하고 **Choose file**로 `data/optimizer/dev.jsonl`을 선택해 **Upload**합니다. 실제 등록이 확인된 영어 데이터셋 `contoso-eval-en-dev12`를 한국어 입력으로 대신 사용하지 않습니다.
5. 데이터셋이 선택되고 미리 보기에 나타나는지 확인한 뒤 실제 등록 버전을 기록합니다. 관측한 영어 마법사에서는 일치하는 스키마로 **Field mapping이 자동 해결**되어 바로 **Configure agents**로 이어졌습니다. 한국어 경로에서 매핑 화면이 나타나면 **query → query**를 사용합니다.

<figure class="portal-shot" id="portal-evaluation-dataset">
<img src="../web/assets/portal/en/15-evaluation-dataset.png" alt="영어 dev12 JSONL을 선택하고 미리 보는 Foundry 평가 데이터셋 화면. 한국어 실행 결과가 아님" width="1440" height="1000" loading="lazy">
<figcaption><strong>데이터셋 선택.</strong> 영문 UI·영문 데이터 리허설 화면; 한국어 실행 결과가 아님. Existing dataset과 업로드한 파일을 확인합니다. 미리 보기는 처음 5행만 보여 주므로 전체가 5건이라는 증거가 아닙니다. <a href="../web/assets/portal/en/15-evaluation-dataset.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**완료 신호:** 초안에 명시적 기준선 버전과 12행 데이터셋이 선택되어 있고 로컬 행 수·해시가 기록되어 있습니다. 미리 보기는 준비이지 실행이 아닙니다. 파일이나 버전이 다르면 다음으로 진행하기 전에 초안을 고칩니다.

<p class="step-next no-print"><a href="#prepare" data-next-step>다음: 02. 평가 기준 선택 →</a></p>

## 02. 평가 기준 선택 {#prepare}

<a id="environment"></a>
<a id="calibration"></a>
<a id="model-smoke"></a>
<a id="first-infrastructure-failure"></a>

<div class="lab-concept" aria-label="02 학습 목표">
<p><strong>무엇:</strong> 결과 형식이 다른 두 관리형 평가자입니다. <strong>왜:</strong> 비교하려면 지표별 척도를 지켜야 합니다. <strong>어떻게:</strong> Relevance 임계값 4, TaskAdherence 이진 통과값 1과 검증된 Judge 배포를 사용합니다.</p>
</div>

**Configure agents**에서는 **custom prompt override를 설정하지 않습니다**. 에이전트 입력은 **`query`만** 사용합니다. `context`와 `ground_truth`는 평가자 참고로 분리하며 답을 잘 만들게 하려고 질문에 붙이지 않습니다.

관측한 포털의 **Criteria**에는 **평가자 23개**가 제안되었습니다. 나머지는 제거하고 **Relevance**와 **TaskAdherence**만 남깁니다. Optimizer에서는 후자가 **Task Adherence**로 표시될 수 있습니다.

| 평가자 | 살펴볼 내용 | 필수 설정 |
|---|---|---|
| Relevance | 질문을 다루는 응답인지 평가, **1–5점** | **Edit Relevance evaluator → Threshold 4 → Update** |
| TaskAdherence | 과제 지시 준수 여부, **Binary Pass/Fail, 원시값 0/1** | **통과값 = 1**. 범용 임계값 UI가 보이면 **Edit TaskAdherence evaluator → Threshold 1 → Update** |

[공식 에이전트 평가기 정의](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators)는 **TaskAdherence를 이진 평가**로 명시합니다. 서비스가 반환한 Pass/Fail을 읽으며, 통과값 `1`을 5점 중 1점으로 해석하지 않습니다.

**Model: Judge model**에는 Agent 모델이 아닌 **`lab-judge-luna-dea3cec5`**를 선택합니다. 두 평가자 이름·결과 형식·설정, Judge 배포·모델 버전, 데이터셋 버전·해시를 기록합니다. 평가자는 정확히 두 개이며 이 수정으로 참가자 단계를 추가하지 않습니다.

**카탈로그 참조가 서비스 버전 고정은 아닙니다.** 링크에는 `relevance` **v14**, `task_adherence` **v17**이 보였지만 제출된 서비스 기준의 **`evaluator_version`은 비어 있거나 기본값**이었습니다. 비공개 서비스 루브릭 버전이 완전히 고정됐다고 주장하지 않습니다. 저장된 평가 정의를 유지하고 이 한계를 기록합니다.

**매핑은 확인하되 생성된 값을 덮어쓰지 않습니다.** 수정된 제출에서 **Relevance `response={{sample.output_text}}`**, **TaskAdherence `response={{sample.output_items}}`**를 확인했습니다. UI 기본값에는 `query={{item.query}}`, TaskAdherence의 `tool_definitions={{sample.tool_definitions}}`도 있었습니다. **Raw JSON**을 읽고 TaskAdherence를 이전 UI의 output-text 연결로 되돌리지 않습니다. 추가 JSONL 열이나 생성 입력이 아닙니다.

**세 모델 역할은 서로 다릅니다.** 요청은 역할별 실제 지원 범위에서 `gpt-6-luna`를 사용하는 것이지 모든 역할에 같은 모델을 강제하는 것이 아닙니다.

| 역할 | 워크숍 선택 범위 |
|---|---|
| 질문에 답하는 에이전트 | **`lab-agent-dea3cec5` → `gpt-4.1-mini` / `2025-04-14`**. 한국어는 운영자가 준비한 **`contoso-eval-ko` v1**과 읽기 전용 지식 연결을 확인해 사용. 실제 확인된 영어 대상은 **`contoso-eval-en` v1**이며 한국어 새 결과를 뜻하지 않음 |
| 평가 Judge | **`lab-judge-luna-dea3cec5` → `gpt-6-luna` / `2026-09-22`**. 실제 관리형 기준선·후보 평가에서 사용 확인 |
| Optimizer 지시 생성 모델 | **`lab-planner-dea3cec5` → `gpt-5.5` / `2026-04-24`**. 공식 지원 최적화 모델 목록에는 `gpt-6-luna`가 **없음** |

**기능 호환성 검증은 Agent 품질 평가가 아닙니다.** 앞선 `gpt-6-luna` 네이티브 Relevance 검사는 **작성된 호환성 fixture 한 건에서 passed 1 / total 1 / errors 0**이었으며 Chat Completions는 READY를 반환했습니다. 이 fixture와 완료된 설정 파일럿은 수정된 비교와 별개입니다. 각 기록의 역할은 [운영자 모델 안내](admin-setup.md#prepare)에 있습니다.

직접 Responses 호출과 **명시적으로 고정한 `gpt-6-luna` 프롬프트 에이전트 v2**는 **이 환경에서 HTTP 500**을 반환했습니다. 공급자 문제가 해결될 때까지 검증된 `gpt-4.1-mini` 에이전트를 유지합니다. 이 환경의 런타임 검증 실패이지 모델 전체가 어디서나 미지원이라는 주장이 아닙니다. 카탈로그 표시는 런타임 증거가 아닙니다.

기존 `gpt-4.1-mini` 모델 버전의 Azure 사용 중단 예정일은 **2027-04-14**입니다. 공개 문서의 **Deprecated** 표시는 신규 구독의 사용이 제한될 수 있다는 의미이므로 보편적 사용 가능성을 가정하지 말고 실제 계정을 확인합니다. 별도 Optimizer 생성 모델은 [공식 허용 모델 목록](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)을 따릅니다.

<figure class="portal-shot" id="portal-evaluation-criteria">
<img src="../web/assets/portal/en/16-evaluation-criteria.png" alt="Relevance와 TaskAdherence 및 명시적 Judge 모델을 설정하는 Foundry 평가 화면. 한국어 실행 결과가 아님" width="1440" height="1000" loading="lazy">
<figcaption><strong>각 지표의 척도 확인.</strong> 영문 리허설 화면입니다. Relevance는 임계값 4, TaskAdherence는 이진 통과값 1입니다. 두 평가기만 선택하고 Model: Judge model도 확인합니다. <a href="../web/assets/portal/en/16-evaluation-criteria.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**완료 신호:** Relevance **1–5점·임계값 4**, TaskAdherence **이진 0/1·통과값 1**, query 전용 입력, 검증된 Judge, 생성 매핑과 서비스 버전 한계가 기록되어 있습니다. 설정이 다르면 지표·모델을 조용히 바꾸지 말고 제출 전에 수정합니다.

<p class="step-next no-print"><a href="#baseline" data-next-step>다음: 03. Foundry Evaluation 실행 →</a></p>

## 03. Foundry Evaluation 실행 {#baseline}

<div class="lab-concept" aria-label="03 학습 목표">
<p><strong>무엇:</strong> 실제 Microsoft Foundry 관리형 에이전트 평가입니다. <strong>왜:</strong> 설정과 모델 연결 확인은 업무 성능 측정이 아닙니다. <strong>어떻게:</strong> 정확한 계약을 검토하고 한 번 제출한 뒤 실제 evaluation/run ID로 완료 상태를 확인합니다.</p>
</div>

새로 승인된 한국어 실습에서는 운영자의 **수정된 비교용 평가**를 [직접 에이전트 평가](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent)의 **Review**에서 확인합니다. 영어 **`contoso-en-learning-loop`**는 이미 포털 제출됐으므로 기록된 run을 열고 다시 제출하지 않습니다. 이전 파일럿과 분리하며 영어 제출을 한국어 실행으로 표시하지 않습니다.

| 검토 항목 | 필수 값 |
|---|---|
| 대상 | 운영자가 준비한 **`contoso-eval-ko`**, **구성 변경 전에 Pin currently latest로 고정한 버전 `1`** |
| 범위·빈도 | Individual turns / One time |
| 데이터 | 등록한 한국어 dev12 데이터셋과 기록된 버전·해시 |
| 에이전트 구성 | `query`만 입력, custom prompt override 없음 |
| 기준·Judge | **Relevance 임계값 4, TaskAdherence 이진 통과값 1**(범용 Threshold가 보이면 1), 생성 매핑과 **`lab-judge-luna-dea3cec5`** |
| Evaluation name | 한국어는 운영자가 지정한 별도 수정 정의. 실제 영어 최종 루프 정의는 **`contoso-en-learning-loop`**이며 파일럿 이름을 사용하지 않음 |

<figure class="portal-shot" id="portal-evaluation-review">
<img src="../web/assets/portal/en/17-evaluation-review.png" alt="고정 에이전트 버전, 기존 데이터셋, 평가 기준을 확인하는 Foundry Review 화면. 한국어 실행 결과가 아님" width="1440" height="1000" loading="lazy">
<figcaption><strong>제출 전 검토.</strong> 영문 UI·영문 데이터 리허설 화면; 한국어 실행 결과가 아님. 수정된 정의 이름·고정 Agent·데이터셋·Relevance 4·TaskAdherence 이진 통과값 1·Judge를 확인합니다. 파일럿의 이전 설정은 수정 계약이 아니며 검토 화면도 실행 증거는 아닙니다. <a href="../web/assets/portal/en/17-evaluation-review.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

최종 동작은 **Submit**이며 승인된 기준선을 한 번만 제출합니다. 아래 영어 제출은 이미 존재하므로 중복 제출하거나 보존된 파일럿을 고쳐 쓰지 않습니다.

**완료된 정식 영어 포털 기준선:** **`contoso-en-learning-loop`**, evaluation `eval_94feef6f6f644fabb22a5680f5f24fb1`, run `evalrun_cde9948ac9d946929661bc3d9e60432a`입니다. HTTP 201 제출 이후 실제 완료를 확인했습니다. `contoso-eval-en` 고정 v1, `contoso-eval-en-dev12` v1, Relevance 임계값 4, TaskAdherence 이진 통과값 1, 동일한 `gpt-6-luna` Judge를 사용한 기준선이며 후보 결과가 아닙니다.

**EVALUATION 상세**의 **Raw JSON**과 **Evaluation runs**에서 정의·run ID, URL, 제출 시각을 기록합니다. 과거 파일럿은 [운영자 기록](admin-setup.md#bootstrap)에 별도로 남깁니다. 보이는 Add run 후보 마법사는 현재 실패하므로 반복하지 말고 06단계를 사용합니다.

**완료 신호:** 실제 실행 페이지에 **Completed**가 표시되고 결과를 열 수 있습니다. 이때도 실패·오류·누락을 포함해 **전체 12건**을 확인합니다. 실패하거나 부분 완료한 실행은 기록에서도 그대로 남기며 실행 완료를 자동 품질 통과로 해석하지 않습니다.

접근·모델 지원·채점에 실패하면 ID와 오류를 유지하고 [강사의 복구 안내](facilitator.md#resume)에 따라 후속 단계를 미실행으로 표시합니다. 실패한 관리형 평가를 작성된 점수로 대체하지 않습니다.

<p class="step-next no-print"><a href="#analyze" data-next-step>다음: 04. 점수와 이유 읽기 →</a></p>

## 04. 점수와 이유 읽기 {#analyze}

<a id="iq"></a>
<a id="score-rubric"></a>
<a id="worked-evaluation"></a>

<div class="lab-concept" aria-label="04 학습 목표">
<p><strong>무엇:</strong> 지표별 점수와 행별 설명입니다. <strong>왜:</strong> 평균은 정책 오류나 누락된 답변을 숨길 수 있습니다. <strong>어떻게:</strong> 두 평가자 요약을 읽고 실패 또는 최저점 사례와 잘한 사례를 비교합니다.</p>
</div>

**Evaluations 실행 페이지**의 요약과 **Detailed metrics result**에서 **`Relevance.reason`**, **`TaskAdherence.reason`**을 읽습니다. 필요하면 가로로 스크롤합니다. 행의 **conversation_id → User view**는 질문·실제 JSON 응답 화면이며 **인라인 Judge 이유 패널이 아닙니다**. 평가 이유는 Detailed metrics result로 돌아가 확인합니다.

**실제 정식 영어 기준선만의 결과:** 파일럿 집계로 대체하거나 후보 결과로 표시하지 않습니다.

| 기준선 결과 | 관측 값 |
|---|---|
| 실행 | **Completed, 12행** |
| 전체 | **10 passed / 2 failed / 0 errored** |
| Relevance | **10/12 통과**, 임계값 **4** |
| TaskAdherence | **12/12 통과**, 이진값 **1** |

| 평가자마다 기록할 값 | 해석 |
|---|---|
| 전체 범위 | 유효 점수가 없는 행까지 **n = 12** |
| 채점 행/전체, 누락, 오류 | 평가 범위 확인값. 누락을 성공 사례로 바꾸거나 분모에서 조용히 제외하지 않음 |
| Relevance 결과 | **1–5점**, 임계값 **4**. 4/5점은 정확도 80%가 아님 |
| TaskAdherence 결과 | **이진 0/1: 1 = Pass, 0 = Fail**. 누락·오류 결과는 채점된 0이 아님 |
| 통과 건수와 점수 요약 | Relevance와 TaskAdherence를 각각 보고하며 새로운 정확도 지표로 합치지 않음 |
| 행별 이유 | 실제 답변·참고 자료와 대조할 평가자의 설명 |

<figure class="portal-shot" id="portal-evaluation">
<img src="../web/assets/portal/en/18-evaluation-results.png" alt="정식 영어 기준선을 확인하는 Foundry 평가 요약과 Detailed metrics result. 한국어 실행 결과가 아님" width="1440" height="1000" loading="lazy">
<figcaption><strong>정식 기준선 읽기.</strong> 영문 UI·영문 데이터 리허설 화면; 한국어 실행 결과가 아님. 기록된 run ID와 대조합니다. 전체 12행 중 통과 10·실패 2·오류 0, Relevance 10/12·이진 TaskAdherence 12/12입니다. 이유는 Detailed metrics result에서 읽으며 후보 결과와 구분합니다. <a href="../web/assets/portal/en/18-evaluation-results.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**실패 또는 최저점 사례를 최소 하나**, 그리고 존재한다면 **잘한 사례 하나**를 선택합니다. 각 사례에서 **실제 질문 → 실제 답변 → 평가 점수·이유 → 정책 `context`와 파싱한 `ground_truth` 참고 답변**을 연결합니다. 잘한 사례가 없으면 만들지 말고 없다고 보고합니다.

구체적인 도메인 행동을 봅니다. 맞는 정책 발효일을 적용했는가? 정말 필요한 정보를 확인했는가? 근거 정책을 인용했는가? 실제 하지 않은 승인이나 실행을 완료했다고 말했는가? 모범 응답과 글자가 완전히 같아야 하는 것은 아닙니다.

**정식 v1 기준선에서 Relevance가 실패한 두 사례:** TaskAdherence는 둘 다 통과했습니다. 후보의 회귀 결과가 아닙니다.

| 사례 | 관측된 답변과 참고 자료의 차이 |
|---|---|
| `atlas-dev-001` | 구독 축소 안내가 모호했으며 참고 답변은 명시적인 추가 확인을 요구함 |
| `atlas-dev-011` | 문서화되지 않은 기능을 미확인이라고 정직하게 설명했지만 Relevance는 불완전하다고 판단함 |

실제 이유와 참고 정책을 함께 읽습니다. **Judge 점수만 높이려고 정책 사실을 바꾸거나 정당한 불확실성을 근거 없는 확신으로 바꾸지 않습니다.**

<figure class="portal-shot" id="portal-evaluation-case">
<img src="../web/assets/portal/en/19-evaluation-case.png" alt="평가 행 conversation_id에서 연 User view의 atlas-dev-001 질문과 실제 JSON 응답. Judge 이유 패널이나 한국어 결과가 아님" width="1440" height="340" loading="lazy">
<figcaption><strong>conversation_id → User view: 실제 응답 확인.</strong> 영문 리허설의 atlas-dev-001 질문과 JSON 응답입니다. 채점 이유는 <strong>Detailed metrics result</strong>로 돌아가 <code>Relevance.reason</code>·<code>TaskAdherence.reason</code>에서 확인하고 참고 정책과 대조합니다. <a href="../web/assets/portal/en/19-evaluation-case.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**한계:** Relevance와 TaskAdherence는 유용하고 간결한 기준이지만 모든 정책·안전성을 인증하지는 않습니다. 모든 평가자가 `context`나 `ground_truth`를 사용하는 것은 아닙니다. 해당 열은 지원되는 참고 평가와 사람 검토용으로 남깁니다. 평가자 두 개를 선택했다고 모든 응답 계약 규칙을 검사했다고 주장하지 않습니다.

<p class="share-checkpoint" id="share-baseline"><strong>공유:</strong> 실제 run ID, n = 12, 지표별 채점 범위·통과 건수, 문제 문장 하나와 좋은 답변 하나를 설명합니다. 어떤 지시 행동을 왜 개선하고 싶은지 말합니다.</p>

**완료 신호:** 실제 답변과 이유로 개선 가설을 설명하며 오류도 드러낼 수 있습니다. 실패가 관측되지 않았다면 최저점 사례를 사용해 그 사실을 정직하게 보고합니다. 학습 예시를 만들려고 기준선을 약화하지 않습니다.

<p class="step-next no-print"><a href="#optimize" data-next-step>다음: 05. Agent Optimizer로 지시 개선 →</a></p>

## 05. Agent Optimizer로 지시 개선 {#optimize}

<a id="tune"></a>

<div class="lab-concept" aria-label="05 학습 목표">
<p><strong>무엇:</strong> 지시만 개선하는 Agent Optimizer 후보 하나입니다. <strong>왜:</strong> 바꾸는 대상을 제한해야 이후 비교를 해석할 수 있습니다. <strong>어떻게:</strong> 에이전트 모델·도구·데이터·Judge를 유지하고 지시 차이를 살핀 뒤 별도 실습 버전을 만듭니다.</p>
</div>

**실제 영어 작업 성공:** `opt_e44bcf5701a348deb62a1cd4f9cb3910`, **후보 1개**, 지시 전용, 같은 데이터셋, `gpt-5.5` 생성, `gpt-6-luna` Judge, 모델 비교 없음입니다. Optimizer UI는 **0.635 → 0.646**, **표시된 변화 +0.010**, **보고 토큰 264,260**입니다. 직접 후보 평가 점수가 아니므로 표시값으로 다른 변화량을 재계산하거나 작업을 다시 제출하지 않습니다.

**Build → Agents → `contoso-eval-ko` → Optimize Preview**를 엽니다. 처음에는 **Optimize my agent → Agent**를 고르며 **Cost**는 선택하지 않습니다. 작업이 생긴 뒤에는 **Optimize → Agent**로 표시될 수 있습니다. 첫 화면의 세금 에이전트 벤치마크는 **제품 예시**이지 Contoso 결과가 아닙니다.

**Create an optimization run**에서 [공식 프롬프트 에이전트 Optimizer 절차](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent)에 따라 설정합니다.

| 설정 | 정확한 실습 선택 |
|---|---|
| Agent version | 직접 Evaluation에서 사용한 고정 기준선 **`contoso-eval-ko` 버전 `1`** |
| Choose targets | **Model** 해제, **Instruction only** 선택, **Tool description 끄기** |
| Max candidates | **1**. Model만 선택하면 비활성화될 수 있으므로 먼저 Model을 해제 |
| Optimization model | **`lab-planner-dea3cec5`**, **`gpt-5.5` / `2026-04-24`** |
| Evaluation model | **`lab-judge-luna-dea3cec5`**, 직접 Evaluation에서 사용한 동일한 검증 `gpt-6-luna` Judge |
| 모델 비교 | 끄기. 개선 대상 에이전트 모델을 바꾸지 않음 |

<figure class="portal-shot" id="portal-optimizer-target">
<img src="../web/assets/portal/en/07-optimizer-target.png" alt="지시만 개선하고 후보 하나 및 별도 최적화·평가 모델을 선택한 Agent Optimizer 설정. 한국어 실행 결과가 아님" width="1210" height="968" loading="lazy">
<figcaption><strong>후보 수보다 대상 선택이 먼저입니다.</strong> 영문 UI·영문 데이터 리허설 화면; 한국어 실행 결과가 아님. Instruction only는 모델 변경을 실험에서 제외합니다. Optimization model은 지시를 만들고 Evaluation model은 응답을 채점합니다. <a href="../web/assets/portal/en/07-optimizer-target.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**Next → Select dataset and criteria**에서 기준선과 **같은 `contoso-eval-ko-dev12` 데이터셋·버전**을 선택합니다. Generate data나 수정한 업로드를 사용하지 않고 같은 Judge와 정확히 Relevance·TaskAdherence를 유지합니다.

Optimizer **Criteria**에 **No custom evaluators available**이 보이면 **Custom only를 OFF**로 바꾸거나 **View built-in evaluators**를 누릅니다. 평가자 행을 선택하면 **Configure...** 대화상자가 열립니다. **Relevance Threshold 4**, **TaskAdherence Threshold 1**을 설정하고 각각 **Apply**합니다. TaskAdherence는 이진 통과값 1이며 필터를 우회하려고 사용자 정의 평가자를 만들지 않습니다.

<figure class="portal-shot" id="portal-optimizer-data">
<img src="../web/assets/portal/en/08-optimizer-dataset.png" alt="기존 영어 dev12 데이터셋을 사용하는 Agent Optimizer 데이터·기준 선택 화면. 한국어 실행 결과가 아님" width="1210" height="968" loading="lazy">
<figcaption><strong>등록한 데이터셋 재사용.</strong> 영문 UI·영문 데이터 리허설 화면; 한국어 실행 결과가 아님. 자신의 데이터셋 버전과 12건 범위를 확인합니다. 5행 미리 보기가 전체 행 수를 바꾸지는 않습니다. <a href="../web/assets/portal/en/08-optimizer-dataset.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

새로 승인된 작업만 검토 후 한 번 제출합니다. 기록된 영어 작업은 기존 ID로 확인하며 승인 범위에서 **최대 60분** 기다립니다. 작업 하나에서도 여러 내부 호출이 발생하므로 무료 모델 요청 하나가 아닙니다. 차단되거나 대기 한도를 넘으면 상태를 기록하고 중복 제출하지 않습니다.

성공한 작업의 **original과 candidate**, **평가기별 결과**, **View changes**를 읽습니다. Optimizer의 **0–1 순위 점수**는 Relevance의 1–5점이나 통과율과 다릅니다. 순위 점수 상승이 정책 개선이나 직접 재평가를 대신하지 않습니다.

<figure class="portal-shot" id="portal-optimizer-results">
<img src="../web/assets/portal/en/09-optimizer-results.png" alt="원본·후보 결과와 평가자 상세 및 후보 조작을 보여 주는 Agent Optimizer 화면. 한국어 실행 결과가 아님" width="1440" height="1000" loading="lazy">
<figcaption><strong>후보의 근거 읽기.</strong> 영문 UI·영문 데이터 리허설 화면; 한국어 실행 결과가 아님. 실제 job/candidate ID와 평가자별 결과를 확인합니다. 추천이 개선 보장이나 운영 승인은 아닙니다. <a href="../web/assets/portal/en/09-optimizer-results.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-optimizer-diff">
<img src="../web/assets/portal/en/10-optimizer-changes.png" alt="원본과 후보 지시를 비교하는 Agent Optimizer View changes 화면. 한국어 실행 결과가 아님" width="1038" height="622" loading="lazy">
<figcaption><strong>지시 차이 확인.</strong> 영문 UI·영문 데이터 리허설 화면; 한국어 실행 결과가 아님. 정책 판단·추가 질문·권한 경계와 자신의 한국어 응답 계약이 유지되는지 확인합니다. 긴 지시가 항상 더 좋지는 않습니다. <a href="../web/assets/portal/en/10-optimizer-changes.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

같은 모델·도구·연결·응답 계약을 유지합니다. 내보낸 후보 설정에 도구가 빠져 있다고 기존 도구를 제거하지 않습니다. 지시 외의 변경이 제안되면 조건 불일치로 보고하며 통제된 개선이라고 주장하지 않습니다.

**실제 Promote로 `contoso-eval-en` v2를 만들고 지시 일치·모델·지식 도구 불변을 확인했습니다.** 활성 버전 변경은 **모든 채널에 영향**이 있어 **격리된 미게시 실습만 허용하고 운영 환경 승격은 금지**합니다. HOLD 후 활성 v1으로 복원했으며 v2와 평가 근거는 남아 있습니다. 재승격하거나 삭제하지 않습니다.

<p class="share-checkpoint" id="share-optimizer"><strong>공유:</strong> 어떤 지시가 바뀌었고 어떤 실패를 줄일 수 있으며 무엇이 나빠질 수 있나요? Optimizer 내부 결과는 검증할 후보를 고르는 근거이며 다음 직접 Evaluation을 대신하지 않습니다.</p>

**완료 신호:** 실제 영어 작업 성공과 검증된 실습 v2가 있습니다. 별도 네이티브 SDK 평가도 06단계 기록대로 완료됐으며 승격·Optimizer UI 점수는 운영 승인이 아닙니다.

<p class="step-next no-print"><a href="#decision" data-next-step>다음: 06. 재평가·비교·종료 →</a></p>

## 06. 재평가·비교·종료 {#decision}

<a id="review"></a>
<a id="operate"></a>
<a id="cleanup"></a>

<div class="lab-concept" aria-label="06 학습 목표">
<p><strong>무엇:</strong> 기존 정의 안에서 v2를 평가하는 실제 Foundry 관리형 run입니다. <strong>왜:</strong> 포털 후보 폼이 제출 전에 실패합니다. <strong>어떻게:</strong> Azure AI Projects/OpenAI Evals SDK 명령 하나를 실행하고 Foundry 포털에서 원격 run을 비교합니다.</p>
</div>

**실제 포털 차단:** Add run → Pin v2 → Individual turns 뒤 **Configure agents: Config required → Add custom prompt / User prompt**가 나타났습니다. `{{item.query}}`를 넣어도 Submit에서 **`Unable to create data source configuration from item schema`** 클라이언트 오류가 발생했습니다. **이 시도로 원격 후보 run은 제출되지 않았습니다.** 새 평가 정의를 만들어 우회하지 않습니다.

저장소 루트의 bash/zsh/WSL2에서 아래 **네 자리표시자를 모두 교체**합니다. 프로젝트 endpoint·구독은 운영자에게 받고, 평가·기준선 실행 ID는 **자신의 기준선** 포털 URL 또는 **Raw JSON**에서 복사합니다. 한국어 실습에는 한국어 실행 ID를 사용하며, 이 가이드의 영문 리허설 ID를 그대로 복사하지 않습니다.

```bash
export AZURE_AI_PROJECT_ENDPOINT="OPERATOR_PROJECT_ENDPOINT"
export AZURE_SUBSCRIPTION_ID="OPERATOR_SUBSCRIPTION_ID"
export FOUNDRY_EVALUATION_ID="YOUR_EVALUATION_ID"
export FOUNDRY_BASELINE_RUN_ID="YOUR_BASELINE_RUN_ID"
```

**사전 준비:** `source .venv/bin/activate`로 준비된 venv를 활성화하고 `python -m pip install -r requirements.lock`으로 설치한 뒤 `az login`과 [계정·구독 확인](admin-setup.md#sdk-prerequisites)을 마칩니다. 운영자가 helper를 제공하며 다른 계정이나 미완료 준비 상태로 실행하지 않습니다.

**SDK 작업은 이 명령 하나입니다.** 기준선 `data_source`와 기존 평가 기준을 재사용하고 run 입력의 대상 버전만 바꿉니다. 같은 모델·도구를 검증하고 **동일 evalID 아래 실제 Foundry 평가 run**을 제출합니다. **로컬 Judge나 별도 클라우드 채점 구현이 아닙니다.**

```bash
python scripts/add_foundry_eval_run.py --endpoint "$AZURE_AI_PROJECT_ENDPOINT" --subscription "$AZURE_SUBSCRIPTION_ID" --evaluation "$FOUNDRY_EVALUATION_ID" --baseline "$FOUNDRY_BASELINE_RUN_ID" --version 2 --name candidate-v2 --out .lab/foundry-evaluations/candidate-v2.json
```

최초 제출은 비공개 **receipt**를 저장합니다. 동일 명령·`--out` 경로를 반복하면 같은 run만 조회합니다. 로컬 receipt가 없어도 같은 이름의 원격 run이 있으면 중복 제출하지 않고 중단합니다. 기존 run을 열거나 원래 receipt를 복구하며, 유리한 결과를 얻으려고 이름·경로·평가 정의를 바꾸지 않습니다.

**검증된 영어 SDK 결과:** 같은 **`eval_94feef6f6f644fabb22a5680f5f24fb1`** 아래 후보 run **`evalrun_f3b710fc835d444fb8aa0d2bb7797bdf`**, `contoso-eval-en` **v2**가 **Completed, 12행, 11 passed / 1 failed / 0 errored**입니다. v1은 **10 passed / 2 failed / 0 errored**였습니다. helper가 같은 데이터셋·평가자·Judge·모델·도구를 확인했으며 지시·버전만 바뀌었습니다. Optimizer 내부 점수가 아닌 실제 Foundry run입니다.

영어는 **Build → Evaluations → `contoso-en-learning-loop` → Evaluation runs**에서 두 run 체크박스를 선택해 **Compare runs**를 엽니다. **Baseline 드롭다운에서 원래 `contoso-eval-en`을 명시적으로 선택합니다.** 기본값은 처음 선택한 행이며 실제로 `candidate-v2`였으므로 방향·검정을 읽기 전에 확인합니다. 한국어는 별도 정의의 원래 v1을 고릅니다. 비공개 루브릭 버전 고정은 여전히 미입증입니다.

| 실제 비교, n = 12 | 원래 `contoso-eval-en` v1 | `candidate-v2` |
|---|---|---|
| 전체 기준 통과 / 실패 / 오류 | 10 / 2 / 0 | 11 / 1 / 0 |
| Relevance 통과; 평균(1–5) | 10/12; **4.4167** | 11/12; **4.3333** |
| TaskAdherence 통과; 이진 평균 | 12/12; **1.0** | 12/12; **1.0** |
| Relevance 행 1 / 2 / 6 / 11 | 3 / 5 / 5 / 3 | 4 / 4 / 4 / 3 |
| 지연 p50 (ms) | 5,891.09 | 7,287.52 |
| 지연 p95 (ms) | 8,817.33 | 16,038.35 |
| Agent 토큰 | 35,187 | 43,751 |

<figure class="portal-shot" id="portal-evaluation-comparison">
<img src="../web/assets/portal/en/20-evaluation-comparison.png" alt="동일한 데이터셋·평가 설정의 기준선과 후보를 비교하는 Foundry Evaluations 화면. 한국어 실행 결과가 아님" width="1440" height="520" loading="lazy">
<figcaption><strong>실제 네이티브 비교.</strong> 영문 UI·영문 데이터 리허설 화면; 한국어 실행 결과가 아님. 처음 선택된 candidate-v2 대신 <strong>Baseline → contoso-eval-en</strong>을 고릅니다. PairedTTest는 두 지표 모두 Inconclusive이며 평균 하락·지연·토큰 증가 때문에 채택은 HOLD입니다. <a href="../web/assets/portal/en/20-evaluation-comparison.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**결정 실행: 채택 HOLD, 활성 버전 1로 복원.** Compare에서 원래 Baseline을 명시 선택한 뒤 이 실습에서 원본을 유지하려면 **Agent Details → Agent configuration → Active version → Edit → Version 1**을 사용하며 운영자가 이미 완료했습니다. **후보 v2·두 평가 run·receipt는 삭제하지 않고 보존합니다.** 평균 하락·행별 회귀·지연·토큰 증가·Inconclusive는 전반적 개선을 입증하지 않으며 점수 때문에 정책 사실을 바꾸지 않습니다.

<p class="share-checkpoint" id="share-optimized"><strong>종료 설명:</strong> 통과 한 건 증가뿐 아니라 행 2·6 회귀, 평균 하락, 지연·토큰 증가, Inconclusive 검정으로 HOLD를 설명합니다. Optimizer +0.010이나 네이티브 통과 건수만으로 판단하지 않습니다.</p>

**완료 신호:** 실제 run ID, 측정된 상충 관계, HOLD 결정이 기록되어 있습니다. 추가 검토와 새 대표 사례는 다음 승인된 개선 주기의 과제이지 추가 필수 실습이나 유리할 때까지 반복하는 평가가 아닙니다.

dev12 재사용은 통계적 유의성·운영 승인의 근거가 아닙니다. **운영용 Publish는 하지 않았고 운영 채널·트래픽도 구성하지 않았습니다.** Foundry는 Publish 없이도 **RBAC-only Responses/preview endpoints**를 자동 제공하므로 미게시를 endpoint 부재로 해석하지 않습니다.

<a id="troubleshooting"></a>
<a id="sources"></a>

**종료:** 실제 run/job/version 참조, 데이터셋 버전·해시, 관측한 실패와 남은 차단 사유를 운영자에게 전달합니다. 지속 비용과 승인된 정리의 책임자를 정합니다. 브라우저를 닫아도 과금은 멈추지 않습니다. 승인된 합성 예시와 가림 처리한 요약만 공유하며 자격 증명이나 비공개 환경 파일은 공유하지 않습니다.

[데이터 계약](../data/README.md) · [강사·복구 안내](facilitator.md#resume) · [운영자 인수](admin-setup.md#handoff) · [실측 검증·출처](verification.md)
