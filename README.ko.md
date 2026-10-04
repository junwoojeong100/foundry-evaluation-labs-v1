# Foundry Learning Loop Lab v1 · 한국어

**[한국어 실습](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html)** · **[English — 기본 가이드](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/)** · [English README](README.md)

**Azure를 처음 확인하는 단계부터 승인된 정리 또는 보존까지 10단계로 진행합니다.** Microsoft Foundry 관리형 Evaluation과 Agent Optimizer로 자사 대표 업무의 Agent 응답을 평가·개선합니다.

> 계정·PC·권한 확인 → Foundry 생성 → 정책·Agent 준비 → 데이터셋 → 평가기 → 평가 → 분석 → 최적화 → 재평가 → 삭제 확인

Contoso 정책·질문은 합성 자료입니다. 공개 벤치마크 순위나 운영 인증이 아니라 **평가 → 학습 → 개선 → 재평가**를 익힙니다.

처음 시작하는 경우 가이드 01부터 진행합니다. Windows PowerShell과 macOS/Linux의 설치·가상환경 명령, 입력값을 찾는 위치, 비용 승인서, 실제 Agent 생성·평가 ID 조회와 완료 기준을 제공합니다. 준비된 환경은 인수표를 확인하고 중복 생성을 건너뜁니다.

