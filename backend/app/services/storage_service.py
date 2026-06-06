import logging
import uuid

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.config import Config as BotoConfig
    _BOTO3_AVAILABLE = True
except ImportError:
    _BOTO3_AVAILABLE = False


def _is_configured() -> bool:
    from app.core.config import settings
    return (
        _BOTO3_AVAILABLE
        and bool(settings.storage_bucket)
        and bool(settings.aws_access_key_id or settings.storage_access_key)
    )


def _get_client():
    from app.core.config import settings

    access_key = settings.aws_access_key_id or settings.storage_access_key
    secret_key = settings.aws_secret_access_key or settings.storage_secret_key
    region     = settings.storage_region or settings.aws_region

    kwargs: dict = {
        "aws_access_key_id":     access_key,
        "aws_secret_access_key": secret_key,
        "config": BotoConfig(signature_version="s3v4"),
        "region_name": region,
    }

    # AWS 네이티브 S3: endpoint_url 생략
    # Cloudflare R2 / MinIO: endpoint_url 사용
    if not settings.use_native_s3:
        kwargs["endpoint_url"] = settings.storage_endpoint

    return boto3.client("s3", **kwargs)


def upload(image_bytes: bytes, analysis_type: str, content_type: str = "image/jpeg") -> str:
    """S3(또는 R2)에 이미지 업로드 후 key 반환. 미설정 시 Mock key."""
    key = f"user_image/{analysis_type}/{uuid.uuid4()}.jpg"

    if not _is_configured():
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
        logger.info("S3 upload OK: %s (%d bytes)", key, len(image_bytes))
    except Exception as exc:
        logger.warning("S3 upload failed (%s) — using mock key", exc)

    return key


def delete(key: str) -> bool:
    """S3에서 이미지 삭제. 성공 시 True."""
    if not key or not _is_configured():
        return False

    from app.core.config import settings
    try:
        _get_client().delete_object(Bucket=settings.storage_bucket, Key=key)
        logger.info("S3 delete OK: %s", key)
        return True
    except Exception as exc:
        logger.warning("S3 delete failed (%s)", exc)
        return False


def get_presigned_url(key: str, expires_in: int = 300) -> str:
    """Presigned URL 생성 (기본 5분). 미설정 시 빈 문자열."""
    if not key or not _is_configured():
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
