# Foundry Learning Loop Lab v1 · 한국어

**[한국어 실습](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html)** · **[English — 기본 가이드](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/)** · [English README](README.md)

**Azure를 처음 확인하는 단계부터 리소스 삭제까지 10단계로 진행합니다.** Microsoft Foundry 관리형 Evaluation과 Agent Optimizer로 자사 대표 업무의 Agent 응답을 평가·개선합니다.

> 계정·PC·권한 확인 → Foundry 생성 → 정책·Agent 준비 → 데이터셋 → 평가기 → 평가 → 분석 → 최적화 → 재평가 → 삭제 확인

Contoso 정책·질문은 합성 자료입니다. 공개 벤치마크 순위나 운영 인증이 아니라 **평가 → 학습 → 개선 → 재평가**를 익힙니다.

처음 시작하는 경우 가이드 01부터 진행합니다. Windows PowerShell과 macOS/Linux의 설치·가상환경 명령, 입력값을 찾는 위치, 비용 승인서, 실제 Agent 생성·평가 ID 조회와 완료 기준을 제공합니다. 준비된 환경은 인수표를 확인하고 중복 생성을 건너뜁니다.

시작 화면에서 실습의 정의·중요성·진행 방식·완료 산출물을 설명합니다. 각 단계는 **하는 일 → 중요한 이유 → 방법·위치 → 실제 화면과 실행 → 완료 기준**으로 읽을 수 있도록 구성합니다.

문제·해결·확인 범위는 **[실행 이슈 기록](guide/troubleshooting.md)**에 정리합니다. 이번 문서 점검의 읽기 전용 조회와 과거 유료 실측을 구분하며, 아래 수치는 신규 한국어 실행 결과가 아닙니다.

## 현재 Sol v1/v2 비교 하나

| 역할 | 확인한 모델·버전 |
|---|---|
| Agent | **gpt-6-sol / 2026-09-22** |
| Foundry 평가 Judge | **gpt-6-luna / 2026-09-22** |
| Agent Optimizer 생성 | **gpt-5.5 / 2026-04-24** |

영어 Agent는 **`contoso-eval-en-sol`**입니다. v1/v2는 변경 불가능한 Agent 전체 버전이며 이번 비교는 **지침만 다릅니다**. 모델·도구·추론·엄격한 JSON 스키마·데이터·평가기 설정은 같습니다. v1부터 강한 기준선을 사용하며 개선을 크게 보이게 하려고 약화하지 않습니다.

후보는 명시적 초안에서 개발합니다. `ensure_fixed_release`는 정식 **1·2만 허용**하고 동일 버전을 재사용하며, v3를 조용히 만들거나 기존 버전을 덮어쓰지 않습니다. 현재 [v2 지침](prompts/en/optimized.txt)과 [v1 기준선](prompts/en/baseline.txt)을 분리했습니다.

