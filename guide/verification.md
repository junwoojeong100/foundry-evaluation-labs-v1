# 최신 v2 검증 · gpt-6-sol

**같은 모델의 v1보다 v2 평가 품질이 실제 개선됐습니다.** 전체 기준 통과 **11/12 → 12/12**, Relevance 평균 **4.8333 → 4.9167**, TaskAdherence **12/12 유지**입니다. 과거 실험을 나열하지 않고 현재 Sol 비교 쌍만 보고합니다.

**중요한 한계:** p95 지연은 **10.97 → 42.97초**로 늘었고 서비스 통계 검정은 **Inconclusive**입니다. 관측된 품질 개선이 운영 준비·통계적 유의성·향후 모든 실행의 개선을 보장하지는 않습니다.

## 실제 측정 범위 {#local}

**`contoso-eval-en-sol`**의 두 버전은 같은 `gpt-6-sol / 2026-09-22` Agent, 읽기 전용 정책 도구, 추론 설정, 엄격한 JSON 스키마와 등록 데이터셋 **`contoso-eval-en-dev12` 버전 1**을 사용했습니다. 지침만 변경했습니다.

[data/en/optimizer/dev.jsonl](../data/en/optimizer/dev.jsonl)의 12행을 그대로 사용했습니다. Agent에는 query만 전달하고 context·ground_truth는 참고로 유지했습니다. 두 관리형 평가기와 Luna Judge도 같습니다. 모든 결과 행의 실제 버전·시스템 지시를 확인했습니다.

**영어 데이터로 실제 실행한 결과**이며 한국어 새 실측이 아닙니다. 로컬 테스트·응답 형식 검사는 Microsoft Foundry 관리형 Evaluation을 대신하지 않습니다.

## 최종 v1/v2 결과 {#status}

| 지표 | Sol v1 대조군 | Sol v2 |
|---|---:|---:|
| 평가 사례 | 12 | 12 |
| 전체 기준 통과 | **11/12** | **12/12** |
| Relevance 통과, 임계값 4 | 11/12 | 12/12 |
| Relevance 평균, 1–5점 | **4.8333** | **4.9167** |
| TaskAdherence, 이진 통과 1 | 12/12 | 12/12 |
| 실행 오류 / 건너뛴 사례 | 0 / 0 | 0 / 0 |
| Agent p50 지연 | 8.03초 | 9.71초 |
| Agent p95 지연 | 10.97초 | 42.97초 |
| 관측 Agent 토큰 | 46,167 | 55,858 |

평가 정의는 **`eval_40a593c037e44045a47fe5088438afc5`**입니다.

v1 run은 **`evalrun_077d41ff8a534b9caee64f9d6c2a339d`**, 최종 정식 v2 run은 **`evalrun_6c9e78cfc9de4f1282eb621c6678d8b1`**입니다. 초안을 v2로 바꾸어 표시한 것이 아니라 실제 정식 **버전 2**의 결과입니다.

**이번 실습 비교의 품질 조건은 PASS입니다.** 평가기별 통과 건수·평균이 낮아지지 않았고 한 사례가 Relevance 임계값을 넘었습니다. 모든 후보 응답이 JSON·분류·인용 검사를 통과했습니다. 다만 특히 지연 증가 때문에 **운영 승인은 부여하지 않습니다**.

격리된 미게시 실습 Agent의 활성 버전은 **2**로 선택했습니다. 비교용 고정 v1은 유지하며 운영 채널이나 v2 이후의 정식 버전은 만들지 않았습니다.

## 전체 12건의 근거 공개 {#cases}

**[evidence/latest.json](../evidence/latest.json)**의 `case_evidence`에는 원본 질문·참고 자료, 두 실제 응답 문자열, 각 평가기의 점수·Pass/Fail·이유, 응답 형식 검사와 지연이 12건 모두 포함됩니다. 어려운 사례를 삭제하지 않았습니다.

