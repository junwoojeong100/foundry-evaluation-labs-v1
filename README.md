# Foundry Learning Loop Lab · 한국어

**[실습 가이드 열기 → `index.html`](index.html)**

하나의 Contoso 고객지원 에이전트를 **평가 → Foundry IQ → Optimizer → Frontier Tuning → 재평가 → Control Plane 운영**으로 개선하는 실습 패키지입니다. 리전은 **North Central US**, 기본 프로파일은 요청한 실습용 계정과 기존 프로젝트에 맞춰져 있습니다.

## 시작

패키지 **전체**를 한 폴더에 풀고 `index.html`을 브라우저로 엽니다. 가이드는 인터넷 없이 읽을 수 있습니다. 실제 Azure 실습에는 로그인·네트워크·서비스 접근 권한·비용 승인이 필요합니다.

| 찾는 것 | 파일 |
|---|---|
| 참가자용 통합 가이드 | [index.html](index.html) |
| 참가자 가이드·부록 통합 PDF | [Foundry-Learning-Loop-Lab-KO.pdf](Foundry-Learning-Loop-Lab-KO.pdf) |
| 원본 한국어 문서 | [guide/handbook.md](guide/handbook.md) |
| 강사 준비·운영·확장 프롬프트 | [facilitator.html](facilitator.html) |
| 실제 SFT 학습 부록 — Frontier 아님 | [sft.html](sft.html) |
| 다른 고객의 환경 준비 | [admin.html](admin.html) |
| 합성 데이터 설명 | [data-guide.html](data-guide.html) |
| Python 의존성 고정 | [requirements.lock](requirements.lock) |
| 검증 범위와 한계 | [verification.html](verification.html) |

## 먼저 알아둘 경계

- **실제 결과를 만들어 두지 않았습니다.** 모델 호출·평가·최적화·학습의 실제 결과는 실행 후 `artifacts/`에 기록됩니다.
- **Frontier Tuning과 일반 fine-tuning은 구분합니다.** Preview·테넌트 승인·리전·모델 지원을 먼저 확인합니다. 접근이 막히면 완료로 표시하지 않습니다.
- **리소스가 NCUS에 있어도 모든 처리가 NCUS 안에서 이뤄진다는 뜻은 아닙니다.** 기본 배포의 `GlobalStandard` 처리 조건을 확인하세요.
- **공유 리소스를 자동으로 삭제하지 않습니다.** 정리는 이 실습이 생성했다고 기록한 개별 객체만 대상으로 합니다.
- `.env.example`에는 비밀값이 없습니다. 암호·키·토큰을 파일이나 소스에 넣지 않습니다. 고객에게 재배포할 때 계정·구독 프로파일을 고객 환경에 맞춥니다.

## 로컬 준비

macOS/Linux 또는 Windows WSL2의 패키지 디렉터리에서:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
cp .env.example .env
python scripts/build_datasets.py
python -m lab validate
```

이 명령들은 Azure에 데이터를 업로드하거나 모델을 호출하지 않습니다. 이후 단계는 **통합 가이드의 02장부터 순서대로** 진행하세요.

`python -m lab`는 Microsoft 공식 CLI가 아니라 이 패키지의 교육용 도구입니다. 직접 실행하는 유료/변경 단계에는 `--confirm`이 필요합니다.

## 가이드 재생성과 로컬 검사

```bash
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -v
```

전체 웹 문서와 `print.html`을 함께 생성합니다. 인쇄본의 명령이 시각적으로 줄바꿈되었을 수 있으므로 터미널에 붙여 넣을 때에는 웹 가이드의 **코드 복사**를 사용하세요.

공개 문서 확인 기준일: **2026-09-29**. 서비스 화면·Preview 상태·지원 모델·과금은 변할 수 있으므로 본문의 공식 출처와 사전 점검을 다시 확인하세요.
