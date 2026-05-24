"""
Answer generation — builds a RAG prompt from retrieved passages and calls the LLM.
"""

from typing import List, Dict
from app.services.llm import chat_complete
from app.config import CHAT_MODEL


_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions about documents "
    "based on provided passages. Be accurate, concise, and cite the passage "
    "number when referencing specific information."
)


def generate_answer(query: str, context_chunks: List[Dict]) -> str:
    """
    Build a RAG prompt from *context_chunks* and return the LLM answer.

    *context_chunks* must have at least a 'text' key (as returned by retriever.search).
    Returns an error string (not raises) so the UI can display it gracefully.
    """
    if not context_chunks:
        return "I couldn't find relevant passages to answer that question."

    passages = "\n\n".join(
        f"[Passage {i+1}] {c['text'][:500]}{'...' if len(c['text']) > 500 else ''}"
        for i, c in enumerate(context_chunks)
    )

    user_prompt = (
        f"Answer the question using ONLY the passages below. "
        f"If the passages don't contain enough information, say so.\n\n"
        f"Passages:\n{passages}\n\n"
        f"Question: {query}\n\nAnswer:"
    )

    try:
        answer = chat_complete(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            model=CHAT_MODEL,
            temperature=0.7,
            max_tokens=800,
        )
        return answer or "No answer returned."
    except Exception as exc:
        return f"Error generating answer: {type(exc).__name__}: {exc}"