**[최신 v2 검증·v1 대조군](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/verification.html#status)** · **[전체 공개 사례 근거](evidence/latest.json)**

현재 비교 하나만 보고하며 **질문 12건, 두 실제 응답, 평가 점수·이유 전체**를 실패까지 포함해 공개합니다. 과거 원본 receipt는 로컬 감사용으로 보존하고 인증·쿠키·서명된 URL·비공개 계정 메타데이터는 공개하지 않습니다.

실제 관리형 Optimizer는 생성 후보 대신 v1을 유지하도록 선택했습니다. 현재 v2는 **해당 Optimizer 실행 이후 운영자가 검토·개선한 지침**을 별도 관리형 평가로 검증한 것입니다. 서비스가 자동 추천한 후보라고 바꾸어 표시하지 않습니다.

## 같은 데이터와 평가 기준

변경 없는 **`data/en/optimizer/dev.jsonl`**, 등록 `contoso-eval-en-dev12` 버전 `1`을 사용합니다. **12행 JSONL**은 query·context·JSON 문자열 ground_truth를 포함하며 Agent에는 query만 전달합니다. 한국어 원본은 별도로 유지합니다. 현재 공개 수치는 영어 실측이며 한국어 새 실행 결과가 아닙니다.

| 관리형 평가기 | 척도·통과 기준 |
|---|---|
| Relevance | 1–5점, 임계값 **4** |
| TaskAdherence | 이진 0/1 Pass/Fail, 통과 **1** |

SDK helper는 기존 Foundry 정의에 실제 run을 추가합니다. 원격 Judge·임계값·매핑을 확인하고 중복 제출을 막으며, 결과 행의 실제 고정 버전·지시도 검증합니다. **로컬 Judge가 아닙니다.**

`scripts/compare_foundry_eval.py`는 전체 사례 대응, 품질 통과 건수·평균의 비회귀와 하나 이상의 명확한 관측 개선을 요구합니다. 잘못된 응답을 숨기거나 미래의 확률적 결과를 보장하지 않습니다. 통계 검정, 지연·토큰 상충 관계도 별도로 보고합니다.

## 가이드

| 내용 | 한국어 | English |
|---|---|---|
| 참가자 실습 | [시작](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html) | [Start](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/index.html) |
| 운영자 준비 | [운영자](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/admin.html) | [Operator](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/admin.html) |
| 진행·복구 | [강사](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/facilitator.html) | [Facilitator](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/facilitator.html) |
| 데이터 계약 | [데이터](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/data-guide.html) | [Data](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/data-guide.html) |
| 최신 v2 근거 | [검증](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/verification.html) | [Verification](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/verification.html) |
| 실행 문제·해결 | [이슈 기록](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/troubleshooting.html) | [Issues](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/troubleshooting.html) |
| 통합 인쇄본 | [열기](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/print.html) | [Print](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/print.html) |
| PDF | [한국어](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-KO.pdf) | [English](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-EN.pdf) |

기본 언어는 영어입니다. 언어를 전환해도 대응 절·읽음 기록·테마를 유지합니다. 로그인·JavaScript 없이 열람할 수 있으며 오프라인에서는 저장소 전체의 폴더 구조를 유지합니다.

참가자 가이드의 왼쪽 목차는 주요 10단계만 표시합니다. 상세 제목과 직접 링크는 본문에 유지하며, 참고 문서의 목차는 별도로 제공합니다.

포털 그림은 **이전 촬영분의 조작 위치 예시**로 표시하며 현재 Sol 실측으로 사용하지 않습니다. 실제 측정 근거는 최신 보고서와 그 안의 run ID입니다.

영문 가이드는 `web/assets/portal/en/`, 한국어는 `web/assets/portal/`의 해당 실습 환경을 사용하며, 구독·권한의 공통 관리 화면만 `web/assets/portal/shared/`를 공유합니다. 각 언어의 전체 가이드에는 **기존 12개 + 언어별 추가 6개 + 공통 2개 = 20개**의 화면을 수록합니다. 2026-10-03에 새로 촬영한 파일은 총 14개이며 모두 Playwright Headless 캡처입니다. 생성·저장·채팅·최종 삭제 없이 기존 상태와 빈 삭제 확인 창만 읽었습니다. 기존 사진과 실측 원문은 그대로 보존합니다.

## 실행 경계

참가자 또는 승인된 운영자가 01–03에서 격리 프로젝트와 읽기 전용 정책 연결을 준비합니다. 별도 Judge 교정·governance는 필수 실습이 아닙니다. Agent는 안내하며 환불·티켓 제출·삭제·권한 부여를 실제 수행하지 않습니다.

지원 범위는 역할별로 다릅니다. 실제 Agent·도구 호출과 [지원 Optimizer 모델](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)을 확인하고 비교 도중 모델을 바꾸지 않습니다.

운영용 게시는 실습에 포함하지 않습니다. 브라우저 종료로 과금이 멈추지 않습니다. 실제 실패를 보존하며 같은 후보를 유리한 점수가 나올 때까지 반복하지 않습니다.

10에서는 결과 보관 후 삭제 대상·소유권·승인을 확인합니다. `cleanup`은 기록된 객체만 정리하며 Search·모델·그룹을 전부 삭제하지 않습니다. 전용 그룹은 별도 삭제와 `az group exists`의 `false`까지 확인하고 공유 자원은 담당자에게 인계합니다.

## 산출물 유지보수

잠금 의존성이 설치된 환경에서 실행합니다.

```bash
python scripts/build_datasets.py --language en --check
python scripts/build_datasets.py --language ko --check
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -q
```

영어 원문은 `guide/en/*.md`·`data/README.en.md`, 한국어는 `guide/*.md`·`data/README.md`입니다. HTML은 `docs/`와 `docs/ko/`에 생성합니다. 대응 절 ID·별도 언어 원본을 유지합니다.

한국어 문서·안내·오류 메시지는 ‘합니다·입니다’ 문체를 사용합니다. 과거 실측 응답·채점 이유와 평가 데이터의 원문 인용은 문체 정리를 위해 바꾸지 않습니다.

통합 인쇄본을 배경 그래픽 포함 A4 PDF로 생성하고 `requirements-verification.lock` 환경에서 `python -m scripts.verify_pdf`로 검사합니다. ZIP은 `python scripts/package_lab.py`로 다시 만듭니다. `evidence/latest.json`의 기존 서비스 실측은 보존하고, 이번 문서·브라우저·PDF 확인은 `guide/troubleshooting.md`에 기록합니다. 새 서비스 결과는 실제 실행한 경우에만 갱신합니다.

GitHub Pages는 **main 브랜치 루트**와 `.nojekyll`을 사용합니다. 루트 index.html·기존 docs/english.html은 쿼리와 절 링크를 유지하며 영어로 연결합니다.
