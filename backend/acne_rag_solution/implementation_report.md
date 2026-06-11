# Acne RAG Solution 수행 보고서

## 1. 수행 목표

비전 모델이 추론한 피부 병변 클래스와 사용자가 입력한 증상 설명을 바탕으로, 근거 문서를 검색하고 AWS Bedrock Claude Sonnet 또는 로컬 템플릿으로 한국어 안내문을 생성하는 간이 RAG 시스템을 구축했다.

본 시스템은 의료 진단기나 처방 시스템이 아니다. 병변 분류 결과 설명, 일반 관리 방향, 성분 선택 참고, 피부과 방문 기준, 근거 출처 제공을 목적으로 한다.

## 2. 주요 작업 내용

1. 기존 여드름 5클래스 RAG 구조를 14노드 피부 병변 체계로 확장했다.
   - 기존 호환 라벨: `Blackheads`, `Whiteheads`, `Papules`, `Pustules`, `Cyst`
   - 신규 14노드 라벨: `blackhead`, `whitehead`, `papule`, `pustule`, `cystnnodule`, `complexacne`, `milia`, `rosacea`, `seborrheic`, `sebdermatitis`, `atopic`, `psoriasis`, `normal`, `abnormal`
   - 신규 라벨과 기존 대문자 여드름 라벨이 같은 근거를 찾을 수 있도록 검색 alias를 추가했다.

2. 클래스별 RAG 응답 정책을 확장했다.
   - 모든 클래스에 대해 “가능한 의미”, “일반 관리 방법”, “성분 선택 참고”, “피부과 방문 기준”을 기본 생성하도록 구성했다.
   - 사용자가 성분 추천을 따로 입력하지 않아도 “성분 선택 참고” 섹션이 항상 출력된다.
   - 약물 용량, 처방, 특정 제품명, 진단 확정 표현은 생성하지 않도록 프롬프트와 템플릿에 제한을 유지했다.

3. 라이선스 안전 기준으로 근거 코퍼스를 확장했다.
   - `evidence_corpus.json`을 57개에서 143개 chunk/card로 확장했다.
   - 현재 구성:
     - `cc_by`: 83개
     - `public_domain`: 51개
     - `citation_only`: 9개
   - 모든 14노드 클래스가 생성 가능 근거를 최소 2개 이상 갖고, 발표용 확장 클래스는 대체로 7개 이상 갖도록 보강했다.
   - 기본 생성 대상은 `public_domain`, `CC0`, `CC BY`에 한정했다.
   - StatPearls, 데이터셋 구성표, 재사용 조건이 불명확하거나 NC/ND 성격이 있는 자료는 `citation_only`로 분리했다.
   - NIAMS, CDC, NCI는 각 기관의 공식 재사용 정책을 확인했고, PubMed Central 논문은 Europe PMC 메타데이터의 `license=cc by` 또는 논문 페이지의 CC BY 표기를 기준으로 확인했다.
   - CC BY-NC로 확인된 논문은 원문 RAG 저장 대상에서 제외하고, 생성 허용 카드로 추가하지 않았다.
   - `docs/license_audit_report.md`, `docs/evidence_sources_register.csv`, `docs/evidence_cards_register.csv`를 생성해 카드별 출처와 라이선스 판단을 추적 가능하게 했다.

4. 추가한 주요 근거 출처
   - NIAMS Acne, Rosacea, Atopic Dermatitis, Psoriasis, Healthy Skin 문서
   - CDC Skin Cancer Symptoms 및 Agency Materials 재사용 정책
   - NCI Skin Cancer PDQ 및 Copyright/Re-use 정책
   - PubMed Central CC BY 논문:
     - `Seborrheic Dermatitis and Dandruff: A Comprehensive Review`
     - `Milia En Plaque Associated With Prayer-Related Frictional Changes`
     - `Advances in the pathogenesis of rosacea`
     - `Seborrheic Dermatitis Revisited`
     - `Atopic Dermatitis Disease Features`
     - `Unraveling Atopic Dermatitis`
     - `The Pathophysiology of Atopic Dermatitis and Psoriasis in Children`
     - `Psoriasis Beyond the Skin`
     - `Dietary Principles in Psoriasis`
   - 프로젝트 제공 14노드 데이터셋 구성표는 라이선스 검토 필요 메타데이터로만 보관했다.

