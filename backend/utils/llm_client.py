from __future__ import annotations

import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()


class LLMClientError(RuntimeError):
    pass




def _build_client() -> OpenAI:
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMClientError(
            "No API key found. Set OPENAI_API_KEY or LLM_API_KEY."
        )

    base_url = os.getenv("LLM_ENDPOINT")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)

    return OpenAI(api_key=api_key)


def call_llm(prompt: str, model: str | None = None) -> str:
    configured_model = model or os.getenv("LLM_MODEL")
    if not configured_model:
        raise LLMClientError(
            "LLM_MODEL is not configured. Set LLM_MODEL to something like "
            "'gpt-5-mini' or 'gpt-5.4'."
        )

    if not prompt or not prompt.strip():
        raise LLMClientError("Prompt is empty.")

    client = _build_client()

    try:
        response = client.responses.create(
            model=configured_model,
            input=prompt,
        )
    except Exception as exc:
        raise LLMClientError(f"OpenAI API call failed: {exc}") from exc

    text = getattr(response, "output_text", None)
    if text:
        return text.strip()

    try:
        chunks: list[str] = []
        for item in getattr(response, "output", []):
            for content in getattr(item, "content", []):
                if getattr(content, "type", None) == "output_text":
                    chunks.append(getattr(content, "text", ""))
        final_text = "".join(chunks).strip()
        if final_text:
            return final_text
    except Exception:
        pass

    raise LLMClientError("Model returned no text output.")