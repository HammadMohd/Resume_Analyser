"""LLM Refinement Layer — uses LLMs for language improvement only.

This module provides bullet rewriting and language refinement
using structured LLM outputs validated with Pydantic.

Key principle: LLM is the editor, not the decision maker.
"""

from backend.config.settings import settings

# Check if LLM API key is configured (Gemini or OpenAI)
GEMINI_API_KEY = settings.gemini_api_key
OPENAI_API_KEY = settings.openai_api_key
LLM_AVAILABLE = bool(GEMINI_API_KEY or OPENAI_API_KEY)
