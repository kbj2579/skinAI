from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from acne_rag_solution.corpus import generation_allowed, load_corpus
from acne_rag_solution.generator import build_solution
from acne_rag_solution.models import Prediction
from acne_rag_solution.retriever import retrieve
from acne_rag_solution.service import generate_guidance


EXAMPLES_PATH = Path(__file__).resolve().parents[1] / "examples" / "all_class_examples.json"
HIERARCHICAL_EXAMPLES_PATH = (
    Path(__file__).resolve().parents[1] / "examples" / "hierarchical_14node_examples.json"
)
LEGACY_LABELS = ["Blackheads", "Whiteheads", "Papules", "Pustules", "Cyst"]
HIERARCHICAL_LABELS = [
    "blackhead",
    "whitehead",
    "papule",
    "pustule",
    "cystnnodule",
    "complexacne",
    "milia",
    "rosacea",
    "seborrheic",
    "sebdermatitis",
    "atopic",
    "psoriasis",
    "normal",
    "abnormal",
]
REQUIRED_SECTIONS = [
    "모델 분류 결과",
    "가능한 의미",
    "일반 관리 방법",
    "성분 선택 참고",
    "피부과 방문이 필요한 경우",
    "근거 출처",
    "주의",
]


class AcneRagEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = load_corpus()

    def test_corpus_has_expanded_evidence_volume(self) -> None:
        self.assertGreaterEqual(len(self.corpus), 70)
        self.assertGreaterEqual(sum(generation_allowed(item) for item in self.corpus), 60)

    def test_legacy_classes_generate_cited_solution(self) -> None:
        for label in LEGACY_LABELS:
            prediction = Prediction.from_dict({"pred_label": label, "confidence": 0.86})
            retrieved = retrieve(prediction, self.corpus, user_symptoms="통증", top_k=5)
            result = build_solution(prediction, retrieved, user_symptoms="통증")
            self.assertGreaterEqual(len(result.retrieved_evidence), 1)
            self.assertIn("근거 출처", result.markdown)
            self.assertIn("의료 진단", result.markdown)

    def test_hierarchical_classes_generate_cited_solution(self) -> None:
        for label in HIERARCHICAL_LABELS:
            prediction = Prediction.from_dict({"pred_label": label, "model_version": "14node-test"})
            retrieved = retrieve(prediction, self.corpus, user_symptoms="붉음 통증 변화", top_k=5)
            result = build_solution(prediction, retrieved, user_symptoms="붉음 통증 변화")
            self.assertEqual(result.prediction["pred_label"], label)
            self.assertGreaterEqual(len(result.retrieved_evidence), 1)
            for section in REQUIRED_SECTIONS:
                self.assertIn(section, result.markdown, msg=f"{label} missing {section}")

    def test_solution_uses_lesion_label_without_confidence_branching(self) -> None:
        prediction = Prediction.from_dict({"pred_label": "papule", "confidence": 0.45})
        retrieved = retrieve(prediction, self.corpus, top_k=5)
        result = build_solution(prediction, retrieved)
        self.assertNotIn("low_confidence", result.sections["모델 분류 결과"])
        self.assertIn("염증성 여드름", result.sections["가능한 의미"])

    def test_prediction_confidence_is_optional(self) -> None:
        prediction = Prediction.from_dict({"pred_label": "whitehead"})
        retrieved = retrieve(prediction, self.corpus, top_k=5)
        result = build_solution(prediction, retrieved)
        self.assertIsNone(result.prediction["confidence"])
        self.assertNotIn("신뢰도", result.markdown)

    def test_simple_service_generates_guidance_from_label_and_symptoms(self) -> None:
        result = generate_guidance("pustule", "고름이 있고 만지면 아픔")
        self.assertEqual(result.prediction["pred_label"], "pustule")
        self.assertIn("고름", result.markdown)
        self.assertIn("사용자 입력 증상: 고름이 있고 만지면 아픔", result.markdown)
        self.assertGreaterEqual(len(result.retrieved_evidence), 1)

    def test_legacy_class_examples_pass_template_validation(self) -> None:
        examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
        self.assertEqual({item["pred_label"] for item in examples}, set(LEGACY_LABELS))
        for example in examples:
            result = generate_guidance(example["pred_label"], example["symptoms"], image_id=example["name"])
            self.assertGreaterEqual(len(result.retrieved_evidence), 1)
            for term in [*example["expected_terms"], *REQUIRED_SECTIONS]:
                self.assertIn(term, result.markdown, msg=f"{example['name']} missing {term}")

    def test_hierarchical_class_examples_pass_template_validation(self) -> None:
        examples = json.loads(HIERARCHICAL_EXAMPLES_PATH.read_text(encoding="utf-8"))
        self.assertEqual({item["pred_label"] for item in examples}, set(HIERARCHICAL_LABELS))
        for example in examples:
            result = generate_guidance(example["pred_label"], example["symptoms"], image_id=example["name"])
            self.assertGreaterEqual(len(result.retrieved_evidence), 1)
            for term in [*example["expected_terms"], *REQUIRED_SECTIONS]:
                self.assertIn(term, result.markdown, msg=f"{example['name']} missing {term}")

    def test_bedrock_generation_replaces_template_markdown(self) -> None:
        with patch("acne_rag_solution.service.invoke_claude", return_value="## Claude 응답\n근거 기반 안내") as mocked:
            result = generate_guidance("pustule", "고름이 있음", use_bedrock=True)
        self.assertEqual(result.markdown, "## Claude 응답\n근거 기반 안내")
        self.assertIn("prediction=", mocked.call_args.args[0])

    def test_deep_inflammatory_class_recommends_dermatology(self) -> None:
        prediction = Prediction.from_dict({"pred_label": "cystnnodule", "confidence": 0.91})
        retrieved = retrieve(prediction, self.corpus, user_symptoms="아프고 반복됨", top_k=5)
        result = build_solution(prediction, retrieved, user_symptoms="아프고 반복됨")
        text = result.markdown
        self.assertIn("피부과", text)
        self.assertIn("흉터", text)

    def test_citation_only_sources_are_not_retrieved_by_default(self) -> None:
        prediction = Prediction.from_dict({"pred_label": "milia", "confidence": 0.9})
        retrieved = retrieve(prediction, self.corpus, top_k=10)
        ids = {item.chunk.id for item in retrieved}
        self.assertNotIn("milia_statpearls_citation_only", ids)
        self.assertNotIn("hierarchical_14node_dataset_plan_citation_only", ids)

    def test_each_hierarchical_class_retrieves_management_and_ingredient_evidence(self) -> None:
        for label in HIERARCHICAL_LABELS:
            prediction = Prediction.from_dict({"pred_label": label})
            retrieved = retrieve(prediction, self.corpus, user_symptoms="좋은 성분 관리", top_k=10)
            self.assertGreaterEqual(len(retrieved), 1, msg=f"{label} retrieved no evidence")
            topic_sets = [set(item.chunk.topic_tags) for item in retrieved]
            self.assertTrue(
                any({"beneficial_management", "management", "self_care"} & topics for topics in topic_sets),
                msg=f"{label} missing management evidence",
            )
            self.assertTrue(
                any({"beneficial_ingredients", "ingredient_safety"} & topics for topics in topic_sets),
                msg=f"{label} missing ingredient evidence",
            )

    def test_template_includes_ingredient_guidance_by_default(self) -> None:
        result = generate_guidance("rosacea", "얼굴이 붉고 화끈거림")
        self.assertIn("성분 선택 참고", result.markdown)
        self.assertIn("자외선차단제", result.markdown)
        self.assertIn("용량", result.llm_prompt)


if __name__ == "__main__":
    unittest.main()
