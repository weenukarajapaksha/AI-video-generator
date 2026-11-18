"""LLM providers behind one interface.

The rest of the app only calls `get_llm().generate(...)`. It never knows whether the
answer came from Amazon Bedrock or from the offline FakeLLM, so providers can be
swapped (Bedrock, an external API, Ollama, ...) without touching the workflow code.
"""
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend import config


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int
    model_id: str

    @property
    def estimated_cost_usd(self) -> float:
        """Rough estimate from the per-million-token prices in the settings file."""
        return (self.input_tokens * config.PRICE_INPUT_PER_M
                + self.output_tokens * config.PRICE_OUTPUT_PER_M) / 1_000_000


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system: str, prompt: str, max_tokens: int = 1000,
                 temperature: float = 0.7) -> LLMResult: ...


class BedrockLLM(LLMProvider):
    """Amazon Bedrock via the Converse API: one request format for every Bedrock model."""

    def __init__(self, model_id: str | None = None):
        self.model_id = model_id or config.BEDROCK_MODEL_ID
        # bedrock-runtime = the API that RUNS models. ("bedrock" is the management API.)
        # The local emulator cannot run models, so this always goes to real AWS.
        self.client = config.aws_client("bedrock-runtime", local_ok=False)

    def generate(self, system, prompt, max_tokens=1000, temperature=0.7) -> LLMResult:
        max_tokens = min(max_tokens, config.MAX_OUTPUT_TOKENS)  # cost guard
        resp = self.client.converse(
            modelId=self.model_id,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
        )
        return LLMResult(
            text=resp["output"]["message"]["content"][0]["text"],
            input_tokens=resp["usage"]["inputTokens"],
            output_tokens=resp["usage"]["outputTokens"],
            model_id=self.model_id,
        )


class FakeLLM(LLMProvider):
    """Offline stand-in: free, instant, deterministic. Used for local mode and tests."""

    def generate(self, system, prompt, max_tokens=1000, temperature=0.7) -> LLMResult:
        if "storyboard" not in system.lower():
            return LLMResult("Hello! I am the FakeLLM. Set LLM_PROVIDER=bedrock for a real model.",
                             len(prompt) // 4, 20, "fake")
        m = re.search(r"Total duration:\s*(\d+)", prompt)
        total = int(m.group(1)) if m else 60
        n = max(5, total // 8)
        base, extra = divmod(total, n)
        durations = [base + (1 if i < extra else 0) for i in range(n)]
        scenes = [{
            "scene_id": i + 1,
            "duration": d,
            "scene_description": f"Placeholder scene {i + 1}",
            "narration": f"This is narration line {i + 1}.",
            "image_prompt": f"Vertical 9:16 illustration for scene {i + 1}",
            "video_prompt": "Slow zoom in",
            "caption": f"Point {i + 1}",
        } for i, d in enumerate(durations)]
        story = {"video_title": "Fake storyboard", "target_audience": "Testers",
                 "aspect_ratio": "9:16", "total_duration": total, "scenes": scenes}
        return LLMResult("```json\n" + json.dumps(story, indent=2) + "\n```", len(prompt) // 4, 600, "fake")


def get_llm() -> LLMProvider:
    if config.LLM_PROVIDER == "bedrock":
        return BedrockLLM()
    return FakeLLM()
