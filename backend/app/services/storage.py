from uuid import UUID

import boto3
from botocore.client import Config

from app.core.config import get_settings

settings = get_settings()


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_bucket() -> None:
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.minio_bucket)
    except Exception:
        try:
            client.create_bucket(Bucket=settings.minio_bucket)
        except Exception:
            pass


def upload_file(storage_path: str, data: bytes, content_type: str) -> None:
    ensure_bucket()
    client = get_s3_client()
    client.put_object(
        Bucket=settings.minio_bucket,
        Key=storage_path,
        Body=data,
        ContentType=content_type,
    )


def generate_presigned_url(storage_path: str) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket, "Key": storage_path},
        ExpiresIn=settings.presigned_url_expire_seconds,
    )


def get_file(storage_path: str) -> bytes:
    client = get_s3_client()
    obj = client.get_object(Bucket=settings.minio_bucket, Key=storage_path)
    return obj["Body"].read()


def content_type_for_path(storage_path: str) -> str:
    ext = storage_path.rsplit(".", 1)[-1].lower()
    mapping = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }
    return mapping.get(ext, "application/octet-stream")
