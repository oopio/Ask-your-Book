"""
PDF viewer panel.
Renders the document using streamlit-pdf-viewer.
The widget key includes active_book_key so it re-mounts on every book switch.
"""

import os
import streamlit as st

try:
    from streamlit_pdf_viewer import pdf_viewer as _pdf_viewer
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


def render(view_mode: str):
    """Render the PDF viewer inside the current column/container."""
    _panel_header()

    if not _AVAILABLE:
        st.warning("📦 PDF viewer not installed: `pip install streamlit-pdf-viewer`")
        return

    pdf_path = st.session_state.current_pdf_path

    if pdf_path and os.path.exists(pdf_path):
        try:
            with open(pdf_path, "rb") as f:
                data = f.read()
            height = 700 if view_mode == "pdf" else 600
            _pdf_viewer(
                data,
                height=height,
                key=f"pdf_viewer_{st.session_state.active_book_key}",
            )
        except Exception as exc:
            st.error(f"Error loading PDF: {exc}")
    elif pdf_path:
        st.warning("PDF file not found. The document database is available but the original PDF is missing.")
    else:
        st.info("No document loaded. Upload or select a document from the sidebar.")


def _panel_header():
    st.markdown("""
    <div style="background:linear-gradient(90deg,#1e293b 0%,#334155 100%);
         padding:1rem;border-radius:8px;margin-bottom:1rem;text-align:center;border:1px solid #475569;">
      <h3 style="color:white;margin:0;font-size:1.2rem;font-weight:600;">📄 Document Viewer</h3>
      <p style="color:rgba(255,255,255,0.85);margin:0.3rem 0 0 0;font-size:0.8rem;">
        Interactive Document Analysis
      </p>
    </div>""", unsafe_allow_html=True)
