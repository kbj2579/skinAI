from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .bedrock_client import DEFAULT_BEDROCK_MODEL_ID
from .models import CLASS_DISPLAY_KO, VALID_LABELS
from .service import generate_guidance


LABELS = [
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


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simple acne RAG MVP without backend/frontend integration."
    )
    parser.add_argument("--label", choices=sorted(VALID_LABELS), help="Predicted lesion class.")
    parser.add_argument("--symptoms", default="", help="User symptom text.")
    parser.add_argument("--image-id", default="manual-input")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--llm", choices=["template", "bedrock"], default="template")
    parser.add_argument("--bedrock-model-id", default=DEFAULT_BEDROCK_MODEL_ID)
    parser.add_argument("--bedrock-region", default=None)
    parser.add_argument("--bedrock-max-tokens", type=int, default=1200)
    parser.add_argument("--bedrock-temperature", type=float, default=0.0)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of markdown.")
    return parser.parse_args()


def prompt_label() -> str:
    print("병변 클래스를 선택하세요.")
    for idx, label in enumerate(LABELS, start=1):
        print(f"{idx}. {CLASS_DISPLAY_KO[label]} ({label})")

    while True:
        raw = input("번호 또는 영문 클래스명 입력: ").strip()
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(LABELS):
                return LABELS[index - 1]
        if raw in VALID_LABELS:
            return raw
        print("다시 입력하세요. 예: 4 또는 Pustules")


def main() -> None:
    configure_stdout()
    args = parse_args()
    label = args.label or prompt_label()
    symptoms = args.symptoms
    if not symptoms:
        symptoms = input("증상 설명 입력(없으면 Enter): ").strip()

    result = generate_guidance(
        label,
        symptoms,
        image_id=args.image_id,
        top_k=args.top_k,
        corpus_path=args.corpus,
        use_bedrock=args.llm == "bedrock",
        bedrock_model_id=args.bedrock_model_id,
        bedrock_region=args.bedrock_region,
        bedrock_max_tokens=args.bedrock_max_tokens,
        bedrock_temperature=args.bedrock_temperature,
    )
    if args.json:
        payload = {
            "llm": args.llm,
            "prediction": result.prediction,
            "retrieved_evidence": result.retrieved_evidence,
            "sections": result.sections,
            "markdown": result.markdown,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(result.markdown)


if __name__ == "__main__":
    main()
