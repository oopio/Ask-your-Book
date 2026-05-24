"""
Streamlit session-state management.

Single source of truth for every session key.
All other modules read/write state through the helpers here.
"""

import streamlit as st
from app.config import DEFAULT_VIEW_MODE, DEFAULT_DARK_MODE, TOP_K_DEFAULT


# ── initialise (call once at app startup) ──────────────────────────────────

def init():
    """Initialise all session-state keys with their defaults if not yet set."""
    defaults = {
        # active document
        "database":         None,
        "book_stats":       None,
        "current_book":     None,
        "current_pdf_path": None,
        "active_book_key":  "",   # forces PDF viewer re-mount on switch
        # library
        "available_books":  [],
        "initialized":      False,
        # chat
        "chat_history":     [],
        # view
        "view_mode":        DEFAULT_VIEW_MODE,
        "dark_mode":        DEFAULT_DARK_MODE,
        # settings
        "num_passages":     TOP_K_DEFAULT,
        "show_sources":     True,
        # filters
        "filter_search":    "",
        "filter_categories": [],
        "filter_tags":      [],
        "filter_date_range": [],
        "filter_page_range": (0, 2000),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ── document switching ─────────────────────────────────────────────────────

def activate_book(database, stats, pdf_path: str, book_name: str):
    """
    Atomically replace the active document.

    Clears all previous book state first so there is never a moment where
    old and new data are mixed in the same render cycle.
    """
    # tear down
    st.session_state.database         = None
    st.session_state.book_stats       = None
    st.session_state.current_book     = None
    st.session_state.current_pdf_path = None
    st.session_state.chat_history     = []
    st.session_state.active_book_key  = ""
    # set new
    st.session_state.database         = database
    st.session_state.book_stats       = stats
    st.session_state.current_book     = book_name
    st.session_state.current_pdf_path = pdf_path
    st.session_state.active_book_key  = book_name   # unique → viewer re-mounts


def clear_filters():
    st.session_state.filter_search     = ""
    st.session_state.filter_categories = []
    st.session_state.filter_tags       = []
    st.session_state.filter_page_range = (0, 2000)


# ── convenience accessors ──────────────────────────────────────────────────

def has_document() -> bool:
    return st.session_state.database is not None

def has_embeddings() -> bool:
    return bool(st.session_state.database)

def current_filters() -> dict:
    return {
        "search":     st.session_state.filter_search,
        "categories": st.session_state.filter_categories,
        "tags":       st.session_state.filter_tags,
        "page_min":   st.session_state.filter_page_range[0],
        "page_max":   st.session_state.filter_page_range[1],
    }
