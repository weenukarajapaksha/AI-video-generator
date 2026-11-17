"""Step 1 playground: exercise S3 + DynamoDB end to end on the local emulator.

Run:  python -m scripts.try_aws
"""
from backend.services import job_repository as jobs
from backend.services import storage_service as storage

# 1. DynamoDB: create a job
job = jobs.create_job("How AI is changing education", duration=90)
job_id = job["job_id"]
print("Created job:", job_id)

# 2. DynamoDB: record two scenes
jobs.put_scene(job_id, 1, narration="Imagine a personalized classroom.", image_status="pending")
jobs.put_scene(job_id, 2, narration="AI explains hard concepts.", image_status="pending")

# 3. S3: store a storyboard file under the job's folder
key = storage.upload_bytes(b'{"scenes": 2}', f"jobs/{job_id}/storyboard.json", "application/json")
print("Uploaded:", key)

# 4. Update the job status
jobs.update_job_status(job_id, "storyboard_ready", storyboard_key=key)

# 5. Read everything back
print("Job now:", jobs.get_job(job_id))
print("Scenes:", [(int(s["scene_number"]), s["narration"]) for s in jobs.list_scenes(job_id)])
print("S3 keys:", storage.list_keys(f"jobs/{job_id}/"))
print("Download link:", storage.presigned_url(key))