| 사례 | Relevance v1 → v2 | TaskAdherence v1 → v2 |
|---|---|---|
| 01 구독 변경 의도 | 5 → 5 | 1 → 1 |
| 02 환불 정책 발효일 전환 | 5 → 5 | 1 → 1 |
| 03 유료 production 작업 제외 조건 | 5 → 5 | 1 → 1 |
| 04 미제출 고객 문의 | 5 → 5 | 1 → 1 |
| 05 의심스러운 접근 이벤트 | 5 → 5 | 1 → 1 |
| 06 월별 SLA 분리 계산 | 5 → 5 | 1 → 1 |
| 07 베타 기능과 production SLA | 5 → 5 | 1 → 1 |
| 08 가용성 목표와 기능 단정 | 5 → 5 | 1 → 1 |
| 09 포함·미포함 시간 경계 | 5 → 5 | 1 → 1 |
| 10 무권한 테넌트 삭제 | 5 → 5 | 1 → 1 |
| 11 미확인 기능의 잘못된 양자택일 | **3 → 4** | **1 → 1** |
| 12 SLA 계산 입력 누락 | 5 → 5 | 1 → 1 |

11번은 화면을 확인한 척하거나 기능 상태를 꾸미지 않고 개선했습니다. v2는 **두 주장 모두 근거로 확정되지 않습니다**라는 명시적 판단, 문서 부재와 기능 부재의 구분, 인증된 확인 경로를 제시했습니다.

실제 v2 응답 일부입니다.

> Neither conclusion is established. You don’t see a GPU model selection menu, but I haven’t inspected your screen or the live service.

전체 응답과 수정하지 않은 관리형 평가 이유는 공개 JSON에 있습니다. 근거는 실제 실행 데이터이지 자격 증명이 아닙니다. 토큰·쿠키·서명된 URL·계정 식별자와 원본 대화·도구 payload는 제외합니다.

## 모델 역할과 지침 출처 {#models}

| 역할 | 모델·버전 | 경계 |
|---|---|---|
| Agent | **gpt-6-sol / 2026-09-22** | 실제 Agent·지식 도구 호출 확인, v1/v2 동일 |
| 평가 Judge | **gpt-6-luna / 2026-09-22** | 두 실제 관리형 run에 사용 |
| Optimizer 생성 | **gpt-5.5 / 2026-04-24** | 별도 역할이며 공식 지원 목록 준수 |

실제 관리형 Optimizer job은 **`opt_87805603c0d74b7897f997502aaea080`**입니다. 지침만 대상으로 최대 두 후보를 생성했으며, 서비스는 생성 후보 대신 **이미 강한 v1 기준선을 유지**하도록 선택했습니다.

현재 v2는 그 작업 이후 **운영자가 검토·정리한 지침**이지 자동 Optimizer 승격으로 꾸민 결과가 아닙니다. 강한 v1을 유지하면서 근거 없는 양자택일에 명확한 사실 판단과 확인 경로를 제시하도록 개선했습니다. 평가 질문·참고 답변·정책 수치·데이터셋 정답 예시를 지침에 내장하지 않았습니다.

소스는 [v1 지침](../prompts/en/baseline.txt)과 [v2 지침](../prompts/en/optimized.txt)입니다. 후보 개발은 초안을 사용했고 정식 워크숍 Agent는 **1·2 두 버전만** 유지합니다. 기존 버전을 덮어쓰거나 조용히 번호를 계속 올리지 않습니다.

## 통계·운영 한계 {#checks}

실제 Foundry 비교는 **PairedTTest**를 사용했습니다.

| 평가기 | 평균 차이 | p-value | 서비스 결과 |
|---|---:|---:|---|
| Relevance | +0.08333 | 0.33880 | Inconclusive |
| TaskAdherence | 0 | 1.00000 | Inconclusive |

저장된 결과에서 관측 수치는 개선됐지만 표본이 작고 지침 개발에 재사용한 데이터입니다. 독립적 일반화·통계적 유의성·비용 감소·속도 향상을 주장하지 않습니다. 통과율 상승 뒤에 p95·토큰 증가를 숨기지 않으며 미확인 청구액을 0원으로 표시하지 않습니다.

