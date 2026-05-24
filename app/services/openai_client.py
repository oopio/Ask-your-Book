"""
Shared OpenAI client singleton.

All modules import `get_client()` from here — no more three separate
client instantiations scattered across ingestion / query / metadata.
"""

import os
from functools import lru_cache
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    """Return the shared OpenAI client (created once, cached forever)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY not found. "
            "Create a .env file with OPENAI_API_KEY=sk-... in the project root."
        )
    return OpenAI(api_key=api_key)
