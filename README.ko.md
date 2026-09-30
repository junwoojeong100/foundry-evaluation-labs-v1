# Foundry Learning Loop Lab v1 · 한국어

**[한국어 실습 시작 → GitHub Pages](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#start)** · **[English guide](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/#start)** · [English README](README.md)

Contoso 고객지원 에이전트의 평가·지식 연결·지시 개선을 경험하는 실습입니다. **약 3–4시간**, 한 페이지의 6단계를 순서대로 진행합니다. 결과 공유, 기능 설명, CLI 해설과 실제 포털 스크린샷 14장이 포함되어 있습니다.

> 예시 이해 → 환경 연결 → 기준선 평가 → Foundry IQ → Agent Optimizer → 최종 판정·종료

**기본 언어는 영어이며, 모든 가이드·참고 문서·통합 인쇄본을 한국어와 영어로 제공합니다.** 상단의 **English / 한국어**로 같은 문서의 언어를 전환할 수 있고, 절 링크와 읽음 기록은 유지됩니다. 문서 열람에는 설치·로그인·JavaScript가 필요 없습니다.

실습의 재현성을 위해 **정책·프롬프트·CLI 출력·에이전트 응답은 기존 한국어 원본**을 유지합니다. 영문 가이드는 원본 예시에 영어 해설을 붙이며 데이터·명령·기존 LIVE 결과를 바꾸지 않습니다.

## 시작하기

- **온라인:** 위 GitHub Pages 링크를 엽니다. 아래의 모든 HTML 링크는 소스 파일 화면이 아닌 게시된 가이드로 연결됩니다.
- **오프라인:** 저장소 전체를 내려받아 영어는 `index.html`, 한국어는 `docs/ko/index.html`을 엽니다. `docs/`·`web/` 등 패키지 폴더를 함께 유지합니다.
- **CLI 실습:** Python 3.11 이상(3.12 권장)과 bash·zsh 또는 Windows WSL2를 사용합니다. 설치·인증은 [가이드 02](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#prepare)를 따릅니다.

저장소 루트에서 실행하는 첫 DEMO입니다.

```bash
python3 -S -m lab demo
```

`-S`는 Python의 `site` 초기화를 생략하며, `demo`는 작성된 예시만 출력합니다. SDK·Azure 로그인·네트워크·유료 모델 호출이 필요 없습니다.

## GitHub Pages 가이드

| 내용 | 한국어 | English |
|---|---|---|
| 참가자 6단계 실습 | [실습 시작](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/index.html#start) | [Start](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/index.html#start) |
| 환경 준비 | [운영자 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/admin.html) | [Operator](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/admin.html) |
| 진행·오류 대응 | [강사 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/facilitator.html) | [Facilitator](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/facilitator.html) |
| 선택 심화 | [SFT·Frontier 부록](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/sft.html) | [SFT appendix](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/sft.html) |
| 합성 데이터·평가 계약 | [데이터 설명](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/data-guide.html) | [Data guide](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/data-guide.html) |
| 최신 검증·출처 | [검증 안내](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/verification.html) | [Verification](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/verification.html) |
| 부록 포함 인쇄본 | [통합 인쇄본](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/ko/print.html) | [Print edition](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/print.html) |
| PDF 다운로드 | [한국어 PDF](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-KO.pdf) | [English PDF](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/docs/Foundry-Learning-Loop-Lab-EN.pdf) |

기계 판독용 문서 검증 기록: [evidence/latest.json](evidence/latest.json).

## 주의사항

- 데이터는 가상 Contoso 정책 8개·사례 100건입니다. 마지막 LIVE 품질 판정은 **HOLD**이며 실행 완료가 운영 승인은 아닙니다.
- 유료 실습은 전용 North Central US 환경과 본인의 권한·비용 승인 범위에서만 진행합니다. 환경 신규 구축·SFT는 기본 예상 시간에 포함되지 않습니다.
- `.env`·`.lab/`·인증·원본 실행 자료는 공개하지 않습니다. 저장소 정리가 Azure 자원 삭제·과금 중단을 뜻하지 않습니다.

## 문서 갱신

```bash
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -v
```

저장소 루트에서 `requirements.lock`의 의존성을 설치한 뒤 실행합니다. 빌더는 **두 언어의 모든 HTML과 통합 인쇄본**을 함께 생성하며, `--check`는 쓰기 없이 최신 상태를 확인합니다.

영문 원문은 `guide/en/`·`data/README.en.md`, 한국어 원문은 `guide/`·`data/README.md`, 공통 UI 번역은 `web/locales.json`입니다. HTML은 영어 `docs/*.html`, 한국어 `docs/ko/*.html`에 생성합니다. 언어별 대응 절 ID와 실행 예시는 기존 한국어 ID까지 동일하게 유지해 깊은 링크·읽음 기록을 보존합니다.

PDF는 각 언어의 통합 인쇄본을 열어 배경 그래픽을 포함한 A4 PDF로 저장합니다. 파일명은 `docs/Foundry-Learning-Loop-Lab-EN.pdf`와 `docs/Foundry-Learning-Loop-Lab-KO.pdf`입니다. `requirements-verification.lock`의 검증 의존성을 설치한 뒤 `python scripts/verify_pdf.py docs/Foundry-Learning-Loop-Lab-KO.pdf --language ko`로 확인합니다(영어는 파일명과 `--language en`으로 변경). 이후 `python scripts/package_lab.py`로 오프라인 ZIP을 갱신합니다.

GitHub Pages는 **`main` 브랜치의 루트**와 `.nojekyll`을 사용합니다. 모든 생성 HTML과 로컬 자산을 제공하며, 루트 `index.html`은 쿼리·절 링크를 보존해 기본 영문 가이드로 연결합니다. 기존 `docs/english.html`도 전체 영문 가이드로 연결됩니다. `python -m lab`는 교육용 도구이며 Microsoft 공식 CLI가 아닙니다.
