"""
Groq API client — fast cloud LLM fallback when Gemini fails (quota, deprecated model, etc.).
"""

from __future__ import annotations

import asyncio
from typing import Optional

from app.repurpose_settings import settings
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("llm.groq")

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore


class GroqClient:
    """Client for Groq chat completions (OpenAI-compatible)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        if Groq is None:
            raise ImportError("groq package not installed. pip install groq")
        self.api_key = (api_key or settings.GROQ_API_KEY or "").strip()
        self.model = model or settings.GROQ_MODEL
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not configured.")
        self._client = Groq(api_key=self.api_key)
        logger.info("Initialized Groq client with model: %s", self.model)

    def generate_sync(self, prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=8192,
            )
            choice = response.choices[0] if response.choices else None
            content = choice.message.content if choice and choice.message else None
            if not content:
                raise ValueError("Groq returned empty content")
            logger.info("Generated %s characters with Groq", len(content))
            return content
        except Exception as e:
            logger.error("Groq generation failed: %s", e)
            raise

    async def generate(self, prompt: str) -> str:
        return await asyncio.to_thread(self.generate_sync, prompt)
