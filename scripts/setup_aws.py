"""Create the S3 bucket and DynamoDB tables (local emulator OR real AWS).

Local:     python -m scripts.setup_aws
Real AWS:  $env:ENV_FILE=".env.aws"; python -m scripts.setup_aws

COST on real AWS:
  - DynamoDB: ON-DEMAND (PAY_PER_REQUEST). An idle table costs $0; you pay only per
    read/write (~$0.625 per MILLION writes), so learning usage is fractions of a cent
    even when the company account has no free tier.
  - S3: an empty bucket is free; you pay per GB stored + per request (fractions of a cent here).
"""
from botocore.exceptions import ClientError

from backend import config
from backend.config import JOBS_TABLE, SCENES_TABLE, aws_client

print("Target:", config.describe_target())

s3 = aws_client("s3")
ddb = aws_client("dynamodb")

bucket = config.S3_BUCKET
if config.IS_REAL_AWS and not bucket:
    account = aws_client("sts").get_caller_identity()["Account"]
    bucket = f"aivg-learning-{account}"
    print(f"No S3_BUCKET set -> using '{bucket}'. Put S3_BUCKET={bucket} in .env.aws")

# ---- S3 ----
try:
    s3.head_bucket(Bucket=bucket)
    print(f"Bucket exists: {bucket}")
except ClientError:
    kwargs = {"Bucket": bucket}
    if config.AWS_REGION != "us-east-1":  # us-east-1 is the one region that must NOT pass this
        kwargs["CreateBucketConfiguration"] = {"LocationConstraint": config.AWS_REGION}
    s3.create_bucket(**kwargs)
    # Make sure nothing in this bucket can ever be made public.
    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )
    # Auto-delete anything older than 7 days, so forgotten test files don't keep costing.
    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket,
        LifecycleConfiguration={
            "Rules": [{"ID": "expire-7d", "Status": "Enabled", "Filter": {"Prefix": ""},
                       "Expiration": {"Days": 7}}]
        },
    )
    s3.put_bucket_tagging(Bucket=bucket, Tagging={"TagSet": config.RESOURCE_TAGS})
    print(f"Created bucket: {bucket} (private, 7-day auto-delete, tagged)")

# ---- DynamoDB ----

existing = ddb.list_tables()["TableNames"]

# VideoJobs: one item per job. Partition key = job_id.
if JOBS_TABLE not in existing:
    ddb.create_table(
        TableName=JOBS_TABLE,
        KeySchema=[{"AttributeName": "job_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "job_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
        Tags=config.RESOURCE_TAGS,
    )
    print(f"Creating table: {JOBS_TABLE}")

# VideoScenes: many items per job. Partition key = job_id, sort key = scene_number,
# so "give me all scenes of job X, in order" is a single Query.
if SCENES_TABLE not in existing:
    ddb.create_table(
        TableName=SCENES_TABLE,
        KeySchema=[
            {"AttributeName": "job_id", "KeyType": "HASH"},
            {"AttributeName": "scene_number", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "job_id", "AttributeType": "S"},
            {"AttributeName": "scene_number", "AttributeType": "N"},
        ],
        BillingMode="PAY_PER_REQUEST",
        Tags=config.RESOURCE_TAGS,
    )
    print(f"Creating table: {SCENES_TABLE}")

# On real AWS, tables take a few seconds to become ACTIVE.
waiter = ddb.get_waiter("table_exists")
for t in (JOBS_TABLE, SCENES_TABLE):
    waiter.wait(TableName=t)
print("Tables ready:", [t for t in ddb.list_tables()["TableNames"] if t.startswith("aivg-learning")])
