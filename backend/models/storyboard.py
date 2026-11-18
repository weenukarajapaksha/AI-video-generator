"""The storyboard: the most important data structure in the project.

The LLM must return JSON that fits these models. If it doesn't, Pydantic tells us
exactly what is wrong, and we can send that error back to the LLM to fix.
"""
from pydantic import BaseModel, Field, model_validator


class Scene(BaseModel):
    scene_id: int = Field(ge=1)
    duration: int = Field(ge=3, le=10, description="Seconds; video models make 5-10 s clips")
    scene_description: str
    narration: str = Field(min_length=3)
    image_prompt: str
    video_prompt: str
    caption: str = Field(max_length=60)


class Storyboard(BaseModel):
    video_title: str
    target_audience: str
    aspect_ratio: str = "9:16"
    total_duration: int = Field(ge=30, le=200)
    scenes: list[Scene] = Field(min_length=5, max_length=30)

    @model_validator(mode="after")
    def check_timing(self):
        ids = [s.scene_id for s in self.scenes]
        if ids != list(range(1, len(ids) + 1)):
            raise ValueError(f"scene_id values must be 1..{len(ids)} in order, got {ids}")
        total = sum(s.duration for s in self.scenes)
        if abs(total - self.total_duration) > self.total_duration * 0.15:
            raise ValueError(
                f"scene durations add up to {total}s but total_duration is "
                f"{self.total_duration}s (must be within 15%)"
            )
        return self
