# Foundry Learning Loop Lab v1 · 한국어

**[한국어 실습 시작 → GitHub Pages](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#start)** · **[English](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/#start)** · [English README](README.md)

**Microsoft Foundry 관리형 Evaluation과 Agent Optimizer를 직접 사용하는 실습**입니다.

> 데이터셋 준비 → 평가기 선택 → Foundry 평가 실행 → 점수·실패 사례 확인 → 지시 최적화 → 같은 기준으로 재평가·비교

목적은 공개 벤치마크 점수만 보는 대신 **자사 데이터·업무 기준으로 평가**하는 것입니다. 가상의 Contoso 정책과 질문으로 **평가 → 실패에서 학습 → 개선 → 재평가**의 학습 루프를 경험합니다.

## 실습 시작

운영자가 수업 전에 격리된 프로젝트, 예제 에이전트, 모델 배포와 승인 범위를 준비합니다. 참가자는 기준선·Optimizer를 포털에서 실행하고, 공식 SDK helper 명령 하나로 두 번째 **Foundry 관리형 평가 run**을 만든 뒤 포털의 **Compare runs**로 비교합니다. 자체 로컬 Judge 실습으로 Foundry Evaluation을 대신하지 않습니다.

한국어는 `data/optimizer/dev.jsonl`, 영어는 `data/en/optimizer/dev.jsonl`의 **12건 전체**를 사용합니다. 개선 전후에 데이터 버전·평가기 설정·Judge·에이전트 모델·도구를 유지하고 지시와 고정 에이전트 버전만 바꿉니다.

| 평가 기준 | 해석 |
|---|---|
| Relevance | 1–5점, 통과 임계값 **4** |
| TaskAdherence | 이진 0/1 **Pass/Fail**, 통과 **1**. 5점 중 1점이 아님 |

**기본 언어는 영어이며 모든 가이드에 한국어 버전이 있습니다.** 상단 언어 전환은 대응하는 절과 읽음 기록을 유지합니다. 문서 열람에는 로그인·JavaScript가 필요 없습니다. 오프라인에서는 저장소 전체를 내려받아 `index.html` 또는 `docs/ko/index.html`을 열며 폴더를 함께 유지합니다.

## GitHub Pages 가이드

| 내용 | 한국어 | English |
|---|---|---|
| 참가자 6단계 | [실습 시작](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#start) | [Start](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/index.html#start) |
| 운영자 사전 준비 | [운영자 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/admin.html) | [Operator](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/admin.html) |
| 진행·복구 | [강사 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/facilitator.html) | [Facilitator](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/facilitator.html) |
| 데이터 계약 | [데이터 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/data-guide.html) | [Data](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/data-guide.html) |
| 실제 검증·출처 | [검증 기록](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/verification.html) | [Verification](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/verification.html) |
| 통합 인쇄본 | [한국어 인쇄본](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/print.html) | [Print](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/print.html) |
| PDF | [한국어 PDF](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-KO.pdf) | [English PDF](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-EN.pdf) |

## 확인한 모델과 결과

| 역할 | 확인된 선택 |
|---|---|
| 에이전트 | `gpt-4.1-mini` / `2025-04-14`. 이 환경의 `gpt-6-luna` Responses·Agent 호출이 HTTP 500이어서 정상 동작한 구성 유지 |
| Foundry 평가 Judge | **`gpt-6-luna` / `2026-09-22`**, 실제 관리형 기준선·후보 평가에서 사용 |
| Optimizer 생성 모델 | `gpt-5.5` / `2026-04-24`. 현재 [지원 최적화 모델 목록](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)에 `gpt-6-luna`가 없어 유지 |

기존 에이전트 모델의 [사용 중단 예정일](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule)은 **2027-04-14**이며 신규 구독은 제한을 받을 수 있습니다. 운영자는 수업 전에 실제 런타임 지원을 확인해야 합니다. 카탈로그 표시는 에이전트 호출 성공이 아닙니다.

**실제 영문 리허설:** 12건으로 Foundry 관리형 평가, 지시 전용 Optimizer 작업 하나, 같은 정의의 재평가를 수행했습니다. 모든 항목을 통과한 사례는 **10/12 → 11/12**였지만 Relevance 평균은 **4.42 → 4.33**, p95 지연은 **8.82 → 16.04초**였습니다. 포털 통계 비교도 **Inconclusive**이므로 채택은 **HOLD**이며 활성 v1을 복원하고 후보 v2는 보존했습니다.

자세한 내용은 [검증 기록](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/verification.html)과 [evidence/latest.json](evidence/latest.json)에 있습니다. 영어 데이터 결과이며 새로운 한국어 실행 결과·운영 승인·일반화 보장이 아닙니다.

## 실행 경계

- 안내 에이전트는 환불이나 업무 권한 부여를 실제 실행하지 않습니다. 운영 트래픽이 아닌 격리된 실습 에이전트만 사용합니다.
- 이 포털 버전의 **Add run**에서 item-schema 오류가 발생했습니다. 06단계의 `scripts/add_foundry_eval_run.py`는 **같은 Foundry 평가**에 데이터·기준을 유지해 run을 제출하고, ID를 기록하며 중복 제출을 방지합니다.
- 자신의 endpoint·구독·평가·기준선 run ID로 자리표시자를 교체합니다. 리허설 ID를 새 근거처럼 복사하거나 좋은 점수가 나올 때까지 재실행하지 않습니다.
- `.env`·`.lab/`·자격 증명·비공개 원본·서명된 다운로드 URL을 공개하지 않습니다. 브라우저를 닫아도 자원 비용이 멈추지 않습니다.

## 문서 유지보수

`requirements.lock`의 의존성이 설치된 저장소 루트에서 실행합니다.

```bash
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -v
```

영문 원문은 `guide/en/*.md`·`data/README.en.md`, 한국어 원문은 `guide/*.md`·`data/README.md`, 공통 UI는 `web/locales.json`입니다. HTML은 영어 `docs/`, 한국어 `docs/ko/`에 생성합니다. 대응 절 ID와 언어별 원본 데이터를 보존합니다.

각 통합 인쇄본을 배경 그래픽 포함 A4 PDF로 저장합니다. `requirements-verification.lock`의 검증 환경에서 `python scripts/verify_pdf.py docs/Foundry-Learning-Loop-Lab-KO.pdf --language ko`로 확인하고, 영어는 해당 파일명과 `--language en`을 사용합니다. 오프라인 ZIP은 `python scripts/package_lab.py`로 갱신합니다.

GitHub Pages는 **`main` 브랜치 루트**와 `.nojekyll`을 사용합니다. 루트 `index.html`과 기존 `docs/english.html`은 쿼리·절 링크를 보존해 기본 영문 가이드로 연결합니다.
