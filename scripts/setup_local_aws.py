"""Create the S3 bucket and DynamoDB tables in the LOCAL emulator.

Run:  python -m scripts.setup_local_aws
"""
from backend.config import JOBS_TABLE, S3_BUCKET, SCENES_TABLE, aws_client

s3 = aws_client("s3")
ddb = aws_client("dynamodb")

existing_buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
if S3_BUCKET not in existing_buckets:
    s3.create_bucket(Bucket=S3_BUCKET)
    print(f"Created bucket: {S3_BUCKET}")
else:
    print(f"Bucket exists: {S3_BUCKET}")

existing_tables = ddb.list_tables()["TableNames"]

# VideoJobs: one item per job. Partition key = job_id.
if JOBS_TABLE not in existing_tables:
    ddb.create_table(
        TableName=JOBS_TABLE,
        KeySchema=[{"AttributeName": "job_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "job_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    print(f"Created table: {JOBS_TABLE}")

# VideoScenes: many items per job. Partition key = job_id, sort key = scene_number,
# so "give me all scenes of job X, in order" is a single Query.
if SCENES_TABLE not in existing_tables:
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
    )
    print(f"Created table: {SCENES_TABLE}")

print("Tables now:", ddb.list_tables()["TableNames"])
