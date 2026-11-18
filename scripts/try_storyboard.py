"""Lesson 8b: idea -> storyboard JSON (validated) -> optional save to S3 + DynamoDB.

Real Bedrock:  $env:ENV_FILE=".env.aws"; .venv\\Scripts\\python -m scripts.try_storyboard
Save to AWS:   ... -m scripts.try_storyboard --save
"""
import sys
from pathlib import Path

from backend import config
from backend.services.storyboard_service import generate_storyboard

idea = "How AI is changing education"
duration = 60

print(f"Provider: {config.LLM_PROVIDER} | Generating a {duration}s storyboard for: {idea!r}")
story, calls = generate_storyboard(idea, duration)

print(f"\n{story.video_title}  ({story.total_duration}s, {len(story.scenes)} scenes, "
      f"audience: {story.target_audience})")
for s in story.scenes:
    print(f"  {s.scene_id:>2}. [{s.duration}s] {s.caption:<30} | {s.narration}")

tokens_in = sum(c.input_tokens for c in calls)
tokens_out = sum(c.output_tokens for c in calls)
cost = sum(c.estimated_cost_usd for c in calls)
print(f"\nLLM calls: {len(calls)} | tokens {tokens_in} in / {tokens_out} out | est. ${cost:.5f}")

out = Path("output/storyboard.json")
out.parent.mkdir(exist_ok=True)
out.write_text(story.model_dump_json(indent=2), encoding="utf-8")
print(f"Saved {out}")

if "--save" in sys.argv:
    from backend.services import job_repository as jobs
    from backend.services import storage_service as storage

    job = jobs.create_job(idea, duration)
    key = storage.upload_bytes(story.model_dump_json(indent=2).encode(),
                               f"jobs/{job['job_id']}/storyboard.json", "application/json")
    for s in story.scenes:
        jobs.put_scene(job["job_id"], s.scene_id, narration=s.narration, caption=s.caption,
                       duration=s.duration, image_status="pending", video_status="pending")
    jobs.update_job_status(job["job_id"], "storyboard_ready", storyboard_key=key,
                           video_title=story.video_title)
    print(f"Saved to AWS: job {job['job_id']} -> s3://{config.S3_BUCKET}/{key} "
          f"+ {len(story.scenes)} scene items")