5. 실행 예시와 검증 스크립트를 추가했다.
   - `examples/hierarchical_14node_examples.json`: 14개 클래스 전체 입력 예시
   - `scripts/run_class_examples.py`: 기본값을 14노드 예시 검증으로 변경
   - 기존 5클래스 예시 `examples/all_class_examples.json`도 유지

6. AWS Bedrock 연결 구조는 유지했다.
   - 기본 모델: `global.anthropic.claude-sonnet-4-6`
   - 실행 옵션: `--llm bedrock`
   - 구조는 Bedrock Knowledge Base가 아니라, 로컬 JSON 코퍼스를 검색한 뒤 Bedrock Runtime Converse API로 Claude Sonnet을 호출하는 직접 구현 RAG 방식이다.

## 3. 주요 파일 구조

```text
acne_rag_solution/
  evidence_corpus.json
  models.py
  corpus.py
  retriever.py
  generator.py
  bedrock_client.py
  service.py
  simple_mvp.py
  cli.py
  sample_prediction.json
  docs/
    evidence_cards_register.csv
    evidence_sources_register.csv
    license_audit_report.md
  examples/
    all_class_examples.json
    hierarchical_14node_examples.json
  scripts/
    rebuild_by_class.py
    run_class_examples.py
  tests/
    test_engine.py
```

## 4. 검증 결과

단위 테스트:

```powershell
python -m unittest acne_rag_solution.tests.test_engine
```

결과:

```text
Ran 13 tests
OK
```

14노드 예시 검증:

```powershell
python .\acne_rag_solution\scripts\run_class_examples.py --llm template
```

결과:

```text
14개 클래스 모두 check: OK
```

확인한 항목:

- 기존 5클래스와 신규 14노드 라벨 모두 표준 JSON 입력으로 처리된다.
- 모든 클래스 출력에 근거 출처가 1개 이상 포함된다.
- `citation_only` 근거는 기본 검색 결과에서 제외된다.
- `cystnnodule`은 피부과 상담과 흉터 위험 안내가 포함된다.
- `rosacea`, `atopic`, `psoriasis`, `sebdermatitis`, `milia`, `normal`, `abnormal`도 기본 관리와 성분 선택 참고가 출력된다.

## 5. 주요 실행 명령

로컬 템플릿 실행:

```powershell
python -m acne_rag_solution.simple_mvp --label rosacea --symptoms "얼굴 중앙이 자주 붉고 화끈거림"
```

Bedrock Claude Sonnet 실행:

```powershell
python -m acne_rag_solution.simple_mvp --label rosacea --symptoms "얼굴 중앙이 자주 붉고 화끈거림" --llm bedrock
```

14노드 전체 예시 검증:

```powershell
python .\acne_rag_solution\scripts\run_class_examples.py --llm template
```

기존 5클래스 예시 검증:

```powershell
python .\acne_rag_solution\scripts\run_class_examples.py --examples .\acne_rag_solution\examples\all_class_examples.json --llm template
```

## 6. S3 업로드 정보

기존 업로드 방식은 원본 이미지 데이터셋이 아니라 `acne_rag_solution` 코드, RAG corpus, 예시, 테스트, 보고서 산출물을 S3에 올리는 방식이다.

기존 S3 위치:

```text
s3://acne-rag-solution-727847798739-20260525/deliverables/acne_rag_solution_20260525.zip
s3://acne-rag-solution-727847798739-20260525/deliverables/acne_rag_solution_kcc_license_audit_20260606.zip
s3://acne-rag-solution-727847798739-20260525/expanded/acne_rag_solution/
s3://acne-rag-solution-727847798739-20260525/reports/implementation_report.md
s3://acne-rag-solution-727847798739-20260525/reports/license_audit_report.md
s3://acne-rag-solution-727847798739-20260525/reports/evidence_sources_register.csv
s3://acne-rag-solution-727847798739-20260525/reports/evidence_cards_register.csv
```

## 7. 주의 및 한계

- 본 시스템은 의료 진단이나 처방을 제공하지 않는다.
- 성분 안내는 후보 성분과 주의점 수준이며, 특정 제품명·용량·사용 횟수·처방 변경을 안내하지 않는다.
- 현재 검색은 vector DB가 아니라 규칙 기반 검색이다. 추후 고도화 시 SQLite, FAISS, pgvector, OpenSearch 등으로 확장할 수 있다.
- 이미지 데이터셋의 재배포 및 상업 활용 조건은 각 제공처별로 별도 검토가 필요하다.
