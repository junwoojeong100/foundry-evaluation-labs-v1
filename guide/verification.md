# 검증 기록과 한계 · Foundry Evaluation

**[최신 결과 JSON](../evidence/latest.json)**은 현재 가이드의 문서 검사와 실제 영문 리허설을 구분해 기록합니다. 핵심 실습은 **Foundry Evaluation → Agent Optimizer → 같은 기준으로 재평가**입니다. 공개 벤치마크 점수가 아니라 같은 Contoso 업무 질문으로 무엇이 바뀌었는지 확인합니다.

## 확인 범위 {#local}

| 대상 | 확인 내용 |
|---|---|
| 데이터 | 영어·한국어 원본을 분리하며, 각 언어의 dev 12건만 이번 학습 루프에 사용 |
| 실제 평가 | Foundry의 관리형 평가 정의·실행 ID, 전체 12개 결과, 항목별 점수·이유·오류 |
| Optimizer | 실제 instruction-only 작업 1개·후보 1개, 원본/후보 지시 diff |
| 재평가 | 같은 평가 정의·데이터 버전·평가기 설정·Judge·에이전트 모델·도구, 지시와 버전만 변경 |
| 포털 | 사용자 인증 후 같은 실습 테넌트의 Playwright Headless, 영문 UI와 영문 데이터 |
| 배포 문서 | 한·영 HTML·인쇄본·PDF, 언어 전환·모바일·로컬 링크·복사·읽음 기록 |

문서 검사의 `PASS`는 Azure 품질 합격이나 운영 승인을 뜻하지 않습니다. 한국어 가이드는 같은 절차를 설명하지만, 아래 수치는 **영어 데이터로 실제 실행한 결과**이지 한국어 실행 결과가 아닙니다.

## 실제 관리형 평가 결과 {#status}

새 전용 North Central US 환경에서 준비한 `contoso-eval-en`의 버전 1과 2를 평가했습니다.

| 지표 | 원본 v1 | 후보 v2 |
|---|---:|---:|
| 평가 사례 | 12 | 12 |
| 모든 평가 항목을 통과한 사례 | 10/12 | 11/12 |
| Relevance 통과, 기준 4/5 | 10/12 | 11/12 |
| Relevance 평균, 1–5 척도 | 4.42 | 4.33 |
| TaskAdherence 통과, 이진 Pass/Fail | 12/12 | 12/12 |
| 실행 오류 | 0 | 0 |
| 에이전트 p50 지연 | 5.89초 | 7.29초 |
| 에이전트 p95 지연 | 8.82초 | 16.04초 |
| 관측 에이전트 토큰 | 35,187 | 43,751 |

**판단은 채택 보류입니다.** 통과 사례는 한 건 늘었지만 평균 Relevance는 하락했고 지연·에이전트 토큰은 증가했습니다. 포털의 **Compare runs → PairedTTest**도 두 지표 모두 **Inconclusive**로 표시했습니다. 작은 합성 dev 표본 한 번으로 유의미한 개선이나 일반화를 주장하지 않습니다. 전용 실습 에이전트의 활성 버전은 **1로 복원**했고 후보 2와 비교 근거는 남겼습니다.

실제 평가 정의는 `eval_94feef6f6f644fabb22a5680f5f24fb1`입니다. 원본 실행은 `evalrun_cde9948ac9d946929661bc3d9e60432a`, 후보 실행은 `evalrun_f3b710fc835d444fb8aa0d2bb7797bdf`입니다. 서비스 결과를 로컬 자체 Judge 점수로 대신하지 않았습니다.

Optimizer 작업 `opt_e44bcf5701a348deb62a1cd4f9cb3910`은 성공했고, 서비스 화면의 순위 점수는 약 **0.635 → 0.646**, 표시 변화는 **+0.010**입니다. 이는 Optimizer 내부의 0–1 집계로, 위 별도 Foundry 재평가의 통과율·평균과 같은 수치가 아닙니다. 작업이 보고한 총 토큰은 **264,260**이며 실제 청구액은 별도로 확인해야 합니다.

## 모델 역할과 실행 중 발견한 문제 {#models}

| 역할 | 이번에 확인한 모델 | 근거·제한 |
|---|---|---|
| 에이전트 | `gpt-4.1-mini` · `2025-04-14` | 기존에 정상 호출된 구성을 유지. `gpt-6-luna`의 Responses·에이전트 호출은 이 환경에서 HTTP 500이어서 성공으로 간주하지 않음 |
| Foundry 평가 Judge | `gpt-6-luna` · `2026-09-22` | Chat Completions와 실제 관리형 평가에서 사용 확인 |
| Optimizer 생성 모델 | `gpt-5.5` · `2026-04-24` | 현재 [공식 최적화 모델 목록](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)에 `gpt-6-luna`가 없어 유지 |

