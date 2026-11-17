"""S3 storage: images, clips, audio and final videos live here."""
from pathlib import Path

from backend.config import S3_BUCKET, aws_client

_s3 = None


def s3():
    global _s3
    if _s3 is None:
        _s3 = aws_client("s3")
    return _s3


def upload_file(local_path: str | Path, key: str) -> str:
    s3().upload_file(str(local_path), S3_BUCKET, key)
    return key


def upload_bytes(data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    s3().put_object(Bucket=S3_BUCKET, Key=key, Body=data, ContentType=content_type)
    return key


def download_bytes(key: str) -> bytes:
    return s3().get_object(Bucket=S3_BUCKET, Key=key)["Body"].read()


def list_keys(prefix: str = "") -> list[str]:
    resp = s3().list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
    return [obj["Key"] for obj in resp.get("Contents", [])]


def presigned_url(key: str, expires_seconds: int = 3600) -> str:
    """Temporary download link - this is how users will download the final video."""
    return s3().generate_presigned_url(
        "get_object", Params={"Bucket": S3_BUCKET, "Key": key}, ExpiresIn=expires_seconds
    )
