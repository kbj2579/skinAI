# Acne RAG Solution

비전 모델이 분류한 피부 병변 클래스와 사용자가 입력한 증상 설명을 받아, 근거 문서 기반 한국어 안내를 생성하는 간이 RAG 패키지입니다.

이 버전은 `confidence`로 응답을 분기하지 않고 `pred_label`과 증상 텍스트만으로 근거를 검색합니다. 의료 진단이나 처방이 아니라 분류 결과 설명, 일반 관리 방향, 성분 선택 참고, 피부과 방문 기준, 근거 출처 제공을 목표로 합니다.

## 범위

- 기존 MVP 호환 클래스: `Blackheads`, `Whiteheads`, `Papules`, `Pustules`, `Cyst`
- 발표용 14노드 클래스: `blackhead`, `whitehead`, `papule`, `pustule`, `cystnnodule`, `complexacne`, `milia`, `rosacea`, `seborrheic`, `sebdermatitis`, `atopic`, `psoriasis`, `normal`, `abnormal`
- RAG corpus: 143개 chunk/card
  - `cc_by`: 83개
  - `public_domain`: 51개
  - `citation_only`: 9개
- 생성 근거 기본 정책: `public_domain`, `CC0`, `CC BY` 중심
- `citation_only` 자료는 기본 RAG 원문 생성에서 제외하고 출처 확인용으로만 보관
- KCC 제출 대비 라이선스 감사 산출물:
  - `docs/license_audit_report.md`: 출처별 재사용 판단 요약
  - `docs/evidence_sources_register.csv`: 원천 URL별 라이선스/검증 방식
  - `docs/evidence_cards_register.csv`: 카드별 출처, 라이선스, 허용 용도, 클래스 태그

## 실행

간이 MVP 실행:

```powershell
python -m acne_rag_solution.simple_mvp
```

14노드 라벨과 증상을 바로 넣는 방식:

```powershell
python -m acne_rag_solution.simple_mvp --label rosacea --symptoms "얼굴 중앙이 자주 붉고 화끈거림"
```

Bedrock Claude Sonnet으로 최종 문장을 생성하는 방식:

```powershell
python -m acne_rag_solution.simple_mvp --label rosacea --symptoms "얼굴 중앙이 자주 붉고 화끈거림" --llm bedrock
```

기본 Bedrock 모델은 `global.anthropic.claude-sonnet-4-6`입니다. 다른 Sonnet inference profile을 쓰려면 `--bedrock-model-id`로 지정합니다.

표준 prediction JSON 입력:

```powershell
python -m acne_rag_solution.cli --prediction .\acne_rag_solution\sample_prediction.json --symptoms "고름이 보이고 주변이 붉음"
```

JSON 출력:

```powershell
python -m acne_rag_solution.cli --prediction .\acne_rag_solution\sample_prediction.json --json --show-prompt
```

## 입력 JSON 계약

```json
{
  "pred_label": "pustule",
  "pred_label_ko": "농포",
  "confidence": 0.86,
  "top_k_probabilities": {
    "pustule": 0.86,
    "papule": 0.08
  },
  "model_version": "skin-14node-demo",
  "image_id": "sample-pustule-001"
}
```

`confidence`는 선택 필드입니다. 값이 있어도 출력에 참고값으로만 표시하고 RAG 검색과 응답 정책 판단에는 사용하지 않습니다.

## 출력 섹션

- 모델 분류 결과
- 가능한 의미
- 일반 관리 방법
- 성분 선택 참고
- 피부과 방문이 필요한 경우
- 근거 출처
- 주의

## 검증

14노드 전체 예시 검증:

```powershell
python .\acne_rag_solution\scripts\run_class_examples.py --llm template
```

기존 5클래스 예시 검증:

```powershell
python .\acne_rag_solution\scripts\run_class_examples.py --examples .\acne_rag_solution\examples\all_class_examples.json --llm template
```

단위 테스트:

```powershell
python -m unittest acne_rag_solution.tests.test_engine
```

## 데이터 주의

이미지 데이터셋 출처는 Kaggle, Roboflow, AIHub, DermNet 계열이 섞여 있으므로 발표·논문·배포 전 각 데이터셋의 재배포 및 상업 활용 조건을 별도로 확인해야 합니다. 데이터셋 구성표는 RAG 원문 생성 근거가 아니라 `citation_only` 메타데이터로만 보관합니다.
