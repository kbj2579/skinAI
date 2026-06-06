import logging
from typing import Optional

import boto3

from app.core.config import settings

logger = logging.getLogger(__name__)

_runtime_client = None   # bedrock-runtime  → converse
_agent_client   = None   # bedrock-agent-runtime → retrieve


def _get_runtime_client():
    global _runtime_client
    if _runtime_client is None:
        _runtime_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
    return _runtime_client


def _get_agent_client():
    global _agent_client
    if _agent_client is None:
        _agent_client = boto3.client(
            "bedrock-agent-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
    return _agent_client


def _retrieve_kb(query: str) -> str:
    """KB에서 관련 문서 검색. 없거나 실패하면 빈 문자열 반환."""
    if not settings.use_bedrock_rag:
        return ""
    try:
        response = _get_agent_client().retrieve(
            knowledgeBaseId=settings.bedrock_knowledge_base_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": 3}
            },
        )
        texts = [
            r["content"]["text"]
            for r in response.get("retrievalResults", [])
            if r.get("score", 0) > 0.3 and r.get("content", {}).get("text")
        ]
        return "\n\n---\n\n".join(texts)
    except Exception as e:
        logger.debug("KB retrieve failed: %s", e)
        return ""


def _build_system(analysis_context: Optional[dict], kb_context: str) -> str:
    parts = [
        "당신은 피부 건강 관리 보조 AI입니다.",
        "피부 관련 일반 질문과 사용자 개인 분석 결과 기반 질문 모두 친절하고 전문적으로 답변하세요.",
        "답변 마지막에 항상 '본 답변은 AI 보조 분석이며 의학적 진단이 아닙니다.'를 포함하세요.",
    ]

    if analysis_context:
        ctx = analysis_context
        conditions_str = ", ".join(
            f"{c['label']}({c['score']:.0%})"
            for c in ctx.get("conditions", [])
        )
        lifestyle_parts = []
        if ctx.get("smoking"):
            lifestyle_parts.append("흡연")
        if ctx.get("drinking"):
            lifestyle_parts.append("음주")

        parts.append("\n[사용자 분석 결과 — 이 정보를 바탕으로 개인화된 답변을 제공하세요]")
        parts.append(f"분석 유형: {ctx.get('analysis_type', '미입력')}")
        parts.append(f"분석 부위: {ctx.get('body_part') or '미입력'}")
        parts.append(f"감지된 상태: {conditions_str}")
        parts.append(f"위험도: {ctx.get('risk_level', '미입력')}")
        parts.append(f"신뢰도: {ctx.get('confidence', 0):.0%}")
        parts.append(f"생활습관: {', '.join(lifestyle_parts) or '해당 없음'}")

    if kb_context:
        parts.append("\n[관련 의학 문서 — 참고하되, 문서에 없는 내용은 일반 의학 지식으로 답변하세요]")
        parts.append(kb_context)

    return "\n".join(parts)


def chat(
    message: str,
    history: list[dict],
    analysis_context: Optional[dict] = None,
) -> str:
    kb_context = _retrieve_kb(message)
    system_text = _build_system(analysis_context, kb_context)

    messages = [
        {"role": m["role"], "content": [{"text": m["content"]}]}
        for m in history
    ]
    messages.append({"role": "user", "content": [{"text": message}]})

    response = _get_runtime_client().converse(
        modelId=settings.bedrock_model_id,
        system=[{"text": system_text}],
        messages=messages,
        inferenceConfig={"maxTokens": 1024, "temperature": 0.7},
    )

    reply = response["output"]["message"]["content"][0]["text"]
    logger.info("Chat reply — %d chars", len(reply))
    return reply
