# 신규 LIVE 증거 · 2026-09-30

이 폴더는 새 NCUS 환경의 **실제 결과를 안전하게 정리한 기록**입니다. DEMO, 테스트 mock, 이전 v1 실행을 LIVE로 바꿔 이름 붙이지 않았습니다.

| 파일 | 의미 |
|---|---|
| `live-summary.json` | 실제 리소스·모델·Agent·Judge·검색·Optimizer·SFT·freeze/holdout·비용 확인 수준 |
| `provisioning-first-attempt.json` | 폐기 모델의 실제 Provider 거절 |
| `provisioning-partial-result.json` | 동시 생성 충돌 당시의 성공/실패를 보존한 기록 |
| `calibration-change-record.json` | holdout 생성 전 Judge의 더 엄격한 버전 변경과 이전 HOLD 보존 |
| `prompt-optimizer-candidate.txt` | 실제 Prompt Optimizer가 반환한 텍스트 원문. 3건 smoke는 모두 형식 실패 |
| `agent-optimizer-candidate.txt` | 실제 Agent Optimizer의 후보 지시 원문. 운영 승인 또는 권장 정답이 아님 |
| `agent-optimizer-changes.diff` | 원래 IQ 지시와 서비스 후보의 차이. dev 유래 정책 예시가 들어간 위험도 검토 대상 |
| `agent-optimizer-succeeded.png` | 신규 프로젝트의 실제 완료 화면. 내장 순위와 업무 게이트는 다름 |
| `official-header-*.png` | Playwright headless로 검증한 로컬 가이드의 공식 아이콘. Azure 실행 증거는 아님 |
| `final-pdf-check.json` | 최종 PDF의 텍스트·페이지·잘림·로컬 링크 검사 |
| `final-local-checks.json` | 로컬 회귀·독립 패키지·headless 검증 범위 |

가공 전 서비스 응답과 인증/승인/전체 리소스 ID는 비공개 `.lab/`에 별도로 보존합니다. 이 폴더에는 키·토큰·MFA 정보·사용자 이메일·개인 식별자를 넣지 않았습니다.

**결론은 HOLD입니다.** 서비스 완료, dev 개선, 독립 최종 시험, 사람의 운영 승인은 서로 다릅니다. 교정 불일치 때문에 fresh holdout의 최종 추론은 차단했고, 사람의 운영 승인을 대신하지 않았습니다.
