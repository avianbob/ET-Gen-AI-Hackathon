"""
Gemini API Client - Google's Generative AI for evidence synthesis.
Uses langchain-google-genai for integration.
"""

from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from app.repurpose_settings import settings
from app.services.repurpose.utils.logger import get_logger
from app.services.repurpose.utils.gemini_model_util import normalize_gemini_model as _normalize_model

logger = get_logger("llm.gemini")


def normalize_gemini_model(model: str | None) -> str:
    before = (model or "").strip()
    out = _normalize_model(model)
    if before and out != before:
        logger.warning("GEMINI_MODEL %r normalized to %r (deprecated or unsupported id).", before, out)
    return out


class GeminiClient:
    """Client for Google Gemini API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = None
    ):
        """
        Initialize Gemini client.

        Args:
            api_key: Google Gemini API key (uses settings if not provided)
            model: Model name (uses settings if not provided)
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = normalize_gemini_model(model or settings.GEMINI_MODEL)

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError("Gemini API key not configured. Please set GEMINI_API_KEY in .env file.")

        try:
            self.llm = ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=self.api_key,
                temperature=0.3,
                max_output_tokens=8192,  # Increased from 2048 to avoid truncation
                convert_system_message_to_human=True  # Gemini doesn't support system messages
            )
            logger.info(f"Initialized Gemini client with model: {self.model}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    async def generate(self, prompt: str) -> str:
        """
        Generate text using Gemini API.

        Args:
            prompt: Input prompt

        Returns:
            Generated text

        Raises:
            Exception: On API error
        """
        try:
            logger.debug(f"Generating with Gemini, prompt length: {len(prompt)} chars")

            # Use ainvoke for async generation
            response = await self.llm.ainvoke(prompt)

            # Extract content from response
            if hasattr(response, 'content'):
                generated_text = response.content
            else:
                generated_text = str(response)

            logger.info(f"Generated {len(generated_text)} characters with Gemini")
            return generated_text

        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
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

            if hasattr(response, 'content'):
                return response.content
            return str(response)

        except Exception as e:
            logger.error(f"Gemini sync generation failed: {e}")
            raise