**로컬 필수 도구는 Python 3.11–3.14·Git·Azure CLI입니다.** [01의 설치 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#setup-local)에서 Windows의 WinGet·공식 설치 파일, macOS의 Homebrew, Ubuntu 24.04 LTS 경로와 가상환경 생성 전 버전 확인을 제공합니다. 이미 설치한 지원 버전은 재사용하고 PATH·설치 제한 문제는 Azure 로그인 전에 해결합니다.

**Azure·Foundry를 처음 접한다면 참가자 가이드만 먼저 읽습니다.** 계정·구독·프로젝트의 차이와 터미널 여는 방법부터 설명합니다. 04–06은 한 번의 평가 생성 과정이며, 클릭 순서·점수 해석 예시·각 단계의 완료 기준을 따라갑니다. 운영자 문서는 본문에서 연결할 때 참고합니다. 단체 초보자 수업은 운영자가 환경을 미리 준비하고 명령 실행 담당자를 지정하는 방식을 권장합니다.

시작 화면에서 실습의 정의·중요성·진행 방식·완료 산출물을 설명합니다. 각 단계는 **하는 일 → 중요한 이유 → 방법·위치 → 실제 화면과 실행 → 완료 기준**으로 읽을 수 있도록 구성합니다.

## 고정된 모델 역할과 비교 조건

| 역할 | 계획할 모델·버전 |
|---|---|
| Agent | **gpt-6-sol / 2026-09-22** |
| Foundry 평가 Judge | **gpt-6-luna / 2026-09-22** |
| Agent Optimizer 생성 | **gpt-5.5 / 2026-04-24** |

새 환경의 기본 Agent는 `lab-ko-iq` 또는 `lab-en-iq`입니다. 환경 prefix를 바꾸면 실제 출력 이름을 사용합니다. v1/v2는 변경 불가능한 Agent 전체 버전이며 **지침만 다릅니다**. 모델·도구·추론·엄격한 JSON 스키마·데이터·평가기 설정을 유지하고 개선을 크게 보이게 하려고 v1을 약화하지 않습니다.

`ensure_fixed_release`는 정식 **1·2만 허용**하고 같은 구성을 재사용하며, v3를 조용히 만들거나 기존 버전을 덮어쓰지 않습니다. 자신의 실제 Optimizer 작업에서 검토한 지침을 사용하고 운영자 수정은 원본 서비스 출력과 구분해 기록합니다. 유지할 다른 후보가 없으면 v1을 유지하고 정리·보존으로 이동하며 없는 v2 비교를 만들지 않습니다.

## 같은 데이터와 평가 기준

한국어는 변경 없는 **`data/optimizer/dev.jsonl`**, 영어는 **`data/en/optimizer/dev.jsonl`**을 사용합니다. 해당 언어의 `lab-ko-dev12` 또는 `lab-en-dev12` 버전 `1`로 등록합니다. **12행 JSONL**은 query·context·JSON 문자열 ground_truth를 포함하며 Agent에는 query만 전달합니다. 언어별 데이터와 실행 폴더를 섞지 않습니다.

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
| 문제 해결 | [문제 해결](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/troubleshooting.html) | [Troubleshooting](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/troubleshooting.html) |
| 통합 인쇄본 | [열기](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/print.html) | [Print](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/print.html) |
| PDF | [한국어](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-KO.pdf) | [English](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-EN.pdf) |
| CLI/SDK 실습 요약영상 | [한국어 MP4](docs/media/Foundry-Lab-Replay-KO.mp4) | [English MP4](docs/media/Foundry-Lab-Replay-EN.mp4) |
| 실제 포털 화면 녹화 | [한국어 MP4](docs/media/Foundry-Portal-Walkthrough-KO.mp4) | [English MP4](docs/media/Foundry-Portal-Walkthrough-EN.mp4) |

두 영상 모두 내레이션·자막·챕터를 포함하며 재사용 실습 가이드와 분리해 제공합니다. CLI/SDK 영상은 실행 기록을 재생하는 요약입니다. 포털 영상은 인증된 Azure/Foundry의 실제 화면을 녹화하고 개인정보를 가린 것으로, 기존 자원과 완료된 결과를 조회하며 평가·Optimizer를 다시 제출하지 않습니다. 외부 자막: CLI/SDK [한국어](docs/media/Foundry-Lab-Replay-KO.srt) · [English](docs/media/Foundry-Lab-Replay-EN.srt), 포털 [한국어](docs/media/Foundry-Portal-Walkthrough-KO.srt) · [English](docs/media/Foundry-Portal-Walkthrough-EN.srt).

기본 언어는 영어입니다. 언어를 전환해도 대응 절·읽음 기록·테마를 유지합니다. 로그인·JavaScript 없이 열람할 수 있으며 오프라인에서는 저장소 전체의 폴더 구조를 유지합니다.

참가자 가이드의 왼쪽 목차는 주요 10단계만 표시합니다. 상세 제목과 직접 링크는 본문에 유지하며, 참고 문서의 목차는 별도로 제공합니다.

포털 그림은 조작 위치를 설명하는 자료이며 자신의 실행 결과를 뜻하지 않습니다. 영어·한국어는 해당 언어의 그림을 사용하고 구독·권한의 공통 화면만 `web/assets/portal/shared/`를 공유합니다. 자산 출처·개인정보 가림·그림 명세는 [NOTICE](web/assets/NOTICE.txt)와 이미지 manifest에서 확인합니다.

## 실행 경계

참가자 또는 승인된 운영자가 01–03에서 격리 프로젝트와 읽기 전용 정책 연결을 준비합니다. 별도 Judge 교정·governance는 필수 실습이 아닙니다. Agent는 안내하며 환불·티켓 제출·삭제·권한 부여를 실제 수행하지 않습니다.

지원 범위는 역할별로 다릅니다. 실제 Agent·도구 호출과 [지원 Optimizer 모델](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)을 확인하고 비교 도중 모델을 바꾸지 않습니다.

운영용 게시는 실습에 포함하지 않습니다. 브라우저 종료로 과금이 멈추지 않습니다. 실제 실패를 보존하며 같은 후보를 유리한 점수가 나올 때까지 반복하지 않습니다.

10에서는 결과 보관 후 대상·소유권·승인을 확인합니다. 확인 인자가 없는 `cleanup`은 계획만 표시하며, 확인 후 실행해도 기록된 객체만 정리하고 Search·모델·그룹을 전부 삭제하지 않습니다. 삭제 승인된 전용 그룹은 `az group exists`의 `false`까지 확인합니다. 보존 승인된 전용·공유 자원은 목록·비용 담당자·보존 검토일을 기록해 인계합니다.

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

통합 인쇄본을 배경 그래픽 포함 A4 PDF로 생성하고 `requirements-verification.lock` 환경에서 `python -m scripts.verify_pdf`로 검사합니다. ZIP은 `python scripts/package_lab.py`로 만듭니다.

실행별 점수·run ID·검증 로그·원본 결과는 Git에서 제외된 비공개 실행 폴더에 보관하고 재사용 가이드에 넣지 않습니다. 가이드는 안내가 잘못된 경우에만 수정합니다. 보존하는 리소스의 소유권·설정 기록은 유지하고 오래된 보고서·임시 파일만 정리하며 클라우드 리소스를 함께 삭제하지 않습니다.

GitHub Pages는 **main 브랜치 루트**와 `.nojekyll`을 사용합니다. 루트 index.html·기존 docs/english.html은 쿼리와 절 링크를 유지하며 영어로 연결합니다.
