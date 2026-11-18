"""DynamoDB access for the VideoJobs and VideoScenes tables."""
import uuid
from datetime import datetime, timezone

from boto3.dynamodb.conditions import Key

from backend.config import JOBS_TABLE, SCENES_TABLE, aws_resource

_db = None


def db():
    global _db
    if _db is None:
        _db = aws_resource("dynamodb")
    return _db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(idea: str, duration: int, user_id: str = "local-user", **extra) -> dict:
    job = {
        "job_id": f"job_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "idea": idea,
        "total_duration": duration,
        "status": "queued",
        "created_at": _now(),
        "updated_at": _now(),
        **extra,
    }
    db().Table(JOBS_TABLE).put_item(Item=job)
    return job


def get_job(job_id: str) -> dict | None:
    return db().Table(JOBS_TABLE).get_item(Key={"job_id": job_id}).get("Item")


def update_job_status(job_id: str, status: str, **extra) -> None:
    fields = {"status": status, "updated_at": _now(), **extra}
    # "status" is a DynamoDB reserved word, so every field goes through #name placeholders.
    expr = "SET " + ", ".join(f"#{k} = :{k}" for k in fields)
    db().Table(JOBS_TABLE).update_item(
        Key={"job_id": job_id},
        UpdateExpression=expr,
        ExpressionAttributeNames={f"#{k}": k for k in fields},
        ExpressionAttributeValues={f":{k}": v for k, v in fields.items()},
    )


def put_scene(job_id: str, scene_number: int, **fields) -> None:
    db().Table(SCENES_TABLE).put_item(
        Item={"job_id": job_id, "scene_number": scene_number, "updated_at": _now(), **fields}
    )


def list_scenes(job_id: str) -> list[dict]:
    # Query (not Scan): reads only items with this partition key -> fast and cheap.
    resp = db().Table(SCENES_TABLE).query(KeyConditionExpression=Key("job_id").eq(job_id))
    return resp["Items"]
