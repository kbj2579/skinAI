import logging

import httpx

from app.core.config import settings
from app.schemas.analysis import ModelResult
from app.services import mock_ai_service

logger = logging.getLogger(__name__)


async def predict(image_bytes: bytes, analysis_type: str) -> ModelResult:
    url = f"{settings.ai_model_base_url}/predict/{analysis_type}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                files={"file": ("image.jpg", image_bytes, "image/jpeg")},
            )
            response.raise_for_status()

        return ModelResult(**response.json())
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning(
            "Model server unavailable for %s (%s). Using local mock.",
            analysis_type,
            exc,
        )
        return mock_ai_service.predict(image_bytes, analysis_type)
