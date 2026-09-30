# Foundry Learning Loop Lab v1.1 · 한국어

[English quickstart](README.en.md) · **[실습 가이드 열기](index.html)** · [원문](guide/handbook.md)

**유창한 답과 업무에 맞는 답은 다릅니다. 먼저 틀린 답을 발견하고, 그다음 같은 Contoso 에이전트를 증거로 개선합니다.**

하나의 경로를 따릅니다.

> 작성된 오답 판단 → 무료 오프라인 DEMO → 로컬 설치 → 새 NCUS 환경 계획·확인 → 모델 연결 1회 → 작은 실제 에이전트 평가 → Foundry IQ → 두 Optimizer의 개별 체크포인트 → 동결·새 holdout → 사람의 판단 → 관측과 다음 개선

SFT와 Frontier는 **선택 부록**입니다. 기본 학습 루프를 끝내기 위해 학습 작업을 제출할 필요는 없습니다.

## 지금 시작: 계정·설치 없이 먼저 판단

Contoso Atlas Cloud 고객이 “9월 10일 최초 월 구독을 샀고 오늘은 9월 15일입니다. 환불해 주세요.”라고 물었습니다.

> **작성된 오답:** “14일 안이므로 환불이 승인되었고 내일 입금됩니다.”

왜 위험한가요? [합성 환불 정책](data/knowledge/documents.json)의 `ATLAS-REF-001`은 최초 월 구매·기한·프로덕션 작업·유료 크레딧 조건을 확인하게 합니다. **신청 자격은 승인이나 송금 완료가 아니며, 이 도우미에는 환불 실행 도구가 없습니다.**

패키지 전체를 받은 뒤, Python 3.11 이상이 있는 로컬 터미널에서 실행합니다. Python 3.12를 권장합니다.

```bash
python3 -S -m lab demo
```

**완료 신호:** `AUTHORED_DEMO_NOT_LIVE`, `author_type: ai`, `DEMO_COMPLETED`. 답변·점수·대화는 AI 작성 예시이며 사람의 작성/검토를 주장하지 않습니다. Azure 로그인, `.env`, Azure CLI, SDK 설치, 네트워크, 유료 호출이 필요하지 않습니다. 실제 모델 성능이나 사람의 운영 승인으로 사용하지 않습니다.

