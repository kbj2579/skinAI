from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_BEDROCK_MODEL_ID = "global.anthropic.claude-sonnet-4-6"

DEFAULT_SYSTEM_PROMPT = """\
너는 피부 병변 이미지 분류 결과와 근거 문서를 바탕으로 한국어 안내문을 작성하는 의료 보조 시스템이다.
진단 확정, 처방, 약물 용량, 약물 변경 지시를 하지 않는다.
제공된 근거 문서 밖의 의학적 주장을 추가하지 않는다.
심한 통증, 빠른 악화, 출혈, 발열, 넓은 염증, 흉터 위험, 색/크기 변화는 진료 권고를 포함한다.
항상 이 안내가 의료 진단이나 처방이 아니라는 점을 명시한다.
이모지, 경고 아이콘, 장식 특수문자는 사용하지 않는다.
전체 답변은 간결하게 작성하고, Markdown 제목과 bullet만 사용한다.
"""


@dataclass(frozen=True)
class BedrockClaudeConfig:
    model_id: str = os.getenv("ACNE_RAG_BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID)
    region_name: str | None = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    max_tokens: int = int(os.getenv("ACNE_RAG_BEDROCK_MAX_TOKENS", "1200"))
    temperature: float = float(os.getenv("ACNE_RAG_BEDROCK_TEMPERATURE", "0"))
    system_prompt: str = DEFAULT_SYSTEM_PROMPT


def invoke_claude(prompt: str, config: BedrockClaudeConfig | None = None) -> str:
    """Call Claude through Amazon Bedrock Converse API."""
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is required for Bedrock Claude calls. Install boto3 first.") from exc

    cfg = config or BedrockClaudeConfig()
    client_kwargs = {}
    if cfg.region_name:
        client_kwargs["region_name"] = cfg.region_name
    client = boto3.client("bedrock-runtime", **client_kwargs)

    response = client.converse(
        modelId=cfg.model_id,
        system=[{"text": cfg.system_prompt}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={
            "maxTokens": cfg.max_tokens,
            "temperature": cfg.temperature,
        },
    )
    content = response["output"]["message"]["content"]
    text = "".join(part.get("text", "") for part in content).strip()
    if not text:
        raise RuntimeError("Bedrock Claude returned an empty response.")
    return text