카탈로그 표시와 실제 호출 성공은 다릅니다. HTTP 500을 해당 모델의 전역 미지원으로 일반화하지 않습니다. `gpt-4.1-mini`의 [공식 종료 예정일](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule)은 **2027-04-14**이며, 신규 구독은 사용 제한을 받을 수 있으므로 운영자는 수업 전에 실제 지원을 확인해야 합니다.

실습을 실행하며 다음을 수정하거나 명시했습니다.

- **TaskAdherence는 1–5가 아니라 이진 0/1·Pass/Fail**입니다. 처음 일반 임계값 UI를 확인한 실행은 설정 점검용으로 따로 보존하고, 비교 본 실험은 Relevance 4·TaskAdherence 1로 시작했습니다. 결과를 보고 기준을 낮추거나 첫 실행을 덮어쓴 것이 아닙니다.
- **포털 Add run의 item-schema 오류:** `Unable to create data source configuration from item schema`가 발생했습니다. 가이드에 제공한 `scripts/add_foundry_eval_run.py`로 **같은 Foundry 평가 정의와 데이터**에 후보 실행을 추가했습니다. 이는 공식 SDK로 제출한 실제 관리형 평가이지 로컬 채점이 아닙니다.
- **정직한 불확실성도 낮은 Relevance를 받을 수 있음:** `atlas-dev-011`은 미확인 기능에 확답하지 않아 TaskAdherence는 통과했지만 Relevance는 3점이었습니다. 높은 점수를 얻으려고 없는 정책·기능을 단정하지 말고, 평가 이유와 자사 기준을 함께 검토해야 합니다.
- **리소스 그룹의 별도 정책 실패:** 실습 ARM 배포는 성공했습니다. 별도 조직 정책 배포는 조직 관리 로그 대상이 없어 실패했으며, 공유 정책을 수정하거나 그 실패를 숨기지 않았습니다.

## 보존·삭제·공개 경계 {#checks}

현재 가이드에서 제외한 학습 실습의 전용 작업 2개, 학습 모델·체크포인트, 모델 배포, 업로드 파일 4개와 결과 파일 2개를 삭제하고 부재를 확인했습니다. 해당 로컬 실행·로그 파일 202개도 삭제했습니다. 공용 모델·Foundry 프로젝트·Search와 현재 평가 근거는 유지했습니다. 이미 발생한 요금이 소급 취소되는 것은 아닙니다.

원본 평가 응답과 삭제 확인서는 비공개로 관리합니다. 공개 배포에는 인증 상태·쿠키·토큰·승인 파일·서명된 다운로드 URL을 넣지 않습니다. Git 이력과 Azure의 일반 활동·청구 기록을 삭제했다는 주장은 하지 않습니다.

## 출처 {#sources}

Contoso Atlas Cloud의 정책·질문·참조 응답은 합성 자료이며 실제 고객 데이터나 공급자 약관이 아닙니다. 이전 설계 참고는 [보관 저장소의 고정 커밋][source-workshop]입니다.

실제 화면의 출처·가림·치수·해시는 [영문 촬영 기록](../web/assets/portal/en/captures.json), Microsoft 아이콘·포털 화면의 사용 범위는 [NOTICE](../web/assets/NOTICE.txt)에 기록합니다. 화면의 점수·상태·데이터는 바꾸지 않고 개인정보 가림과 잘라내기만 적용합니다.

공식 절차: [Foundry 에이전트 평가](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent) · [Agent Optimizer](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent) · [평가기별 척도](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators).

## 로컬 재검증 {#update}

```bash
python scripts/build_datasets.py --language ko --check
python scripts/build_datasets.py --language en --check
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -q
```

**명령 해설:** 두 원본 데이터의 무변경 검증, 양 언어 HTML 생성, 생성물 최신 상태 확인, 로컬 자동 검사입니다. 이 명령들은 Azure 평가를 실행하지 않습니다. PDF·배포 ZIP은 별도로 갱신하고 실제 수행한 검사만 최신 JSON에 기록합니다.

[source-workshop]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/tree/93bc07e31373c4cfc278a2dc3757785946404cf2
