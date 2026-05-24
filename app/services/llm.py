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
) -> Optional[str]:
    """
    Call the chat completions API and return the assistant message content.
    Returns None on failure (caller decides how to handle).
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
    except Exception as exc:
        raise  # let callers handle / log as appropriate
