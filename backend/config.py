"""Central settings + a guard that prevents accidental use of real (paid) AWS."""
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL") or None
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET", "ai-video-generator-local")
JOBS_TABLE = os.getenv("JOBS_TABLE", "VideoJobs")
SCENES_TABLE = os.getenv("SCENES_TABLE", "VideoScenes")
ALLOW_REAL_AWS = os.getenv("ALLOW_REAL_AWS", "false").lower() == "true"


def _check_safe() -> None:
    if AWS_ENDPOINT_URL is None and not ALLOW_REAL_AWS:
        raise RuntimeError(
            "AWS_ENDPOINT_URL is empty, so boto3 would call REAL AWS (may cost money). "
            "Start the local emulator (docker compose up -d) or set ALLOW_REAL_AWS=true on purpose."
        )


def aws_client(service: str):
    """Low-level client, e.g. aws_client('s3'). Same code works for local and real AWS."""
    _check_safe()
    return boto3.client(service, region_name=AWS_REGION, endpoint_url=AWS_ENDPOINT_URL)


def aws_resource(service: str):
    """Higher-level resource API, e.g. aws_resource('dynamodb')."""
    _check_safe()
    return boto3.resource(service, region_name=AWS_REGION, endpoint_url=AWS_ENDPOINT_URL)
