"""HTTP endpoints for video jobs. Each route is thin: validate -> call a service -> return."""
from fastapi import APIRouter, HTTPException

from backend.models.video import GenerateVideoRequest, GenerateVideoResponse, JobStatus, SceneStatus
from backend.services import job_repository as jobs

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/generate", response_model=GenerateVideoResponse, status_code=202)
def generate_video(req: GenerateVideoRequest):
    """Create a job in DynamoDB and return immediately (202 = accepted, work happens later).

    Later lessons: a background worker (SQS) picks the job up and runs the LangGraph pipeline.
    """
    job = jobs.create_job(req.idea, req.duration, style=req.style, language=req.language)
    return GenerateVideoResponse(job_id=job["job_id"], status=job["status"],
                                 message="Video generation queued")


@router.get("/{job_id}", response_model=JobStatus)
def get_video_job(job_id: str):
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.get("/{job_id}/scenes", response_model=list[SceneStatus])
def get_video_scenes(job_id: str):
    if jobs.get_job(job_id) is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return jobs.list_scenes(job_id)
