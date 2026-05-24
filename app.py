"""
Ask Your Book — Document Intelligence Platform
AI-powered document Q&A with PDF viewer, smart categorization, and filtering.

Run:
    streamlit run app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# ── Page config MUST be the very first Streamlit call ─────────────────────
st.set_page_config(
    page_title="ASK YOUR BOOK — Document Intelligence Platform",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Ensure data directories exist ─────────────────────────────────────────
from app.config import BOOKS_DIR, PDFS_DIR, EMBEDS_DIR
BOOKS_DIR.mkdir(parents=True, exist_ok=True)
PDFS_DIR.mkdir(parents=True, exist_ok=True)
EMBEDS_DIR.mkdir(parents=True, exist_ok=True)

# ── Session state ─────────────────────────────────────────────────────────
from app.ui.state import init as init_state
init_state()

# ── CSS ───────────────────────────────────────────────────────────────────
from app.ui.styles import inject as inject_styles
inject_styles()

# ── UI components ─────────────────────────────────────────────────────────
from app.ui import header, sidebar, pdf_viewer, chat

# Header
header.render()

# Sidebar
with st.sidebar:
    sidebar.render()

# ── View-mode toggle ──────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;margin-bottom:2rem;">
  <div style="background:white;padding:0.5rem;border-radius:15px;
       box-shadow:0 4px 20px rgba(0,0,0,0.1);display:inline-block;">
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    if st.button(
        "📄 Document Viewer",
        type="primary" if st.session_state.view_mode == "pdf" else "secondary",
        use_container_width=True, key="btn_pdf_mode",
    ):
        st.session_state.view_mode = "pdf"
        st.rerun()
with c2:
    if st.button(
        "🤖 AI Assistant",
        type="primary" if st.session_state.view_mode == "chat" else "secondary",
        use_container_width=True, key="btn_chat_mode",
    ):
        st.session_state.view_mode = "chat"
        st.rerun()
with c3:
    if st.button(
        "⚡ Dual View",
        type="primary" if st.session_state.view_mode == "split" else "secondary",
        use_container_width=True, key="btn_split_mode",
    ):
        st.session_state.view_mode = "split"
        st.rerun()

st.markdown("</div></div>", unsafe_allow_html=True)

# ── Dynamic layout ────────────────────────────────────────────────────────
mode = st.session_state.view_mode

if mode == "split":
    col_pdf, col_chat = st.columns([1, 1])
elif mode == "pdf":
    col_pdf  = st.container()
    col_chat = None
else:  # chat
    col_pdf  = None
    col_chat = st.container()

# PDF viewer
if col_pdf is not None:
    if mode == "pdf":
        st.markdown('<div class="single-view-container">', unsafe_allow_html=True)
    with col_pdf:
        pdf_viewer.render(mode)
    if mode == "pdf":
        st.markdown("</div>", unsafe_allow_html=True)

# Chat panel
if col_chat is not None:
    if mode == "chat":
        st.markdown('<div class="single-view-container">', unsafe_allow_html=True)
    with col_chat:
        chat.render()
    if mode == "chat":
        st.markdown("</div>", unsafe_allow_html=True)
