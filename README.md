# AI Video Generator (learning project)

Idea → storyboard → images → clips → narration → FFmpeg edit → 9:16 MP4.
Built step by step to learn AWS + LangGraph. **Runs 100% locally at $0.**

## Cost rule
All AWS calls go to a local emulator (moto). `backend/config.py` refuses to call
real AWS unless `ALLOW_REAL_AWS=true`. Paid services (Bedrock, Luma Ray, AgentCore)
are replaced by free local alternatives.

## Run (Step 1)
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt "moto[server]"
copy .env.example .env

# terminal 1 - local fake AWS
.venv\Scripts\moto_server -p 5000

# terminal 2
.venv\Scripts\python -m scripts.setup_local_aws
.venv\Scripts\python -m scripts.try_aws
```
Browse the emulator's state at http://localhost:5000/moto-api/

Note: moto keeps data in memory, so restarting it wipes everything. Re-run `setup_local_aws`.

## Roadmap
1. [x] Local S3 + DynamoDB
2. [ ] FastAPI job API
3. [ ] Storyboard with a local LLM + Pydantic
4. [ ] LangGraph workflow
5. [ ] Images, clips (FFmpeg pan/zoom), TTS, captions
6. [ ] FFmpeg final edit → S3
7. [ ] SQS + worker
8. [ ] Step Functions (local)
9. [ ] Optional: real AWS with budget alerts
