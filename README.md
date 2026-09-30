# Foundry Learning Loop Lab v1 · 한국어

**[브라우저에서 실습 시작 → GitHub Pages](https://junwoojeong100.github.io/foundry-evaluation-labs-v1/#start)**

Contoso 고객지원 에이전트의 평가·지식 연결·지시 개선을 경험하는 한국어 실습입니다. **약 3–4시간**, 한 페이지의 6단계를 순서대로 진행합니다. 기능 설명, CLI 해설과 실제 포털 스크린샷 14장이 포함되어 있습니다.

> 예시 이해 → 환경 연결 → 기준선 평가 → Foundry IQ → Agent Optimizer → 최종 판정·종료

## 시작하기

- **온라인:** 위 GitHub Pages 링크를 엽니다. 문서 열람에는 설치나 로그인이 필요 없습니다.
- **오프라인:** 저장소 전체를 내려받아 [index.html](index.html#start)을 엽니다. [통합 PDF](Foundry-Learning-Loop-Lab-KO.pdf)도 제공합니다.
- **CLI 실습:** Python 3.11 이상(3.12 권장)과 bash·zsh 또는 Windows WSL2를 사용합니다. 설치·인증은 [가이드 02](index.html#prepare)를 따릅니다.

저장소 루트에서 실행하는 첫 DEMO입니다.

```bash
python3 -S -m lab demo
```

`-S`는 Python의 `site` 초기화를 생략하며, `demo`는 작성된 예시만 출력합니다. SDK·Azure 로그인·네트워크·유료 모델 호출이 필요 없습니다.

## 문서

| 내용 | 문서 |
|---|---|
| 환경 준비 | [운영자 안내](admin.html) |
| 진행·오류 대응 | [강사 안내](facilitator.html) |
| 선택 심화 | [SFT 부록](sft.html) |
| 합성 데이터·평가 계약 | [데이터 설명](data-guide.html) |
| 최신 검증·출처 | [검증 안내](verification.html) · [결과 JSON](evidence/latest.json) |
| English | [README.en.md](README.en.md) |

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

순서대로 HTML 생성, 쓰기 없는 최신 상태 확인, 로컬 테스트입니다. PDF·ZIP은 별도 갱신합니다. GitHub Pages는 `main`의 루트와 `.nojekyll`을 사용합니다. `python -m lab`는 이 저장소의 교육용 도구이며 Microsoft 공식 CLI가 아닙니다.
