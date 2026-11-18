"""FastAPI app entry point.

Local (moto):  .venv\\Scripts\\uvicorn backend.main:app --reload
Real AWS:      $env:ENV_FILE=".env.aws"; .venv\\Scripts\\uvicorn backend.main:app --reload
Then open http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI

from backend import config
from backend.api.video_routes import router as video_router

app = FastAPI(title="AI Video Generator", version="0.1.0")
app.include_router(video_router)


@app.get("/health", tags=["system"])
def health():
    """Shows which AWS this server is talking to - handy to avoid surprises."""
    return {"status": "ok", "aws_target": config.describe_target()}
