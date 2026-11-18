"""Lesson 8a: your first Bedrock call from Python.

Real Bedrock:  $env:ENV_FILE=".env.aws"; .venv\\Scripts\\python -m scripts.try_bedrock
Offline fake:  .venv\\Scripts\\python -m scripts.try_bedrock
"""
import sys
import time

from backend import config
from backend.providers.llm_provider import get_llm

question = " ".join(sys.argv[1:]) or "In two sentences, what is Amazon Bedrock?"
llm = get_llm()
print(f"Provider: {config.LLM_PROVIDER} | Model: {getattr(llm, 'model_id', 'fake')}")

start = time.perf_counter()
result = llm.generate("You are a helpful, concise assistant.", question, max_tokens=200)
elapsed = time.perf_counter() - start

print("\n" + result.text + "\n")
print(f"Tokens: {result.input_tokens} in / {result.output_tokens} out | {elapsed:.1f}s")
print(f"Estimated cost: ${result.estimated_cost_usd:.6f}")
