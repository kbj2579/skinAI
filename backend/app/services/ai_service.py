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
    logger.info("SageMaker OK: %s → %s", analysis_type, result.get("risk_level"))
    return ModelResult(**result)


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
