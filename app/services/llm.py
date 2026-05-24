"""
LLM service — chat completion wrapper used by RAG answer generation
and metadata categorisation.
"""

from typing import List, Dict, Optional
from app.config import CHAT_MODEL
from app.services.openai_client import get_client


def chat_complete(
    messages: List[Dict[str, str]],
    model: str = CHAT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 800,
) -> str:
    """
    Call the chat completions API and return the assistant message content.
    Raises on failure — callers are responsible for catching and handling errors.
    """
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception:
        raise  # let callers handle / log as appropriate
