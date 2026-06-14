import json
import logging

import httpx

from app.core.config import settings
from app.schemas.analysis import ModelResult
from app.services import mock_ai_service

logger = logging.getLogger(__name__)


# ── SageMaker 추론 ────────────────────────────────────────────────
async def _predict_sagemaker(image_bytes: bytes, analysis_type: str) -> ModelResult:
    """AWS SageMaker 엔드포인트 호출."""
    import boto3
    client = boto3.client(
        "sagemaker-runtime",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    import asyncio
    response = await asyncio.to_thread(
        client.invoke_endpoint,
        EndpointName=settings.sagemaker_endpoint_name,
        ContentType="image/jpeg",
        Accept="application/json",
        Body=image_bytes,
        # 분석 유형을 커스텀 헤더로 전달
        CustomAttributes=f"analysis_type={analysis_type}",
    )

    result = json.loads(response["Body"].read())

    # 모델이 {conditions, risk_level, confidence} 형식으로 반환하면 그대로 사용
    if "conditions" in result and "risk_level" in result:
        logger.info("SageMaker OK: %s → %s", analysis_type, result.get("risk_level"))
        return ModelResult(**result)

    # 모델이 {highest_class_name, probability} 형식으로 반환하면 변환
    class_name = result.get("highest_class_name", "abnormal")
    probability = float(result.get("probability", 0.0))

    # top_k_probabilities가 있으면 conditions로 변환
    top_k = result.get("top_k_probabilities") or result.get("top_k") or {}
    if top_k and isinstance(top_k, dict):
        conditions = [{"label": k, "score": round(v, 4)} for k, v in sorted(top_k.items(), key=lambda x: x[1], reverse=True)]
    else:
        conditions = [{"label": class_name, "score": round(probability, 4)}]

    # risk_level 결정
    if class_name == "normal":
        risk_level = "normal"
    elif probability >= 0.80:
        risk_level = "danger"
    elif probability >= 0.60:
        risk_level = "suspicious"
    else:
        risk_level = "mild"

    logger.info("SageMaker OK (converted): %s → %s (%.2f)", class_name, risk_level, probability)
    return ModelResult(conditions=conditions, risk_level=risk_level, confidence=probability)


# ── 로컬 모델 서버 추론 ───────────────────────────────────────────
async def _predict_local(image_bytes: bytes, analysis_type: str) -> ModelResult:
    """로컬 / EC2 모델 서버 HTTP 호출."""
    url = f"{settings.ai_model_base_url}/predict/{analysis_type}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            files={"file": ("image.jpg", image_bytes, "image/jpeg")},
        )
        response.raise_for_status()
    return ModelResult(**response.json())


# ── 메인 predict (우선순위: SageMaker → 로컬 서버 → Mock) ──────────
async def predict(image_bytes: bytes, analysis_type: str) -> ModelResult:
    # 1순위: SageMaker
    if settings.use_sagemaker:
        try:
            return await _predict_sagemaker(image_bytes, analysis_type)
        except Exception as exc:
            logger.warning("SageMaker failed (%s) — trying local server", exc)

    # 2순위: 로컬 모델 서버
    try:
        return await _predict_local(image_bytes, analysis_type)
    except Exception as exc:
        logger.warning("Local model server unavailable (%s) — using mock", exc)

    # 3순위: Mock (항상 동작)
    return mock_ai_service.predict(image_bytes, analysis_type)