`python3`가 없다면 가이드를 먼저 읽고 Python을 준비하세요. 오류를 해결하려고 Azure LIVE 명령으로 바꾸지 않습니다. 이어서 **[본문의 같은 경로](guide/handbook.md#demo)**를 따릅니다.

## 현재 제공 상태

| 구분 | 상태와 의미 |
|---|---|
| 오프라인 가이드·DEMO | 로컬에서 학습 가능. 작성 예시이며 LIVE 아님 |
| 데이터 | 가상 Contoso 정책 8개, 원본 100건. train 56 / validation 12 / dev 12 / test 20 보존 |
| 새 Azure 환경 | 신규 NCUS RG에서 **25개 소유 리소스/연결/역할 기록**과 ARM `Succeeded` 확인. 모델 4개, Foundry 프로젝트, Search, 관측 자원을 새로 구성 |
| 실제 모델·에이전트·검색 | 모델 smoke, 기준선 Agent, IQ/MCP dev 12건, 실제 1536차원 embedding·벡터/하이브리드 검색·IQ 계획 실행 |
| 평가와 개선 | 실제 managed 평가와 별도 업무/검색 Judge 실행. 누락·429·JSON 오류·교정 불일치를 남겨 **HOLD**. Prompt Optimizer 후보를 실제 생성하고 새 Agent로 재평가 |
| 최적화·학습 완료 | Agent Optimizer `succeeded`. SFT 학습·실제 모델 배포·동일 기반 dev 12×2 paired 평가 완료. 중요 실패가 남아 운영 판단은 HOLD |
| Frontier 지원·접근 경로 | **`NOT_VERIFIED`**. 확인하지 못한 것을 “존재하지 않음”으로 단정하지 않음 |
| 사람의 운영 승인 | 별도 절차. 자동 점수·AI 검토·과금 허용과 다름 |

작성된 DEMO, 로컬 mock 테스트, 메타데이터 조회, 실제 API 성공, 품질 통과를 섞지 않습니다. 원본 실행은 비공개 환경에, 정리한 증거는 [`evidence/`](evidence/integration-20260930/)에 보존합니다.

**실패에서 보완한 점:** 폐기 모델 거절 뒤 응답 생성 전에 gpt-4.1-mini로 명시 전환했고, 프로젝트/모델 동시 생성 충돌과 관측 연결 메타데이터를 실제 오류로 확인해 고쳤습니다. 같은 RG와 실패 원본을 보존했으며 기존 Azure 자원은 변경하지 않았습니다.

## LIVE로 넘어가기 전 로컬 설치

DEMO 후 본문 02장에서 수행할 명령입니다. **패키지 설치에는 네트워크가 필요하며 DEMO의 전제 조건이 아닙니다.**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m lab validate
```

macOS/Linux의 bash·zsh 또는 Windows WSL2 Ubuntu를 기준으로 합니다. PowerShell에 `source`를 그대로 붙여 넣지 않습니다.

**완료 신호:** 데이터 검사 통과, 원본 100건과 분할 유지. 이후 [새 환경 준비](guide/admin-setup.md)를 따릅니다. 예전 계정·구독·리소스 프로파일을 재사용하지 않습니다. `.env.example`은 자리표시자 템플릿일 뿐이며 실제 환경은 bootstrap의 비공개 manifest·`.env`로 구분합니다.

## 문서 지도

| 목적 | 읽을 문서 |
|---|---|
| 참가자: 처음부터 끝까지 한 경로 | [웹 가이드](index.html) · [원문](guide/handbook.md) |
| 운영자: 새 환경·신원·비용·RBAC·재개 | [운영자 안내](admin.html) · [원문](guide/admin-setup.md) |
| 강사: 단계별 완료와 보류 판단 | [강사 안내](facilitator.html) · [원문](guide/facilitator.md) |
| 선택: 실제 SFT와 Frontier 경계 | [부록](sft.html) · [원문](guide/sft-appendix.md) |
| 데이터와 평가 입력의 경계 | [데이터 설명](data-guide.html) · [원문](data/README.md) |
| 무엇을 확인했고 무엇이 미실행인가 | [검증 기록](verification.html) · [원문](guide/verification.md) |
| v1 장점의 이관·제외·출처·아카이브 준비 | [이관 기록](migration.html) · [원문](guide/integration-migration.md) |
| 인쇄용 전체 가이드 | [통합 HTML](print.html) · [PDF](Foundry-Learning-Loop-Lab-KO.pdf) |

패키지 **전체**를 같은 폴더에 두세요. 읽기·검색·코드 복사는 오프라인으로 동작하며, 복사 버튼은 명령을 실행하지 않습니다. PDF의 시각적 줄바꿈 대신 웹의 코드 복사를 사용합니다. 문서가 변경되면 HTML/PDF도 다시 제작·검사해야 합니다.

## 반드시 지킬 경계

- `python -m lab`는 이 저장소의 교육용 도구이며 Microsoft 공식 CLI가 아닙니다.
- 신규 **North Central US** 리소스만 사용합니다. 기존/공유 리소스, 공유 정책, 다른 리전은 변경하지 않습니다.
- 이번 작업은 **금액 상한 없음이 명시 승인**되었지만 무제한 작업 승인이 아닙니다. 300회 호출, Optimizer별 1작업·최대 2후보, SFT 1작업·1 epoch, 작업당 최대 60분 대기 등 합의한 범위를 유지합니다. 다른 참가자는 자신의 승인 범위를 별도로 확인해야 합니다.
- GlobalStandard/Global/Developer의 처리 위치는 리소스 리전과 다릅니다. 합성 데이터 승인 범위를 실제 고객 데이터로 확대하지 않습니다.
- **새 RG와 결과는 검토를 위해 보존합니다. 삭제 승인은 없습니다.** 터미널을 닫아도 Search·학습 모델 호스팅 등의 비용은 계속될 수 있습니다.
- AI가 작성·검토한 기록은 AI로 표시합니다. 사람 검토를 대신 기록하거나 HOLD를 없애려고 실패·점수·합격선을 바꾸지 않습니다.
- fresh holdout 12건은 동결 후 별도로 만들며 원본 test 20건을 대체하거나 그 게이트를 낮추지 않습니다.
- 실제 환경·승인 원문·자격 증명·가공 전 실행 결과를 소스, ZIP, PDF에 넣지 않습니다. 안전하게 정리한 신규 실행 증거만 포함합니다. v1 저장소의 실행 파일이나 README가 없어도 이 패키지만으로 진행합니다.

## 제작자용 로컬 검사

```bash
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -v
```

위 빌더는 웹 문서와 `print.html`을 생성하며 **PDF는 별도 제작**합니다. 패키지 이름/버전은 **v1.1**을 유지합니다. 문서 제작 기준일은 **2026-09-30**이며, 개별 서비스의 지원 상태와 실제 실행 시점은 검증 기록에서 구분합니다.
