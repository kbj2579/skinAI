from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .bedrock_client import DEFAULT_BEDROCK_MODEL_ID
from .models import Prediction
from .service import generate_guidance_from_prediction


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate source-grounded Korean skin-lesion guidance from a vision-model prediction JSON."
    )
    parser.add_argument("--prediction", type=Path, required=True, help="Path to standardized prediction JSON.")
    parser.add_argument("--symptoms", default="", help="Optional user symptom text.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--llm", choices=["template", "bedrock"], default="template")
    parser.add_argument("--bedrock-model-id", default=DEFAULT_BEDROCK_MODEL_ID)
    parser.add_argument("--bedrock-region", default=None)
    parser.add_argument("--bedrock-max-tokens", type=int, default=1200)
    parser.add_argument("--bedrock-temperature", type=float, default=0.0)
    parser.add_argument("--json", action="store_true", help="Print full JSON instead of markdown.")
    parser.add_argument("--show-prompt", action="store_true", help="Include the LLM prompt in JSON output.")
    return parser.parse_args()


def run(args: argparse.Namespace) -> dict[str, Any]:
    with args.prediction.open("r", encoding="utf-8") as f:
        prediction = Prediction.from_dict(json.load(f))
    result = generate_guidance_from_prediction(
        prediction,
        args.symptoms,
        top_k=args.top_k,
        corpus_path=args.corpus,
        use_bedrock=args.llm == "bedrock",
        bedrock_model_id=args.bedrock_model_id,
        bedrock_region=args.bedrock_region,
        bedrock_max_tokens=args.bedrock_max_tokens,
        bedrock_temperature=args.bedrock_temperature,
    )
    payload = {
        "llm": args.llm,
        "prediction": result.prediction,
        "retrieved_evidence": result.retrieved_evidence,
        "sections": result.sections,
        "markdown": result.markdown,
    }
    if args.show_prompt:
        payload["llm_prompt"] = result.llm_prompt
    return payload


def main() -> None:
    configure_stdout()
    args = parse_args()
    payload = run(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["markdown"])


if __name__ == "__main__":
    main()
