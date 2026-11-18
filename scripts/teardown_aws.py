"""Delete EVERYTHING this project created (bucket contents, bucket, tables).

Real AWS:  $env:ENV_FILE=".env.aws"; python -m scripts.teardown_aws
Only touches resources named aivg-learning-*.
"""
from botocore.exceptions import ClientError

from backend import config
from backend.config import JOBS_TABLE, SCENES_TABLE, aws_client, aws_resource

print("Target:", config.describe_target())

bucket = config.S3_BUCKET
if config.IS_REAL_AWS and not bucket:
    bucket = f"aivg-learning-{aws_client('sts').get_caller_identity()['Account']}"
assert bucket.startswith("aivg-learning-"), f"Refusing to delete non-project bucket {bucket}"

try:
    b = aws_resource("s3").Bucket(bucket)
    b.objects.all().delete()
    b.delete()
    print("Deleted bucket:", bucket)
except ClientError as e:
    print("Bucket:", e.response["Error"]["Code"])

ddb = aws_client("dynamodb")
for t in (JOBS_TABLE, SCENES_TABLE):
    assert t.startswith("aivg-learning-")
    try:
        ddb.delete_table(TableName=t)
        print("Deleted table:", t)
    except ClientError as e:
        print(t, e.response["Error"]["Code"])
