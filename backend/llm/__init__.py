"""LLM Refinement Layer — uses LLMs for language improvement only.

This module provides bullet rewriting and language refinement
using structured LLM outputs validated with Pydantic.

Key principle: LLM is the editor, not the decision maker.
"""

import os

# Check if OpenAI API key is configured
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
LLM_AVAILABLE = bool(OPENAI_API_KEY)