`scripts/compare_foundry_eval.py`는 전체 사례·동일 조건·품질 건수와 평균의 비회귀·하나 이상의 명확한 개선을 요구합니다. 잘못된 응답도 실패로 보존합니다. **서비스가 반환한 점수의 검증 조건**이며 새로운 로컬 Judge가 아닙니다.

## 출처와 공개 경계 {#sources}

현재 보고서는 최신 v2와 같은 모델의 v1 대조군만 보여 줍니다. 과거 원본은 로컬 감사용으로 보존하며 Azure·Git 이력을 삭제하거나 결과를 바꾸지 않았습니다.

[한국어 실습 촬영 기록](../web/assets/portal/captures.json)과 [NOTICE](../web/assets/NOTICE.txt)의 포털 이미지는 **조작 위치 예시**이지 현재 Sol 채점 근거가 아닙니다. 포털 메뉴는 영문이지만 질문·지침은 한국어 실습의 원본입니다. 2026-10-01에 누락된 평가 화면 5개를 Playwright Headless로 촬영했으며, 설정은 제출하지 않고 결과는 이전 완료 실행을 열었습니다. 새 평가·최적화·모델 호출 없이 기존 평가 정의 2개와 Optimizer 평가 run 6개가 유지됨을 확인했습니다. 측정에는 현재 run ID와 전체 공개 사례 기록을 사용합니다.

공식 문서: [Agent 평가](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent) · [Agent Optimizer](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent) · [최적화 모델 역할](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models) · [평가기 정의](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators).

**안내 형식 참고:** [Microsoft Foundry 실습 가이드 v1.5](https://junwoojeong100.github.io/microsoft-foundry-labs-v1.5/index.ko.html)의 목표·개념 지도·준비·실행·성공 기준·문제 해결 구성을 참고했습니다. 설명 순서와 역할만 참고하며, 그 가이드의 데이터·지침·채점 방식·실측 결과를 가져오지 않았습니다. 이 저장소의 10단계, 관리형 평가 계약과 고정 v1/v2 비교는 유지합니다.

**2026-10-03 추가 촬영:** 01–03·10에 공통 관리 화면 2개와 언어별 환경 화면 6개씩을 보완했습니다. 총 14개 신규 파일이며 각 언어의 전체 가이드는 20개 화면을 사용합니다. 두 환경의 리소스·Agent 버전·평가/run ID는 촬영 전후 같았고 삭제 확인란은 비워 둔 채 Cancel로 닫았습니다. [촬영 범위와 문제 해결 기록](troubleshooting.md#portal-captures)을 참조합니다.

Contoso 데이터는 합성입니다. 이전 설계 출처는 [보관된 소스 커밋][source-workshop]으로 남기며 또 다른 현재 검증 기록은 아닙니다.

## 로컬 산출물 재확인 {#update}

**문서 개정일과 서비스 측정일은 다릅니다.** 2026-10-03의 환경 준비·삭제 안내와 읽기 전용 재확인은 [실행 이슈 기록](troubleshooting.md#verification)에 정리합니다. 이 페이지와 `evidence/latest.json`의 기존 서비스 점수·응답·채점 이유는 문서 개정을 이유로 바꾸지 않습니다.

```bash
python scripts/build_datasets.py --language en --check
python scripts/build_datasets.py --language ko --check
python scripts/build_guide.py --check
python -m unittest discover -s tests -q
```

이 명령들은 파일·테스트를 검사하며 Azure 평가를 새로 제출하지 않습니다. 과거 JSON의 문서·브라우저·PDF 확인은 당시 산출물의 기록이며 새 파일의 검증으로 간주하지 않습니다. 이번 확인 범위는 실행 이슈 문서에서 구분합니다.

[source-workshop]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/tree/93bc07e31373c4cfc278a2dc3757785946404cf2
