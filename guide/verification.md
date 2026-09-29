# 검증 기록과 한계

**이 문서는 가이드 작성 검증과 실제 Azure 실습 완료를 구분합니다.** 기준일은 2026-09-29입니다.

## 확인한 것

| 범위 | 확인 내용 |
|---|---|
| 실행 환경 | Python 3.12, 프로젝트별 가상환경, 고정 의존성 설치 |
| SDK | `azure-ai-projects 2.7.0`, `openai 3.20.0`, `azure-identity 1.25.3`의 실제 설치·메서드 계약 |
| 데이터 | 가상 Contoso 정책 8개, 100개 사례, train 56 / validation 12 / dev 12 / test 20 |
| 데이터 경계 | split·질문 그룹 분리, 출처 ID, 정책 원문 context, JSONL 형식, 결정적 생성·해시 |
| 평가 엔진 | 잘못된 JSON·서비스 실패·누락 judge·출처 오류·중요 실패·잘못된 비교 조건에서 통과하지 않는 오프라인 검사 |
| 관리형 평가 연결 | 저장된 응답만 평가하도록 하는 API 계약·행 ID 조인·공개 설정 계보·중복 제출 방지의 모의 검사 |
| SFT 연결 | Standard SFT 업로드·제출·상태·취소·같은 기반 모델의 paired 비교를 모의 API로 검사 |
| 안전한 범위 | 지정 사용자·테넌트·구독·리전·endpoint 검사, 명시적 확인, 공유 리소스 삭제 방지 |
| 문서 화면 | 데스크톱 1440px 및 모바일 390px에서 본문·탐색·검색·앵커·그림 로딩·전체 페이지 가로 넘침 확인 |
| 접근성 | 한국어 언어 선언, skip link, 제목·표 머리글·그림 설명, 포커스, 키보드 탐색, 모바일 표/그림 스크롤 영역 |
| 인쇄 | A4 통합 PDF의 한국어 텍스트·본문/부록 수록·페이지 경계·공백 페이지·휴대 불가능한 localhost 링크를 검사하고 대표 페이지를 렌더링하여 확인 |

모의 테스트의 응답·점수는 테스트 fixture이며, 고객에게 실제 개선 결과로 제공하지 않습니다. `artifacts/runs/`에 실제 성공 점수를 미리 만들어 두지 않았습니다.

## 지정 계정에서 실제로 확인한 읽기 전용 항목

| 항목 | 관찰 |
|---|---|
| 로그인 | 요청한 사용자·테넌트·구독과 Azure CLI 결과 일치 |
| 리소스 | 본문의 Foundry 계정/프로젝트와 Search가 North Central US에 존재 |
| 배포 | `workshop-chat`, `workshop-judge`, `workshop-optimizer` 존재와 배포 상태 |
| Foundry API | 현재 SDK로 에이전트·연결 메타데이터 읽기 성공 |
| Search API | 인덱스 메타데이터 및 `2026-08-01-preview` 지식 베이스 목록 API 읽기 성공 |
| 평가기 카탈로그 | `builtin.groundedness` selector 18, `builtin.relevance` selector 14 관찰 |
| judge 배포 | `workshop-judge`의 실제 모델 `gpt-5.5`, 버전 `2026-04-24` 메타데이터 확인 |
| 관측 자원 | NCUS Application Insights/Log Analytics와 프로젝트의 Application Insights 유형 연결 존재 |

이것은 **해당 시점의 메타데이터 관찰**입니다. 파일에 있는 계정 정보만 보고 확인했다고 쓴 것이 아니지만, 쓰기 권한·서비스 실행·미래 가용성까지 보장하지도 않습니다. 내장 평가기 selector가 공개되어 있어도 비공개 rubric 내용이나 서비스 내부 릴리스까지 검증했다는 뜻은 아닙니다.

## 실행하지 않은 것

- 새 Azure 리소스·인덱스·지식 베이스·에이전트·역할 생성 또는 변경
- 모델 추론·IQ 검색/planner 호출·유료 평가·Optimizer 작업
- 학습 데이터의 실제 업로드·SFT/RFT/Frontier 학습 제출·학습 모델 배포
- Frontier 참여 신청서 제출 또는 해당 계정의 FDE 참여 승인 확인
- 실제 trace 내용 열람, 운영 정책 적용, 고객 운영 채널 게시
- 기존 고객·공유 리소스 삭제

따라서 **실제 학습 완료, 성능 향상, 안전성, NCUS 내부만의 처리, 운영 준비 완료**를 주장하지 않습니다. 그 증거는 참가자가 승인된 환경에서 본문을 따라 실행해 남겨야 합니다.

## 중요한 제품 경계

**Prompt Optimizer와 Agent Optimizer는 다릅니다.** 전자는 지시문 재작성, 후자는 데이터·평가 기반 후보 탐색입니다. 포털과 hosted-agent SDK의 데이터 형식을 같은 계약이라고 가정하지 않았습니다.

**Frontier Tuning과 일반 SFT는 다릅니다.** 확인한 Frontier 공식 자료는 Private Preview/FDE 협업과 관심 신청 경로를 안내합니다. 공개 셀프서비스 Foundry 학습 절차는 확인하지 못했으며, 이 테넌트의 참여 상태는 미확인입니다. 부록의 SFT는 SFT로만 표시합니다.

**고정 정책 근거와 실제 검색 근거는 다릅니다.** 관리형 품질 비교의 `context`는 고정 참조 정책이고, 실제 MCP 출력은 `retrieved_context`로 별도 보존합니다. 출처 ID 검사만으로 의미상의 근거성을 증명하지 않습니다.

**리소스 리전과 처리 위치는 다릅니다.** 기본 모델의 `GlobalStandard`를 NCUS 안에서만 처리하는 배포로 설명하지 않습니다. Standard/Global/Data Zone/Developer 학습 유형 역시 구분합니다.

## 재검사 명령

패키지 루트에서 가상환경을 활성화한 후 실행합니다.

```bash
python scripts/build_datasets.py --check
python scripts/build_guide.py --check
python -m unittest discover -s tests -v
```

실제 Azure 준비 상태는 별도로 다시 확인합니다.

```bash
python -m lab preflight
```

PDF 검사는 실습 실행과 별개인 선택적 제작 도구입니다. `requirements-verification.lock`에는 PDF 확인용 의존성이 추가되어 있으며, 참가자의 기본 실습 설치에는 필요하지 않습니다.

```bash
python -m pip install -r requirements-verification.lock
python scripts/verify_pdf.py Foundry-Learning-Loop-Lab-KO.pdf
```

가이드·SDK·API·모델·평가기·데이터를 바꿨다면 이전 검증 기록을 새 변경에 대한 검증으로 재사용하지 않습니다.
