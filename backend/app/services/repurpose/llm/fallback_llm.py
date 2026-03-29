"""
Chain Gemini → Groq → Ollama when Gemini errors or quota is exhausted.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from app.services.repurpose.utils.logger import get_logger

if TYPE_CHECKING:
    from app.services.repurpose.llm.gemini_client import GeminiClient
    from app.services.repurpose.llm.groq_client import GroqClient
    from app.services.repurpose.llm.ollama_client import OllamaClient

logger = get_logger("llm.fallback")


class FallbackLLMClient:
    """Tries Gemini, then Groq, then Ollama on failure."""

    def __init__(
        self,
        gemini: Optional["GeminiClient"],
        groq: Optional["GroqClient"],
        ollama: Optional["OllamaClient"],
    ):
        self._gemini = gemini
        self._groq = groq
        self._ollama = ollama

        if gemini:
            self.model = getattr(gemini, "model", "gemini")
            self.primary_provider = "gemini"
        elif groq:
            self.model = getattr(groq, "model", "groq")
            self.primary_provider = "groq"
        elif ollama:
            self.model = getattr(ollama, "model", "ollama")
            self.primary_provider = "ollama"
        else:
            self.model = "none"
            self.primary_provider = "none"

    async def generate(self, prompt: str) -> str:
        last_error: Optional[BaseException] = None

        if self._gemini:
            try:
                return await self._gemini.generate(prompt)
            except Exception as e:
                last_error = e
                logger.warning("Gemini failed (%s); trying Groq/Ollama if configured.", e)

        if self._groq:
            try:
                text = await self._groq.generate(prompt)
                logger.info("Response generated via Groq (fallback).")
                return text
            except Exception as e:
                last_error = e
                logger.warning("Groq failed (%s); trying Ollama if configured.", e)

        if self._ollama:
            try:
                return await self._ollama.generate(prompt)
            except Exception as e:
                last_error = e

        if last_error is not None:
            raise last_error
        raise RuntimeError("No LLM providers configured.")

    def generate_sync(self, prompt: str) -> str:
        last_error: Optional[BaseException] = None

        if self._gemini:
            try:
                return self._gemini.generate_sync(prompt)
            except Exception as e:
                last_error = e
                logger.warning("Gemini sync failed (%s); trying fallbacks.", e)

        if self._groq:
            try:
                text = self._groq.generate_sync(prompt)
                logger.info("Response generated via Groq (sync fallback).")
                return text
            except Exception as e:
                last_error = e
                logger.warning("Groq sync failed (%s); trying Ollama.", e)

        if self._ollama:
            try:
                return self._ollama.generate_sync(prompt)
            except Exception as e:
                last_error = e

        if last_error is not None:
            raise last_error
        raise RuntimeError("No LLM providers configured.")
