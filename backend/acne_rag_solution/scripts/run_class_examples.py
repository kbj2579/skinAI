from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from acne_rag_solution.bedrock_client import DEFAULT_BEDROCK_MODEL_ID
from acne_rag_solution.service import generate_guidance


DEFAULT_EXAMPLES_PATH = (
    Path(__file__).resolve().parents[1] / "examples" / "hierarchical_14node_examples.json"
)
REQUIRED_SECTIONS = [
    "모델 분류 결과",
    "가능한 의미",
    "일반 관리 방법",
    "성분 선택 참고",
    "피부과 방문이 필요한 경우",
    "근거 출처",
    "주의",
]


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run class examples through the skin-lesion RAG pipeline.")
    parser.add_argument("--examples", type=Path, default=DEFAULT_EXAMPLES_PATH)
    parser.add_argument("--llm", choices=["template", "bedrock"], default="template")
    parser.add_argument("--bedrock-model-id", default=DEFAULT_BEDROCK_MODEL_ID)
    parser.add_argument("--bedrock-region", default=None)
    parser.add_argument("--bedrock-max-tokens", type=int, default=900)
    parser.add_argument("--bedrock-temperature", type=float, default=0.0)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--show-full", action="store_true", help="Print full markdown for each example.")
    return parser.parse_args()


def main() -> None:
    configure_stdout()
    args = parse_args()
    examples = json.loads(args.examples.read_text(encoding="utf-8"))

    failures: list[str] = []
    for example in examples:
        result = generate_guidance(
            example["pred_label"],
            example["symptoms"],
            image_id=example["name"],
            top_k=args.top_k,
            use_bedrock=args.llm == "bedrock",
            bedrock_model_id=args.bedrock_model_id,
            bedrock_region=args.bedrock_region,
            bedrock_max_tokens=args.bedrock_max_tokens,
            bedrock_temperature=args.bedrock_temperature,
        )
        missing = [
            term
            for term in [*example["expected_terms"], *REQUIRED_SECTIONS]
            if term not in result.markdown
        ]
        if missing:
            failures.append(f"{example['name']}: missing {missing}")

        print(f"## {example['name']} ({example['pred_label']})")
        print(f"symptoms: {example['symptoms']}")
        print(f"retrieved: {', '.join(item['id'] for item in result.retrieved_evidence)}")
        print(f"check: {'OK' if not missing else 'FAIL'}")
        if missing:
            print(f"missing: {', '.join(missing)}")
        if args.show_full:
            print(result.markdown)
        else:
            first_lines = result.markdown.splitlines()[:12]
            print("\n".join(first_lines))
        print()

    if failures:
        raise SystemExit("Example validation failed:\n" + "\n".join(failures))


if __name__ == "__main__":
    main()
