import logging
import uuid

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.config import Config as BotoConfig

    _BOTO3_AVAILABLE = True
except ImportError:
    _BOTO3_AVAILABLE = False


def _is_real_storage() -> bool:
    """Return True when object storage is configured and boto3 is available."""
    from app.core.config import settings

    return (
        _BOTO3_AVAILABLE
        and bool(settings.storage_endpoint)
        and bool(settings.storage_access_key)
        and bool(settings.storage_secret_key)
        and bool(settings.storage_bucket)
    )


def _get_client():
    from app.core.config import settings

    return boto3.client(
        "s3",
        endpoint_url=settings.storage_endpoint,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
        config=BotoConfig(signature_version="s3v4"),
        region_name=settings.storage_region,
    )


def upload(image_bytes: bytes, analysis_type: str, content_type: str = "image/jpeg") -> str:
    key = f"{analysis_type}/{uuid.uuid4()}.jpg"

    if not _is_real_storage():
        logger.debug("Storage mock: %s", key)
        return key

    from app.core.config import settings

    try:
        _get_client().put_object(
            Bucket=settings.storage_bucket,
            Key=key,
            Body=image_bytes,
            ContentType=content_type,
        )
        logger.info("Storage upload OK: %s (%d bytes)", key, len(image_bytes))
    except Exception as exc:
        logger.warning("Storage upload failed (%s) — using mock key", exc)

    return key


def get_presigned_url(key: str, expires_in: int = 300) -> str:
    if not key or not _is_real_storage():
        return ""

    from app.core.config import settings

    try:
        return _get_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.storage_bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    except Exception as exc:
        logger.warning("Presigned URL failed (%s)", exc)
        return ""
