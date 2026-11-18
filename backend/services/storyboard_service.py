"""Idea -> validated Storyboard, using whichever LLM provider is configured."""
import json
import re

from pydantic import ValidationError

from backend.models.storyboard import Storyboard
from backend.providers.llm_provider import LLMProvider, LLMResult, get_llm

SYSTEM_PROMPT = """You are a storyboard writer for short vertical social-media videos (Reels, Shorts, TikTok).
Return ONLY one JSON object, no other text, with exactly this shape:
{
  "video_title": str,
  "target_audience": str,
  "aspect_ratio": "9:16",
  "total_duration": int,
  "scenes": [
    {"scene_id": int, "duration": int, "scene_description": str, "narration": str,
     "image_prompt": str, "video_prompt": str, "caption": str}
  ]
}
Rules:
- scene_id starts at 1 and increases by 1.
- Each scene duration is between 5 and 9 seconds.
- The sum of all scene durations must equal total_duration.
- Scene 1 is a strong hook. The last scene is a conclusion with a call to action.
- Narration is spoken English, about 2.5 words per second of scene duration.
- image_prompt describes one vertical 9:16 frame: subject, setting, lighting, style.
- video_prompt describes camera movement or motion for that frame.
- caption is at most 6 words."""

MAX_ATTEMPTS = 2  # each attempt is a paid LLM call on Bedrock, so keep this small


def _extract_json(text: str) -> dict:
    """LLMs often wrap JSON in ```json fences or add a sentence. Take the outermost {...}."""
    text = re.sub(r"```(?:json)?", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in the model output")
    return json.loads(text[start:end + 1])


def generate_storyboard(idea: str, duration: int = 60, style: str = "cinematic",
                        llm: LLMProvider | None = None) -> tuple[Storyboard, list[LLMResult]]:
    llm = llm or get_llm()
    prompt = (f"Video idea: {idea}\nTotal duration: {duration} seconds\nVisual style: {style}\n"
              f"Create the storyboard.")
    calls: list[LLMResult] = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = llm.generate(SYSTEM_PROMPT, prompt, max_tokens=4000, temperature=0.7)
        calls.append(result)
        try:
            return Storyboard.model_validate(_extract_json(result.text)), calls
        except (ValueError, ValidationError) as err:
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(f"Storyboard invalid after {attempt} attempts: {err}") from err
            # Self-correction: show the model its own output and the exact error.
            prompt = (f"{prompt}\n\nYour previous answer was invalid.\nError: {err}\n"
                      f"Previous answer:\n{result.text}\n\nReturn the corrected JSON only.")
    raise AssertionError("unreachable")
