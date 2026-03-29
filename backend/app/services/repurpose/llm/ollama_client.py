"""
Ollama Client - Local LLM server integration for fallback.
Uses langchain-community for Ollama support.
"""

from typing import Optional
from langchain_community.llms import Ollama
from app.repurpose_settings import settings
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("llm.ollama")


class OllamaClient:
    """Client for local Ollama LLM server."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server URL (uses settings if not provided)
            model: Model name (uses settings if not provided)
        """
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL

        try:
            self.llm = Ollama(
                base_url=self.base_url,
                model=self.model,
                temperature=0.3
            )
            logger.info(f"Initialized Ollama client with model: {self.model} at {self.base_url}")

        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise

    async def generate(self, prompt: str) -> str:
        """
        Generate text using Ollama.

        Args:
            prompt: Input prompt

        Returns:
            Generated text

        Raises:
            Exception: On generation error
        """
        try:
            logger.debug(f"Generating with Ollama, prompt length: {len(prompt)} chars")

            # Use ainvoke for async generation
            response = await self.llm.ainvoke(prompt)

            # Ollama returns string directly
            if isinstance(response, str):
                generated_text = response
            else:
                generated_text = str(response)

            logger.info(f"Generated {len(generated_text)} characters with Ollama")
            return generated_text

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    def generate_sync(self, prompt: str) -> str:
        """
        Generate text synchronously (for testing/debugging).

        Args:
            prompt: Input prompt

        Returns:
            Generated text
        """
        try:
            response = self.llm.invoke(prompt)

            if isinstance(response, str):
                return response
            return str(response)

        except Exception as e:
            logger.error(f"Ollama sync generation failed: {e}")
            raise

    def check_availability(self) -> bool:
        """
        Check if Ollama server is available.

        Returns:
            True if server is reachable, False otherwise
        """
        try:
            # Try a simple generation to check availability
            response = self.llm.invoke("Hello")
            return bool(response)
        except Exception as e:
            logger.warning(f"Ollama server not available: {e}")
            return False
