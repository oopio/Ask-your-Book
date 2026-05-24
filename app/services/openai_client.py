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
    """Return the shared OpenAI client (created once, cached forever).

    Reads the API key from (in priority order):
      1. OPENAI_API_KEY environment variable / .env file (local dev)
      2. st.secrets["OPENAI_API_KEY"] (Streamlit Cloud)
    """
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        # Fallback to Streamlit secrets (Streamlit Cloud deployment)
        try:
            import streamlit as st
            api_key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            pass

    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY not found. "
            "Add it to .env (local) or Streamlit Cloud secrets (deployed)."
        )
    return OpenAI(api_key=api_key)
