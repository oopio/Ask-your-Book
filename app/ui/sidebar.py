"""
Sidebar — document library, filters, upload, settings.
Calls backend/pipeline and updates state; never touches RAG directly.
"""

import os
import streamlit as st
from app.ui import state
from app.backend import pipeline, library, filters as filter_engine
from app.backend import metadata_store


def render():
    """Render the full sidebar. Call once per page run inside `with st.sidebar:`."""
    _brand_header()
    _init_library()
    _filters_section()
    _library_section()
    st.markdown("---")
    _upload_section()
    st.markdown("---")
    _settings_section()


# ── sections ───────────────────────────────────────────────────────────────

def _brand_header():
    st.markdown("""
    <div style="text-align:center;padding:1.2rem;background:linear-gradient(135deg,#1e293b 0%,#334155 100%);
         border-radius:8px;margin-bottom:1rem;border:1px solid #475569;">
      <h2 style="color:white;margin:0;font-size:1.4rem;font-weight:700;">📚 ASK YOUR BOOK</h2>
      <p style="color:rgba(255,255,255,0.8);margin:0.5rem 0 0 0;font-size:0.85rem;">
        Professional Document Intelligence
      </p>
    </div>""", unsafe_allow_html=True)


def _init_library():
    """One-time startup: discover books and auto-load the first one."""
    if not st.session_state.initialized:
        st.session_state.available_books = library.list_books()
        st.session_state.initialized = True

        if st.session_state.available_books and st.session_state.database is None:
            first = st.session_state.available_books[0]
            db, stats = pipeline.load_book(first["path"], first["name"])
            if db is not None:
                state.activate_book(db, stats, first["pdf_path"] or "", first["name"])


def _filters_section():
    if not st.session_state.available_books:
        return

    st.markdown(_section_header("🔍 Advanced Filters"), unsafe_allow_html=True)

    with st.container():
        st.session_state.filter_search = st.text_input(
            "Search documents",
            value=st.session_state.filter_search,
            placeholder="Enter document name...",
            key="search_input",
        )

        all_cats = metadata_store.all_categories()
        all_tags = metadata_store.all_tags()

        if all_cats:
            st.session_state.filter_categories = st.multiselect(
                "Categories", options=all_cats,
                default=st.session_state.filter_categories, key="categories_input",
            )
        if all_tags:
            st.session_state.filter_tags = st.multiselect(
                "Tags", options=all_tags,
                default=st.session_state.filter_tags, key="tags_input",
            )

        st.session_state.filter_page_range = tuple(st.slider(
            "Page count", 0, 2000,
            value=tuple(st.session_state.filter_page_range),
            step=50, key="page_range_input",
        ))

        if st.button("Clear Filters", use_container_width=True):
            state.clear_filters()
            st.rerun()

    st.markdown("---")


def _library_section():
    if not st.session_state.available_books:
        return

    st.markdown(_section_header("📚 Document Library"), unsafe_allow_html=True)

    active_filters = state.current_filters()

    # Build metadata-format list for the filter engine
    books_meta = []
    for book in st.session_state.available_books:
        if book.get("metadata"):
            entry = book["metadata"].copy()
        else:
            entry = {
                "document_name": book["name"],
                "categories": [],
                "tags": [],
                "page_count": book["pages"],
            }
        entry["_book_ref"] = book
        books_meta.append(entry)

    filtered_meta = filter_engine.apply(books_meta, active_filters)
    filtered = [e["_book_ref"] for e in filtered_meta]

    if filter_engine.is_active(active_filters):
        st.caption(f"Showing {len(filtered)} of {len(st.session_state.available_books)} document(s)")
    else:
        st.caption(f"{len(filtered)} document(s)")

    if not filtered:
        st.info("No documents match the current filters.")
        return

    for book in filtered:
        _book_card(book)


def _book_card(book: dict):
    is_current = st.session_state.current_book == book["name"]
    status_class = "active" if is_current else "available"
    status_label = "ACTIVE" if is_current else "AVAILABLE"

    badges_html = ""
    tags_html   = ""
    if book.get("metadata"):
        for cat in book["metadata"].get("categories", [])[:3]:
            badges_html += f'<span class="badge-category">{cat}</span>'
        tags = book["metadata"].get("tags", [])
        for tag in tags[:5]:
            tags_html += f'<span class="badge-tag">#{tag}</span>'
        if len(tags) > 5:
            tags_html += f'<span class="badge-tag">+{len(tags)-5} more</span>'

    st.markdown(f"""
    <div class="book-card {'active' if is_current else ''}">
      <div class="book-title">{book['name']}</div>
      <div class="book-meta">{book['pages']} pages</div>
      <div>{badges_html}</div>
      <div>{tags_html}</div>
      <span class="status-badge status-{status_class}">{status_label}</span>
    </div>""", unsafe_allow_html=True)

    if not is_current:
        if st.button("Load", key=f"load_{book['path']}", use_container_width=True):
            with st.spinner("Loading..."):
                db, stats = pipeline.load_book(book["path"], book["name"])
                if db is not None:
                    # No embeddings yet — attempt silent regeneration
                    if len(db) == 0:
                        from app.backend.pipeline import regenerate_embeddings
                        new_db, n_ok, _ = regenerate_embeddings(book["path"])
                        if new_db:
                            db = new_db
                            stats["total_chunks"] = len(new_db)
                    state.activate_book(db, stats, book["pdf_path"] or "", book["name"])
                    st.session_state.available_books = library.list_books()
            st.rerun()


def _upload_section():
    # On Streamlit Cloud the disk is ephemeral — uploads would be lost on restart.
    # Hide this section for deployed users; keep it available locally.
    is_cloud = (
        os.environ.get("STREAMLIT_SHARING_MODE") is not None
        or os.environ.get("IS_STREAMLIT_CLOUD") is not None
        or not os.path.exists(".env")
    )
    if is_cloud:
        return

    st.markdown(_section_header("📤 Upload Document"), unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Select PDF file", type=["pdf"],
        help="Upload a PDF document", label_visibility="collapsed",
    )

    if uploaded is not None:
        st.caption(uploaded.name)
        if st.button("Upload & Load", type="primary", use_container_width=True):
            with st.spinner("Processing..."):
                db, stats, pdf_path = pipeline.process(uploaded)

            if db is not None:
                state.activate_book(db, stats, pdf_path or "", stats["filename"])
                st.session_state.available_books = library.list_books()
                if len(db) > 0:
                    st.success("✅ Ready")
                else:
                    st.warning("📄 Loaded — chat unavailable until API is active")
                st.rerun()
            else:
                st.error("Upload failed. Check the file and try again.")


def _settings_section():
    with st.expander("Settings"):
        st.session_state.num_passages = st.slider(
            "Retrieval depth", 1, 10, st.session_state.num_passages
        )
        st.session_state.show_sources = st.checkbox(
            "Show sources", value=st.session_state.show_sources
        )


# ── helpers ────────────────────────────────────────────────────────────────

def _section_header(title: str) -> str:
    return (
        f'<div style="background:linear-gradient(135deg,#1e293b 0%,#334155 100%);'
        f'padding:0.8rem;border-radius:8px;margin:1rem 0;text-align:center;border:1px solid #475569;">'
        f'<h4 style="color:white;margin:0;font-size:1rem;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.5px;">{title}</h4></div>'
    )
