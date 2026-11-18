"""Pydantic models = the "contract" of our API.

FastAPI uses these to:
  1. validate incoming JSON (bad input -> automatic 422 error)
  2. shape the outgoing JSON
  3. generate the interactive docs at /docs
"""
from typing import Literal

from pydantic import BaseModel, Field


class GenerateVideoRequest(BaseModel):
    idea: str = Field(min_length=10, max_length=500,
                      examples=["How artificial intelligence will change education"])
    duration: int = Field(default=90, ge=60, le=180, description="Seconds (1-3 minutes)")
    style: Literal["cinematic", "cartoon", "minimal", "documentary"] = "cinematic"
    aspect_ratio: Literal["9:16"] = "9:16"
    language: str = "English"


class GenerateVideoResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    job_id: str
    idea: str
    status: str
    total_duration: int
    style: str | None = None
    created_at: str
    updated_at: str
    final_video_url: str | None = None


class SceneStatus(BaseModel):
    scene_number: int
    narration: str | None = None
    image_status: str | None = None
    video_status: str | None = None
