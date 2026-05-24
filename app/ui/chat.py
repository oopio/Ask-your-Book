"""
AI Assistant chat panel.
Calls the RAG retriever and answerer; updates chat_history in session state.
"""

import streamlit as st
from app.rag import retriever, answerer
from app.utils.text_utils import estimate_page


def render():
    """Render the chat panel inside the current column/container."""
    _panel_header()

    db = st.session_state.database

    if db is None:
        st.info("📂 Load a document from the sidebar to start chatting.")
        return

    if len(db) == 0:
        st.info("📄 Document loaded. Chat will be available once the API is active.")
        return

    # ── chat history ──────────────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if (
                msg["role"] == "assistant"
                and msg.get("sources")
                and st.session_state.show_sources
            ):
                with st.expander("📚 View Sources"):
                    _render_sources(msg["sources"])

    # ── new question ──────────────────────────────────────────────────────
    if question := st.chat_input("Ask a question..."):
        st.session_state.chat_history.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                chunks = retriever.search(
                    question, db, top_k=st.session_state.num_passages
                )
                answer = answerer.generate_answer(question, chunks)
                st.markdown(answer)

                if st.session_state.show_sources and chunks:
                    with st.expander("📚 View Sources"):
                        _render_sources(chunks)

        st.session_state.chat_history.append({
            "role":    "assistant",
            "content": answer,
            "sources": chunks if st.session_state.show_sources else None,
        })


# ── helpers ────────────────────────────────────────────────────────────────

def _panel_header():
    st.markdown("""
    <div style="background:linear-gradient(90deg,#1e293b 0%,#334155 100%);
         padding:1rem;border-radius:8px;margin-bottom:1rem;text-align:center;border:1px solid #475569;">
      <h3 style="color:white;margin:0;font-size:1.2rem;font-weight:600;">🤖 AI Assistant</h3>
      <p style="color:rgba(255,255,255,0.85);margin:0.3rem 0 0 0;font-size:0.8rem;">
        Intelligent Query Processing
      </p>
    </div>""", unsafe_allow_html=True)


def _render_sources(sources: list):
    for i, src in enumerate(sources, 1):
        page = estimate_page(src.get("id", 0))
        page_info = f" (~Page {page})" if page else ""
        similarity = src.get("similarity", 0)
        preview = src.get("text", "")[:300]

        st.markdown(f"""
        <div class="source-passage">
          <div class="source-header">
            <span>📄 Passage {i}{page_info}</span>
            <span class="source-similarity">{similarity:.3f}</span>
          </div>
          <div>{preview}...</div>
        </div>""", unsafe_allow_html=True)
