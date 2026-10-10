# 합성 한국어 평가 데이터 {#data-guide}

[데이터셋 단계](../guide/handbook.md#start) · [선택 기록표](../guide/admin-setup.md#handoff) · [English data guide](README.en.md)

## 비교에는 변경 없는 데이터셋 하나 {#start}

한국어 절차는 **[data/optimizer/dev.jsonl](optimizer/dev.jsonl)**의 **JSONL 12행**을 Microsoft Foundry 평가·agent optimizer·재평가에 사용합니다. 본인이 만든 프로젝트에서 [04의 등록 절차](../guide/handbook.md#start)로 `lab-ko-dev12` 버전 `1`을 등록합니다. 자신의 같은 실습을 재개할 때는 기록한 이름·버전·해시를 대조하여 등록을 재사용합니다.

**실행 위치:** [터미널에서 12행·해시 확인](../guide/handbook.md#dataset-check) → [Microsoft Foundry에서 업로드·선택](../guide/handbook.md#dataset-register). 로컬 확인 명령은 파일을 업로드하거나 평가를 제출하지 않습니다.
{: .execution-guide}

비교하는 동안 파일의 바이트·SHA-256·질문·참고 답변·언어를 유지합니다. 한국어와 영어 데이터는 분리하며 한 비교 안에서 섞지 않습니다.

[04의 코드 ↔ 포털 표](../guide/handbook.md#dataset-code-portal)에서 로컬 행 수·해시 확인과 실제 포털 등록을 구분합니다. [05의 원격 설정 검증 코드](../guide/handbook.md#criteria-code-portal), [09의 실제 SDK 제출 코드](../guide/handbook.md#decision-code-portal)는 같은 데이터·매핑·버전이 유지되는 과정을 보여줍니다. 읽기용 소스를 별도로 실행하지 않습니다.

## 목적과 한계 {#scope}

Contoso Atlas Cloud의 정책·질문·참고 답변은 합성 자료입니다. 실제 고객 데이터나 Microsoft·Microsoft Azure·실제 공급자의 약관이 아닙니다.

공개 벤치마크만 보는 대신 **자사 업무와 기준으로 평가**하는 방법을 익힙니다. 정책 날짜 경계, 모호성, 근거 없는 확신과 실행 완료 주장을 대표 사례로 확인합니다. dev 12건은 학습 루프의 예시이지 운영 안전·독립적 일반화의 인증이 아닙니다.

## 원본 데이터 보존 {#composition}

[data/cases.jsonl](cases.jsonl)은 100건이며 `train` 56, `validation` 12, `dev` 12, `test` 20으로 나뉩니다. 이번 워크숍은 dev12만 사용하며 나머지는 추가 필수 실습이 아닙니다.

결과를 보고 쉬운 행만 선택하거나 중복·병합하거나 참고 답변을 바꾸지 않습니다. [정책 문서 8개](knowledge/documents.json)의 `ATLAS-*` ID와 발효일을 유지합니다. 정책 연결도 본인이 [03의 준비 명령](../guide/handbook.md#agent)으로 생성합니다.

## 업로드·응답 스키마 {#schema}

JSONL 한 행에는 정확히 세 열이 있습니다.

| 열 | 형식 | 용도 |
|---|---|---|
| `query` | 문자열 | Agent에 보내는 **유일한** 입력 |
| `context` | 문자열 | 지원되는 평가기와 사례 검토용 정책 참고 자료 |
| `ground_truth` | JSON **문자열** | 구조화 참고 답변이며 생성 프롬프트가 아닙니다. |

미리 채운 `response`는 없습니다. Microsoft Foundry가 고정 Agent를 호출해 실제 응답을 얻습니다. JSON 배열로 바꾸거나 열 이름을 바꾸거나 참고 자료를 질문에 붙이거나 응답을 미리 만들지 않습니다.

참고 답변과 Agent 응답은 네 키를 사용합니다.

| 키 | 계약 |
|---|---|
| `answer` | 비어 있지 않은 한국어 문자열입니다. |
| `citations` | 근거 정책 문서의 중복 없는 고정 ID |
| `route` | `answer`, `clarify`, `escalate`, `refuse` |
| `needs_human` | 불리언, route가 `escalate`일 때만 true |

[응답 스키마](../schemas/response.schema.json)는 분류 일관성도 검사합니다. 네이티브 구조화 출력은 JSON 형식을 제한하지만 사실의 정확성을 보장하지는 않습니다. 숫자 검색 참조 ID는 정책 인용 ID가 아닙니다.

Agent는 티켓 제출·구독 변경·크레딧 승인·데이터 삭제를 실제 수행하지 않습니다. `escalate` 분류가 담당자 연락 완료를 뜻하지 않습니다. 확답을 요구해도 근거 없는 사실을 만들 수 없습니다.

## 한 번 등록하고 같은 버전 선택 {#upload}

**Microsoft Foundry → Build → Evaluations → Create → Agent**에서 명시적 기준선 버전과 **Individual turns / One time**을 선택합니다. 버전 선택으로 체크가 해제되면 대상을 다시 선택합니다.

처음에는 **Upload new dataset → Browse**로 정확한 한국어 파일을 올려 `lab-ko-dev12` 버전 `1`을 등록합니다. 재개·Optimizer·재평가는 **Existing dataset**에서 같은 이름·버전을 선택합니다. 미리 보기가 5행이어도 실제 파일·평가 범위는 12행입니다.

Codespaces 사용자는 [Explorer의 Download](../guide/handbook.md#dataset-download)로 원본 파일을 내 PC에 받은 뒤 Browse에서 선택합니다. 파일을 편집하거나 다른 형식으로 변환하지 않습니다.

custom prompt override는 비워 둡니다. 필드 매핑 화면이 나타나면 `query → query`를 사용합니다. 서비스 매핑은 **Relevance `response={{sample.output_text}}`**, **TaskAdherence `response={{sample.output_items}}`**이며 추가 JSONL 열이 아닙니다.

**Relevance 1–5점·임계값 4**, **TaskAdherence 이진 0/1·통과 1**과 같은 Luna Judge를 유지합니다. 두 평가기가 모든 참고 열을 쓰거나 모든 업무 규칙을 인증한다고 주장하지 않습니다.

## 전체 근거 비교 {#compare}

같은 모델의 v1과 v2에 대해 12건 전체의 질문·답변·평가 점수·이유를 나란히 비교합니다. 자신의 실제 run ID와 데이터 해시를 기록하여 비교 대상을 구분합니다.

helper는 질문·참고 자료와 실제 행별 Agent 버전·지시를 대조합니다. 오류·누락을 성공으로 바꾸거나 분모에서 빼지 않습니다. JSON·분류 검사는 부가 검증이며 **관리형 평가를 대신하는 로컬 Judge가 아닙니다**.

Agent optimizer 내부 순위와 별도 관리형 실행의 평균·통과율을 구분합니다. 후보 지침 전체를 검토하고 모델·도구·추론·스키마를 유지합니다. 검토한 v2를 한 번 비교하며 정식 버전을 계속 올리지 않습니다. 유지할 후보가 없으면 v1 유지 이유를 기록하고 10으로 진행합니다.

결과를 공유하기 전에 인증 정보·서명된 URL·비공개 계정 정보를 제거합니다. 오류·누락을 포함해 전체 사례를 기록합니다.

등록된 데이터셋은 `cleanup`만으로 모두 삭제되지 않습니다. 실습 후 [10의 보관·삭제 절차](../guide/handbook.md#cleanup)에서 결과를 보관하고 자신의 전용 그룹을 정리합니다. 보존이 승인된 경우에만 실제 남은 등록·평가 기록과 비용·검토일을 기록합니다. 공유·외부 자원은 삭제하지 않습니다.
