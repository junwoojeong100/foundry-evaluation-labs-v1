# 선택 부록 — 실제 Foundry SFT 학습 실습

> **선택·별도 유료 경로 / Foundry SFT이며 Frontier Tuning이 아닙니다.**
> 이 부록은 공개 self-service API로 **모델 가중치를 실제 학습**하는 추가 경험입니다.
> Frontier Tuning은 FDE 협업형 private preview이며 [공식 nomination](https://aka.ms/frontiertuning)이 별도입니다.
> 공개 self-service Frontier Tuning API는 검증되지 않았습니다. 이 테넌트의 entitlement는 **UNKNOWN**이며, 메타데이터가 없다는 이유로 미승인이라고 단정하지 않습니다.
> SFT 작업·모델·점수를 Frontier Tuning 성과로 이름만 바꾸어 보고하지 마세요.

## 1. 범위와 비용을 먼저 승인한다

- 학습 기반은 **`gpt-4o-mini-2024-07-18`**, 방법은 **supervised**, 학습 유형은 **`Standard`**, 리전은 **North Central US**로 고정합니다.[1]
- 기존 `workshop-chat`의 GPT-6 계열은 이 실습의 학습 기반이 아닙니다. GPT-6 에이전트와 학습된 GPT-4o mini의 차이를 “튜닝 효과”라고 해석하지 않습니다.
- `Standard` 학습은 현재 Foundry 리소스 리전에서 수행됩니다. 오류가 나도 `GlobalStandard`/`Developer`로 자동 전환하지 않습니다.
- 작성 시점의 기반 GPT-4o mini Standard 추론 할당량 관측은 **스냅샷일 뿐**입니다. 현재 모델별 단위·가용 용량·학습 허용량·배포 성공은 실행 전에 다시 확인합니다.
- 업로드/학습 권한과 배포 권한은 구분됩니다. 관리자가 해당 프로젝트의 학습 권한 및 계정의 deployment write 권한을 확인해야 합니다.[1]
- **학습 비용 + 기반/학습 모델 추론 비용 + 학습 모델의 지속적인 시간당 호스팅 비용 + 평가 모델 비용**을 따로 승인하세요.[2]
- 이 패키지 작성 과정에서는 이 부록의 업로드·학습·배포·유료 추론을 실행하지 않았습니다. 파일 존재나 테스트 통과가 클라우드 성공 증거는 아닙니다.

## 2. 준비 파일과 로그인 범위를 고정한다

공통 준비를 마친 프로젝트 루트에서 실행합니다. `.env`의 계정·프로젝트·구독·테넌트·`LAB_PREFIX`를 실험 중 바꾸지 마세요.
모든 원격 SDK 호출은 `credential_for(config)`로 CLI 로그인 사용자·테넌트·구독을 확인한 뒤 subscription-bound `AzureCliCredential`만 사용합니다.
환경 변수/API 키/다른 로그인 방식으로 자동 대체하지 않습니다.

```bash
.venv/bin/python -m lab.sft --help
.venv/bin/python -m lab tune-prepare --kind sft
.venv/bin/python -m lab.sft --config .env status
```

생성 위치는 `artifacts/tuning/sft/`입니다. 이미 있는 준비 폴더를 덮어쓰지 않습니다.

| 파일 | 내용 | 학습 서비스 사용 |
|---|---|---|
| `sft-train.jsonl` | train 56행, UTF-8 BOM | 학습 파일 |
| `sft-validation.jsonl` | validation 12행, UTF-8 BOM | 검증 파일 |
| `manifest.json` | 준비 시 행 수·바이트·SHA-256 | 로컬 근거, 업로드 금지 |
| `sft-state.json` | 학습 전 기준선·실제 파일 ID·작업 ID·상태 원장 | 도구가 단계별 기록 |

`manifest.json`의 `PREPARED_NOT_SUBMITTED`는 변하지 않는 **준비 시점** 기록입니다. 이후 실제 진행은 `sft-state.json`으로 확인합니다.
dev 12행/test 20행/원본 `cases.jsonl` 전체는 학습 파일로 업로드하지 않습니다.
학습 입력은 `system → user → assistant`이며, user JSON에는 **query와 context만** 있습니다.
정답·라우팅 라벨은 assistant 학습 정답/평가 전용입니다. 변경되는 정책 사실은 가중치 암기가 아니라 현재 근거로 제공합니다.

## 3. 먼저 동일 기반 모델을 배포한다

1. [Foundry 포털](https://ai.azure.com/)에서 `.env`와 같은 구독·계정·프로젝트의 현재 할당량·RBAC·NCUS 용량·가격을 확인합니다.
2. **Build → Models → Deploy model**에서 기반 `gpt-4o-mini`, 버전 **2024-07-18**, **Standard**를 배포합니다.
3. 고유한 `<본인 prefix>-sft-base` 이름을 쓰고 버전·SKU·용량·필터 정책을 실험 중 유지합니다. GPT-6 배포를 재사용하지 않습니다.
4. Provisioning state가 **Succeeded**인지 확인합니다. **학습 Standard와 배포 Standard는 별개의 선택**입니다.

자동 유료 배포 명령은 제공하지 않습니다. 아래 `my-sft-base`는 **실제로 만든 고유 기반 배포 이름**으로 바꾸세요.

## 4. 학습 전에 dev 기준선을 실행하고 보고서를 읽는다

```bash
.venv/bin/python -m lab.sft --config .env baseline \
  --base-deployment my-sft-base --run-id sft-pretrain-dev-01 --confirm
.venv/bin/python -m lab score --run-id sft-pretrain-dev-01
cat artifacts/runs/sft-pretrain-dev-01/report.md
```

**학습 전 baseline은 필수**입니다. 같은 system과 query/context만으로 **dev 12행 전체**를 유료 추론하고 로컬 점수·보고서를 자동 저장합니다.
추가 `score`는 같은 캡처를 로컬 재계산할 뿐 재추론하지 않습니다. 어떤 실패를 SFT로 고치려는지 보고서에서 확인하세요.
`submit`은 원장에 기록된 완료 기준선과 데이터·프롬프트·지식·원본 응답·배포 근거를 검사합니다. 누락·변경·부분 실행이면 차단합니다.
**높은 점수는 제출 조건이 아닙니다.** API/형식/행동 실패도 원래 분모에 남깁니다. test는 학습 전에 실행하지 않습니다.
기반 배포 설정이 바뀌면 제출 전에 새 `--run-id`와 비용 승인으로 기준선을 다시 기록합니다. 이전 실행과 원장 이력은 보존합니다.

## 5. 포털에서 Create SFT model 설정을 확인한다

1. [Foundry 포털](https://ai.azure.com/)에서 `.env`와 같은 구독·계정·프로젝트를 선택합니다.
2. **Build → Fine-tune → Fine-tune**에서 **Fine-tune a model / Create SFT model** 화면을 엽니다.[1]
3. 기반 `gpt-4o-mini`의 **2024-07-18**, 방법 **Supervised fine-tuning**, 학습 유형 **Standard**를 확인합니다.
4. 학습/검증 데이터는 각각 준비한 두 파일입니다. 두 분할을 합치거나 검증 파일을 생략하지 않습니다.
5. seed **105**, epochs **1**을 확인합니다. 이 부록의 SDK 작업은 자동 배포하지 않으며, 학습 모델 배포·호스팅은 별도로 승인합니다.
6. 이 부록은 아래 CLI로 한 번만 제출하므로 **포털 Submit은 누르지 말고 폼을 닫습니다**. 같은 학습을 양쪽에서 만들지 마세요.

이 모델/버전/Standard 선택이 보이지 않거나 권한·용량 오류가 있으면 중단합니다.
다른 모델·리전·학습 유형으로 조용히 바꾸거나 Frontier Tuning entitlement와 연결해서 해석하지 않습니다.

## 6. 파일만 업로드하고 processed를 확인한다

```bash
.venv/bin/python -m lab.sft --config .env upload --confirm
.venv/bin/python -m lab.sft --config .env status
```

실제 `files.create(file=..., purpose="fine-tune")`를 사용합니다. 첫 ID를 디스크에 저장한 뒤 다음 파일을 업로드합니다.
이미 ID가 기록된 파일은 재실행해도 재업로드하지 않습니다. 서버가 명시적으로 거절한 미완료 업로드만 다시 시도할 수 있습니다.
연결 단절처럼 성공 여부가 불명확하면 재업로드를 막습니다. 원장과 포털에서 실제 파일부터 확인하세요.
두 파일 모두 **`processed`**여야 다음 단계가 가능합니다. `uploaded`/처리 중은 학습 준비 완료가 아닙니다.
`status`는 매번 한 번씩 조회할 뿐 무한 대기하지 않습니다. 잠시 기다린 뒤 사람이 다시 실행하세요.

## 7. 실제 Standard SFT 작업을 한 번 제출한다

```bash
.venv/bin/python -m lab.sft --config .env submit --confirm
.venv/bin/python -m lab.sft --config .env status
```

제출 계약은 다음과 같습니다. 모델 배포 이름이 아니라 **학습 기반 모델 ID**입니다.

```python
client.fine_tuning.jobs.create(
    model="gpt-4o-mini-2024-07-18",
    training_file=training_file_id,
    validation_file=validation_file_id,
    seed=105,
    method={"type": "supervised", "supervised": {"hyperparameters": {"n_epochs": 1}}},
    extra_body={"trainingType": "Standard"},
)
```

이 코드는 SDK 계약 설명입니다. CLI 외에 별도로 실행해 두 번째 작업을 만들지 마세요.
1 epoch는 비용을 통제하기 위한 작은 교육용 시작점이지 품질 향상이나 예산 상한을 보장하지 않습니다.
원장에 **SUBMITTING을 먼저 기록**하고 네트워크 요청을 보냅니다. SDK 자동 재시도는 0입니다.
작업 생성 후에는 실패했더라도 같은 원장의 `submit`을 다시 실행할 수 없습니다.

**타임아웃/연결 단절 복구:** `SUBMISSION_UNKNOWN` 또는 남은 `SUBMITTING`은 “작업 없음”이 아닙니다.
포털의 같은 계정·프로젝트에서 요청 시각, 기반 모델, 두 파일 ID, Standard, seed/epochs를 실제 작업과 대조하세요.
원장을 지우고 재제출하지 마세요. 이 CLI는 임의 작업 ID 채택 기능을 제공하지 않습니다.
발견한 작업은 포털에서 조회/취소하고 실제 종료를 확인한 뒤 검증된 기록 복구 또는 별도 실험을 결정합니다.
`operation.lock`이 남았다면 기록된 프로세스가 종료됐고 다른 작업이 실행 중이지 않은지 확인한 후에만 그 잠금 파일을 정리하세요.

## 8. 상태와 실제 학습 결과를 읽는다

`status`의 `actual_status`는 서비스의 실제 상태입니다. 대기/실행/실패/취소를 성공으로 바꾸지 않습니다.
**`succeeded`와 실제 `fine_tuned_model`이 모두 있어야** 다음 비교에 사용할 수 있습니다. 작업 ID·모델 ID를 추측해 채우지 마세요.
포털 **Job details → Monitor**에서 실제 train loss와 validation loss를 확인합니다.
학습 loss만 낮아지고 validation loss가 나빠지면 과적합 가능성이 있습니다. loss 자체를 고객지원 정확도나 안전성 점수로 보고하지 않습니다.
**Checkpoints**도 확인하세요. 여러 epoch를 돌린 다른 실험이라면 validation/dev로 후보를 선택하며 test로 체크포인트를 고르지 않습니다.
이 1-epoch 경로는 실제 최종 `fine_tuned_model`만 비교합니다. 다른 체크포인트 ID로 몰래 교체하지 않습니다.
서비스가 제공한 `result_files`/`trained_tokens`는 상태 근거로 남지만, 코드가 가짜 학습 곡선·토큰 수·개선율을 만들지는 않습니다.

## 9. 실제 학습 모델을 별도로 배포한다

1. 현재 학습 모델 배포의 할당량·RBAC·NCUS 용량·가격을 별도로 확인합니다.
2. **Fine-tune → 성공한 작업 → Deploy**에서 방금 확인한 **실제 `fine_tuned_model`**을 선택합니다.[3]
3. 학습 모델의 ARM 모델 버전 **1**, **Standard**, 같은 계정/NCUS와 고유한 `<본인 prefix>-sft-tuned` 이름을 확인합니다.
4. 3절의 기반 배포는 유지하고 두 배포 모두 **Succeeded**인지 확인합니다. 데이터 평면 준비 지연은 여전히 가능합니다.

아래 `my-sft-tuned`는 **실제로 만든 학습 모델의 고유 배포 이름**으로 바꾸세요.
CLI는 ARM에서 계정 ID, NCUS, 모델 이름·버전, Standard SKU를 읽어 확인한 후에만 추론합니다.

## 10. dev에서 동일 조건의 모델 쌍을 실행한다

```bash
.venv/bin/python -m lab.sft --config .env run-pair \
  --base-deployment my-sft-base --tuned-deployment my-sft-tuned \
  --split dev --run-prefix sft-dev-01 --confirm
.venv/bin/python -m lab score --run-id sft-dev-01-base
.venv/bin/python -m lab score --run-id sft-dev-01-tuned
```

두 arm 모두 `project.get_openai_client().chat.completions.create`를 사용합니다.
학습 전 보고서는 학습 필요성을 검토한 근거이며, 여기서는 기반과 학습 모델을 **모두 새로 캡처**해 같은 조건으로 비교합니다.
학습과 동일한 `prompts/tuning-system.txt`, 동일한 query/context JSON, temperature 0/seed 105/최대 4096 출력 토큰을 사용합니다.
**정적 reference-context-conditioned 모델 비교**이며 Foundry IQ 검색·도구 호출·에이전트 실행 비교가 아닙니다.
기반 arm은 `stage=candidate`, 학습 arm은 `stage=tuned`; 둘 다 `target_type=model`, `technique=Foundry SFT`입니다.
`artifacts/runs/sft-dev-01-{base,tuned}/`에 프롬프트 스냅샷·해시·ARM 모델 근거·원본 응답·시간·관측 토큰을 기록합니다.
API 오류도 원래 행 수의 실패로 남깁니다. 성공 응답으로 대체하거나 실패 행을 분모에서 빼지 않습니다.
한쪽 폴더라도 있으면 재실행을 거절합니다. 새 비용 승인과 **새 `--run-prefix`** 없이는 기존 근거를 덮어쓰지 마세요.

## 11. 실제 관리형 평가를 연결하고 test를 마지막에 연다

`foundry-eval.jsonl`은 유효한 JSON 응답의 자연어 `answer`만 투영한 평가 입력입니다. IQ 검색 결과라고 표시하지 않습니다.
로컬 형식·분류·인용 검사는 근거성 judge를 대신하지 않습니다. 별도 비용을 승인한 뒤 동일 judge 조건으로 두 arm을 평가합니다.

```bash
.venv/bin/python -m lab --config .env evaluate submit --run-id sft-dev-01-base --confirm
.venv/bin/python -m lab --config .env evaluate submit --run-id sft-dev-01-tuned --confirm
.venv/bin/python -m lab --config .env evaluate collect --run-id sft-dev-01-base
.venv/bin/python -m lab --config .env evaluate collect --run-id sft-dev-01-tuned
.venv/bin/python -m lab score --run-id sft-dev-01-base
.venv/bin/python -m lab score --run-id sft-dev-01-tuned
```

collect가 아직 진행 중이면 기다렸다가 다시 조회합니다. judge 누락·오류는 **HOLD**이지 합격이 아닙니다.
validation/dev로 선택을 끝낸 뒤 동일 명령의 `--split test --run-prefix sft-test-01`로 동결 20행을 실행합니다.
관리형 평가·수집·score도 `sft-test-01-base`와 `sft-test-01-tuned`에 각각 수행한 후 비교합니다.

```bash
.venv/bin/python -m lab compare \
  --baseline sft-test-01-base --candidate sft-test-01-tuned \
  --out artifacts/sft-test-01-decision.json
```

모든 실패를 포함한 행 수, 중요 사례, judge 설정/출처, 불확실성 구간, 지연·관측 토큰을 함께 읽으세요.
작은 합성 test의 교육용 판정은 운영 승인이나 보편적 튜닝 효과의 증명이 아닙니다. test를 보고 프롬프트/학습 데이터를 다시 맞추지 마세요.

## 12. 중단·비용 정리·다음 실험

```bash
.venv/bin/python -m lab.sft --config .env cancel --confirm
.venv/bin/python -m lab.sft --config .env status
```

취소는 **원장에 기록된 작업 ID만** 대상으로 합니다. 취소 응답 후 별도 status 조회로 실제 terminal 상태를 확인하세요.
취소는 이미 발생한 학습 비용을 환불하지 않으며, 이미 만든 모델 배포도 삭제하지 않습니다.
사용을 마치면 **포털에서 본인 학습 모델 배포와 이 실습용 기반 배포를 먼저 삭제**하고, 학습 모델과 업로드 파일을 정리합니다.
다른 사람의 배포/공통 GPT-6·judge 배포는 삭제하지 마세요. 공통 `lab cleanup`이 이 부록 배포까지 지운다고 가정하지 않습니다.
학습 모델은 배포가 남아 있으면 삭제할 수 없습니다. 필요한 로컬 원장·평가 근거는 보존하세요.
**15일 비활성 배포 자동 삭제는 즉시 예산 상한이 아닙니다.** 요청이 없어도 삭제 전까지 시간당 호스팅 비용이 계속됩니다.[1][2]
새 학습은 기존 원장을 초기화하는 대신 별도 작업 폴더·새 prefix·새 데이터 버전·새 승인으로 시작합니다.

## 공식 참고 자료

1. [Customize a model with fine-tuning: 지원 모델·Standard·BOM·Foundry SDK·포털·정리](https://learn.microsoft.com/azure/foundry/openai/how-to/fine-tuning)
2. [Azure OpenAI 가격: fine-tuning 학습·추론·호스팅](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)
3. [Deploy a fine-tuned model](https://learn.microsoft.com/azure/foundry/openai/how-to/fine-tuning-deploy)
4. [GPT-4o mini fine-tuning tutorial — classic 문서, 새 포털 경로와 구분](https://learn.microsoft.com/azure/foundry-classic/openai/tutorials/fine-tune)
5. [Frontier Tuning nomination — SFT와 별도 접근 경로](https://aka.ms/frontiertuning)
