from __future__ import annotations

from pathlib import Path

from .bedrock_client import BedrockClaudeConfig, invoke_claude
from .corpus import load_corpus
from .generator import SolutionResult, build_solution
from .models import Prediction
from .retriever import retrieve


def generate_guidance_from_prediction(
    prediction: Prediction,
    user_symptoms: str = "",
    *,
    top_k: int = 5,
    corpus_path: Path | None = None,
    use_bedrock: bool = False,
    bedrock_model_id: str | None = None,
    bedrock_region: str | None = None,
    bedrock_max_tokens: int = 1200,
    bedrock_temperature: float = 0.0,
) -> SolutionResult:
    """Generate RAG guidance from a standardized prediction."""
    corpus = load_corpus(corpus_path)
    retrieved = retrieve(
        prediction,
        corpus,
        user_symptoms=user_symptoms,
        top_k=top_k,
    )
    result = build_solution(prediction, retrieved, user_symptoms=user_symptoms)
    if not use_bedrock:
        return result

    config = BedrockClaudeConfig(
        model_id=bedrock_model_id or BedrockClaudeConfig().model_id,
        region_name=bedrock_region or BedrockClaudeConfig().region_name,
        max_tokens=bedrock_max_tokens,
        temperature=bedrock_temperature,
    )
    claude_markdown = invoke_claude(result.llm_prompt, config)
    return SolutionResult(
        prediction=result.prediction,
        retrieved_evidence=result.retrieved_evidence,
        sections=result.sections,
        markdown=claude_markdown,
        llm_prompt=result.llm_prompt,
    )


def generate_guidance(
    pred_label: str,
    user_symptoms: str = "",
    *,
    model_version: str = "manual-label-mvp",
    image_id: str = "manual-input",
    top_k: int = 5,
    corpus_path: Path | None = None,
    use_bedrock: bool = False,
    bedrock_model_id: str | None = None,
    bedrock_region: str | None = None,
    bedrock_max_tokens: int = 1200,
    bedrock_temperature: float = 0.0,
) -> SolutionResult:
    """Generate RAG guidance from a lesion class and optional symptom text."""
    prediction = Prediction.from_dict(
        {
            "pred_label": pred_label,
            "model_version": model_version,
            "image_id": image_id,
        }
    )
    return generate_guidance_from_prediction(
        prediction,
        user_symptoms,
        top_k=top_k,
        corpus_path=corpus_path,
        use_bedrock=use_bedrock,
        bedrock_model_id=bedrock_model_id,
        bedrock_region=bedrock_region,
        bedrock_max_tokens=bedrock_max_tokens,
        bedrock_temperature=bedrock_temperature,
    )
