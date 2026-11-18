"""Central settings + guards that prevent accidental use of real (paid) AWS.

Which settings file is loaded is chosen by the ENV_FILE environment variable:
    (unset)            -> .env      local emulator (moto), $0
    ENV_FILE=.env.aws  -> .env.aws  real company AWS account
"""
import os

import boto3
from dotenv import load_dotenv

ENV_FILE = os.getenv("ENV_FILE", ".env")
load_dotenv(ENV_FILE)

AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL") or None
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_PROFILE = os.getenv("AWS_PROFILE") or None
S3_BUCKET = os.getenv("S3_BUCKET", "aivg-learning-local")
JOBS_TABLE = os.getenv("JOBS_TABLE", "aivg-learning-VideoJobs")
SCENES_TABLE = os.getenv("SCENES_TABLE", "aivg-learning-VideoScenes")
ALLOW_REAL_AWS = os.getenv("ALLOW_REAL_AWS", "false").lower() == "true"

IS_REAL_AWS = AWS_ENDPOINT_URL is None

# ---- LLM settings ----
# "fake" = offline FakeLLM ($0).  "bedrock" = Amazon Bedrock (PAID per token).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "fake").lower()
# "eu." prefix = EU cross-region inference profile (needed from Stockholm, eu-north-1).
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-micro-v1:0")
# Approximate USD per 1M tokens, only used to PRINT cost estimates. Check the Bedrock pricing page.
PRICE_INPUT_PER_M = float(os.getenv("PRICE_INPUT_PER_M", "0.05"))
PRICE_OUTPUT_PER_M = float(os.getenv("PRICE_OUTPUT_PER_M", "0.18"))
# Hard cap on output tokens per call - the main lever on LLM cost.
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "4000"))

# Every resource we create gets these tags, so it is easy to find and delete later.
RESOURCE_TAGS = [
    {"Key": "project", "Value": "aivg-learning"},
    {"Key": "purpose", "Value": "internship-practice"},
]

_session = None


def _check_safe() -> None:
    if IS_REAL_AWS and not ALLOW_REAL_AWS:
        raise RuntimeError(
            "AWS_ENDPOINT_URL is empty, so boto3 would call REAL AWS (may cost money). "
            "Use the local emulator, or set ALLOW_REAL_AWS=true in .env.aws on purpose."
        )


def session() -> boto3.Session:
    global _session
    if _session is None:
        _check_safe()
        _session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    return _session


def aws_client(service: str, local_ok: bool = True):
    """Low-level client, e.g. aws_client('s3'). Same code works for local and real AWS.

    local_ok=False is for services the local emulator can't fake (e.g. running Bedrock models).
    """
    if not local_ok and not IS_REAL_AWS:
        raise RuntimeError(f"'{service}' needs real AWS. Use ENV_FILE=.env.aws, "
                           f"or LLM_PROVIDER=fake for offline mode.")
    return session().client(service, endpoint_url=AWS_ENDPOINT_URL)


def aws_resource(service: str):
    """Higher-level resource API, e.g. aws_resource('dynamodb')."""
    return session().resource(service, endpoint_url=AWS_ENDPOINT_URL)


def describe_target() -> str:
    if not IS_REAL_AWS:
        return f"LOCAL emulator at {AWS_ENDPOINT_URL}"
    ident = aws_client("sts").get_caller_identity()
    return f"REAL AWS account {ident['Account']} as {ident['Arn']} in {AWS_REGION}"
