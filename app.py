"""
Ask Your Book - Document Intelligence Platform
AI-powered document Q&A with PDF viewer, smart categorization, and filtering
"""

import streamlit as st
import os
import sys
import tempfile
from datetime import datetime
import csv
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ingestion import (
    extract_text_from_book,
    clean_text,
    chunk_text_by_sentences,
    get_embedding
)
from core.query import (
    search_book,
    generate_answer,
    cosine_similarity
)
from core.metadata import (
    generate_metadata,
    save_metadata,
    load_metadata,
    extract_first_n_words,
    get_all_categories,
    get_all_tags
)
from core.filters import (
    apply_filters,
    is_filter_active
)

try:
    from streamlit_pdf_viewer import pdf_viewer
    PDF_VIEWER_AVAILABLE = True
except ImportError:
    PDF_VIEWER_AVAILABLE = False
    print("⚠ streamlit-pdf-viewer not installed. PDF viewing disabled.")

# View mode state
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'split'  # 'pdf', 'chat', 'split'

# Dark/Light mode state
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True  # Default to dark mode

# Page configuration
st.set_page_config(
    page_title="ASK YOUR BOOK - Professional Document Intelligence Platform",
    page_icon="�",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS with dark/light mode, glassmorphism, and animations
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {{
        --primary-bg: {'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' if st.session_state.dark_mode else 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)'};
        --secondary-bg: {'rgba(30, 41, 59, 0.8)' if st.session_state.dark_mode else 'rgba(255, 255, 255, 0.8)'};
        --glass-bg: {'rgba(30, 41, 59, 0.1)' if st.session_state.dark_mode else 'rgba(255, 255, 255, 0.1)'};
        --text-primary: {'#f8fafc' if st.session_state.dark_mode else '#1e293b'};
        --text-secondary: {'#94a3b8' if st.session_state.dark_mode else '#64748b'};
        --border-color: {'rgba(148, 163, 184, 0.2)' if st.session_state.dark_mode else 'rgba(100, 116, 139, 0.2)'};
        --accent-primary: #3b82f6;
        --accent-secondary: #8b5cf6;
        --success: #10b981;
        --shadow-light: {'0 4px 20px rgba(0, 0, 0, 0.3)' if st.session_state.dark_mode else '0 4px 20px rgba(0, 0, 0, 0.1)'};
        --shadow-heavy: {'0 8px 40px rgba(0, 0, 0, 0.4)' if st.session_state.dark_mode else '0 8px 40px rgba(0, 0, 0, 0.15)'};
    }}
    
    /* Global Styles */
    .main {{
        padding: 0.5rem;
        background: var(--primary-bg);
        min-height: 100vh;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    /* Glassmorphism Cards */
    .glass-card {{
        background: var(--secondary-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        box-shadow: var(--shadow-light);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    
    .glass-card:hover {{
        transform: translateY(-8px) scale(1.02);
        box-shadow: var(--shadow-heavy);
        border-color: var(--accent-primary);
    }}
    
    /* Book Card with enhanced glassmorphism */
    .book-card {{
        background: var(--secondary-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    
    .book-card::after {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
        transition: width 0.3s ease;
    }}
    
    .book-card:hover {{
        transform: translateY(-6px) scale(1.02);
        box-shadow: var(--shadow-heavy);
        border-color: var(--accent-primary);
    }}
    
    .book-card:hover::after {{
        width: 8px;
    }}
    
    .book-card.active {{
        border-color: var(--success);
        background: {'rgba(16, 185, 129, 0.1)' if st.session_state.dark_mode else 'rgba(16, 185, 129, 0.05)'};
        animation: pulse-glow 3s ease-in-out infinite;
    }}
    
    @keyframes pulse-glow {{
        0%, 100% {{ box-shadow: 0 0 20px rgba(16, 185, 129, 0.3); }}
        50% {{ box-shadow: 0 0 30px rgba(16, 185, 129, 0.5); }}
    }}
    
    .book-title {{
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }}
    
    .book-card:hover .book-title {{
        color: var(--accent-primary);
        transform: translateX(4px);
    }}
    
    .book-meta {{
        font-size: 0.85rem;
        color: var(--text-secondary);
        transition: color 0.3s ease;
    }}
    
    /* Modern Status Badges */
    .status-badge {{
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.75rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        position: relative;
        overflow: hidden;
    }}
    
    .status-active {{
        background: linear-gradient(135deg, var(--success) 0%, #059669 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }}
    
    .status-available {{
        background: {'rgba(59, 130, 246, 0.2)' if st.session_state.dark_mode else 'rgba(59, 130, 246, 0.1)'};
        color: var(--accent-primary);
        border: 1px solid var(--accent-primary);
    }}
    
    .status-available:hover {{
        background: var(--accent-primary);
        color: white;
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }}
    
    /* Enhanced Category and Tag Badges */
    .badge-category {{
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-top: 0.5rem;
        display: inline-block;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .badge-category:hover {{
        transform: scale(1.1) rotate(2deg);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }}
    
    .badge-tag {{
        background: {'rgba(148, 163, 184, 0.2)' if st.session_state.dark_mode else 'rgba(100, 116, 139, 0.1)'};
        color: var(--text-secondary);
        padding: 0.25rem 0.7rem;
        border-radius: 10px;
        font-size: 0.65rem;
        font-weight: 500;
        margin-right: 0.4rem;
        margin-top: 0.4rem;
        display: inline-block;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        border: 1px solid var(--border-color);
    }}
    
    .badge-tag:hover {{
        background: var(--accent-primary);
        color: white;
        transform: scale(1.05);
        border-color: var(--accent-primary);
    }}
    
    /* Source Passages with glassmorphism */
    .source-passage {{
        background: var(--secondary-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.75rem 0;
        font-size: 0.9rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }}
    
    .source-passage:hover {{
        transform: translateX(8px) scale(1.02);
        box-shadow: var(--shadow-light);
        border-color: var(--accent-primary);
    }}
    
    .source-header {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.75rem;
        font-weight: 600;
        color: var(--text-primary);
        font-size: 0.85rem;
    }}
    
    .source-similarity {{
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    
    /* Page Jump Button */
    .page-jump-button {{
        background: linear-gradient(135deg, var(--success) 0%, #059669 100%);
        color: white;
        border: none;
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        font-size: 0.75rem;
        cursor: pointer;
        margin-left: 0.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }}
    
    .page-jump-button:hover {{
        transform: scale(1.1);
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
    }}
    
    /* Loading Shimmer Animation */
    @keyframes shimmer-loading {{
        0% {{ background-position: -200px 0; }}
        100% {{ background-position: calc(200px + 100%) 0; }}
    }}
    
    .shimmer {{
        background: {'linear-gradient(90deg, #374151 25%, #4b5563 50%, #374151 75%)' if st.session_state.dark_mode else 'linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%)'};
        background-size: 200px 100%;
        animation: shimmer-loading 1.5s infinite;
        border-radius: 8px;
        height: 20px;
        margin: 0.5rem 0;
    }}
    
    /* Typing Animation */
    @keyframes typing {{
        0%, 60%, 100% {{ transform: translateY(0); }}
        30% {{ transform: translateY(-10px); }}
    }}
    
    .typing-indicator {{
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 1rem;
    }}
    
    .typing-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--accent-primary);
        animation: typing 1.4s infinite ease-in-out;
    }}
    
    .typing-dot:nth-child(1) {{ animation-delay: 0s; }}
    .typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
    .typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
    
    /* View Mode Toggle Buttons */
    .stButton > button {{
        border-radius: 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid var(--border-color) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        font-size: 0.85rem !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
    }}
    
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
        color: white !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3) !important;
        transform: scale(1.05) !important;
        border-color: var(--accent-primary) !important;
    }}
    
    .stButton > button[kind="secondary"] {{
        background: var(--secondary-bg) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-color) !important;
    }}
    
    .stButton > button[kind="secondary"]:hover {{
        background: var(--glass-bg) !important;
        color: var(--text-primary) !important;
        border-color: var(--accent-primary) !important;
        transform: scale(1.02) !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2) !important;
    }}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {{ width: 8px; }}
    ::-webkit-scrollbar-track {{ background: var(--glass-bg); border-radius: 10px; }}
    ::-webkit-scrollbar-thumb {{ background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%); border-radius: 10px; }}
    
    /* Hide Streamlit elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{display:none;}}
    
    /* Responsive Layout */
    @media (max-width: 768px) {{
        .main {{ padding: 0.25rem; }}
        .glass-card {{ border-radius: 12px; padding: 1rem; }}
        .book-card {{ padding: 1rem; margin-bottom: 0.75rem; }}
    }}
    
    .single-view-container {{ max-width: 100% !important; padding: 0 1rem !important; }}
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'current_book' not in st.session_state:
    st.session_state.current_book = None

if 'current_pdf_path' not in st.session_state:
    st.session_state.current_pdf_path = None

if 'database' not in st.session_state:
    st.session_state.database = None

if 'book_stats' not in st.session_state:
    st.session_state.book_stats = None

if 'available_books' not in st.session_state:
    st.session_state.available_books = []

if 'initialized' not in st.session_state:
    st.session_state.initialized = False

# Filter state
if 'filter_search' not in st.session_state:
    st.session_state.filter_search = ""

if 'filter_categories' not in st.session_state:
    st.session_state.filter_categories = []

if 'filter_tags' not in st.session_state:
    st.session_state.filter_tags = []

if 'filter_date_range' not in st.session_state:
    st.session_state.filter_date_range = []

if 'filter_page_range' not in st.session_state:
    st.session_state.filter_page_range = (0, 2000)


def find_text_in_chunks(search_text, database, threshold=0.7):
    """Find chunks that contain or are similar to the search text"""
    if not search_text or not database:
        return []
    
    matching_chunks = []
    search_text_lower = search_text.lower()
    
    for chunk in database:
        chunk_text_lower = chunk['text'].lower()
        
        # Direct text match
        if search_text_lower in chunk_text_lower:
            matching_chunks.append({
                'chunk': chunk,
                'match_type': 'direct',
                'relevance': 1.0
            })
        else:
            # Semantic similarity match
            try:
                search_embedding = get_embedding(search_text)
                if search_embedding:
                    similarity = cosine_similarity(search_embedding, chunk['embedding'])
                    if similarity >= threshold:
                        matching_chunks.append({
                            'chunk': chunk,
                            'match_type': 'semantic',
                            'relevance': similarity
                        })
            except:
                continue
    
    # Sort by relevance
    matching_chunks.sort(key=lambda x: x['relevance'], reverse=True)
    return matching_chunks[:5]  # Return top 5 matches


def extract_page_from_chunk_id(chunk_id, total_pages=None):
    """Estimate page number from chunk ID (rough approximation)"""
    if not total_pages:
        total_pages = 300  # Default estimate
    
    # Rough estimation: assume chunks are distributed evenly across pages
    estimated_page = min(int((chunk_id / 100) * total_pages), total_pages)
    return max(1, estimated_page)


def get_context_around_chunk(chunk_id, database, context_size=2):
    """Get surrounding chunks for context"""
    if not database:
        return []
    
    # Find the chunk
    target_chunk = None
    chunk_index = None
    
    for i, chunk in enumerate(database):
        if chunk['id'] == chunk_id:
            target_chunk = chunk
            chunk_index = i
            break
    
    if target_chunk is None:
        return []
    
    # Get surrounding chunks
    start_idx = max(0, chunk_index - context_size)
    end_idx = min(len(database), chunk_index + context_size + 1)
    
    context_chunks = []
    for i in range(start_idx, end_idx):
        chunk = database[i]
        is_target = (i == chunk_index)
        context_chunks.append({
            'chunk': chunk,
            'is_target': is_target,
            'position': 'before' if i < chunk_index else 'after' if i > chunk_index else 'target'
        })
    
    return context_chunks


def save_database_to_csv(chunks, filename):
    """Save processed chunks to CSV database"""
    # Ensure data/books directory exists
    os.makedirs("data/books", exist_ok=True)
    csv_path = f"data/books/book_db_{filename}.csv"
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'text', 'word_count', 'embedding'])
        
        for chunk in chunks:
            embedding_str = json.dumps(chunk['embedding'])
            writer.writerow([
                chunk['id'],
                chunk['text'],
                chunk['word_count'],
                embedding_str
            ])
    
    return csv_path


def load_database_from_csv(csv_path):
    """Load database from CSV (supports both old and new format with pages)"""
    database = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            embedding = json.loads(row['embedding'])
            
            chunk_data = {
                'id': row['id'],
                'text': row['text'],
                'word_count': row['word_count'],
                'embedding': embedding
            }
            
            # Add page info if available (new format)
            if 'pages' in row:
                chunk_data['pages'] = row['pages']
            if 'page_numbers' in row:
                chunk_data['page_numbers'] = json.loads(row['page_numbers'])
            
            database.append(chunk_data)
    
    return database


def extract_book_name_from_path(file_path):
    """Extract a clean book name from file path"""
    if file_path.startswith('book_db_') and file_path.endswith('.csv'):
        name = file_path.replace('book_db_', '').replace('.csv', '')
        name = name.replace('_', ' ')
        return name
    
    if file_path == "book_vector_database.csv":
        for f in os.listdir('.'):
            if 'intelligent investor' in f.lower() and f.endswith('.pdf'):
                return f.replace('.pdf', '')
        return "Primary Document"
    
    return "Unknown Document"


def find_pdf_for_book(book_name):
    """Find the PDF file for a given book name"""
    # Check in data/pdfs directory
    pdf_dir = "data/pdfs"
    if not os.path.exists(pdf_dir):
        return None
    
    # Clean the book name for matching
    book_name_clean = book_name.lower().replace('_', ' ').replace('-', ' ')
    
    # Try exact match first
    for file in os.listdir(pdf_dir):
        if file.endswith('.pdf'):
            file_name_clean = file.replace('.pdf', '').lower()
            
            # Exact match (case-insensitive)
            if book_name_clean == file_name_clean:
                return os.path.join(pdf_dir, file)
    
    # Try fuzzy match
    for file in os.listdir(pdf_dir):
        if file.endswith('.pdf'):
            file_name_clean = file.replace('.pdf', '').lower()
            
            # Check if names match (fuzzy matching)
            if book_name_clean in file_name_clean or file_name_clean in book_name_clean:
                return os.path.join(pdf_dir, file)
    
    # Try matching key words (for books with long names)
    book_words = set(book_name_clean.split())
    best_match = None
    best_score = 0
    
    for file in os.listdir(pdf_dir):
        if file.endswith('.pdf'):
            file_name_clean = file.replace('.pdf', '').lower()
            file_words = set(file_name_clean.split())
            
            # Count matching words
            matching_words = book_words.intersection(file_words)
            score = len(matching_words)
            
            if score > best_score and score >= 2:  # At least 2 words match
                best_score = score
                best_match = os.path.join(pdf_dir, file)
    
    return best_match


def find_available_books():
    """Find all available book databases with metadata"""
    books = []
    
    # Check data/books directory
    books_dir = "data/books"
    if not os.path.exists(books_dir):
        return books
    
    for file in os.listdir(books_dir):
        if file.startswith('book_db_') and file.endswith('.csv'):
            try:
                csv_path = os.path.join(books_dir, file)
                database = load_database_from_csv(csv_path)
                total_words = sum(int(chunk['word_count']) for chunk in database)
                book_name = extract_book_name_from_path(file)
                pdf_path = find_pdf_for_book(book_name)
                
                # Load metadata if available
                metadata = load_metadata(csv_path)
                
                book_info = {
                    'name': book_name,
                    'path': csv_path,
                    'pdf_path': pdf_path,
                    'chunks': len(database),
                    'words': total_words,
                    'pages': total_words // 250,
                    'metadata': metadata  # Include metadata
                }
                
                books.append(book_info)
            except Exception as e:
                continue
    
    return books


def load_book_by_path(book_path, book_name):
    """Load a book database by file path"""
    try:
        database = load_database_from_csv(book_path)
        total_words = sum(int(chunk['word_count']) for chunk in database)
        
        stats = {
            'filename': book_name,
            'total_chunks': len(database),
            'total_words': total_words,
            'csv_path': book_path,
            'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        return database, stats
    except Exception as e:
        st.error(f"Error loading document: {str(e)}")
        return None, None


def process_uploaded_file(uploaded_file):
    """Process uploaded file and create vector database"""
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Step 1/6: Extracting text...")
        progress_bar.progress(10)
        text = extract_text_from_book(tmp_path)
        
        if not text:
            st.error("Failed to extract text")
            return None
        
        status_text.text("Step 2/6: Cleaning text...")
        progress_bar.progress(15)
        text = clean_text(text)
        
        status_text.text("Step 3/6: Chunking...")
        progress_bar.progress(20)
        chunks = chunk_text_by_sentences(text, chunk_size=500, overlap=50)
        
        status_text.text(f"Step 4/6: Generating embeddings ({len(chunks)} chunks)...")
        
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            progress = 20 + int((i / len(chunks)) * 50)
            progress_bar.progress(progress)
            status_text.text(f"Step 4/6: Processing chunk {i+1}/{len(chunks)}...")
            
            embedding = get_embedding(chunk['text'])
            if embedding:
                processed_chunks.append({
                    'id': chunk['id'],
                    'text': chunk['text'],
                    'word_count': chunk['word_count'],
                    'embedding': embedding
                })
        
        status_text.text("Step 5/6: Saving database...")
        progress_bar.progress(75)
        
        safe_filename = "".join(c for c in uploaded_file.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        csv_path = save_database_to_csv(processed_chunks, safe_filename)
        
        # Calculate stats
        total_words = sum(int(c['word_count']) for c in processed_chunks)
        page_count = total_words // 250
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        # Step 6: Generate metadata
        status_text.text("Step 6/6: Generating metadata (AI analysis)...")
        progress_bar.progress(85)
        
        try:
            # Extract first 2000 words for analysis
            sample_text = extract_first_n_words(text, 2000)
            
            # Generate metadata using LLM
            metadata = generate_metadata(
                document_text=sample_text,
                document_name=uploaded_file.name.replace('.pdf', ''),
                page_count=page_count,
                word_count=total_words,
                csv_path=csv_path,
                file_size_mb=file_size_mb
            )
            
            # Save metadata
            save_metadata(metadata, csv_path)
            
            progress_bar.progress(95)
            
        except Exception as e:
            st.warning(f"Metadata generation failed: {e}. Document uploaded successfully.")
        
        progress_bar.progress(100)
        status_text.text("Complete! Document processed with AI categorization.")
        
        stats = {
            'filename': uploaded_file.name,
            'total_chunks': len(processed_chunks),
            'total_words': total_words,
            'csv_path': csv_path,
            'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        return processed_chunks, stats, tmp_path
        
    except Exception as e:
        st.error(f"Error: {e}")
        return None


# Attractive Main Header
st.markdown("""
<div style="text-align: center; padding: 2.5rem 0; background: linear-gradient(135deg, #1e293b 0%, #334155 100%); border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0,0,0,0.15); border: 1px solid #475569;">
    <div style="animation: float 3s ease-in-out infinite;">
        <h1 style="color: white; font-size: 2.8rem; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); font-weight: 700; font-family: 'Inter', sans-serif;">
            � ASK YOUR BOOK
        </h1>
        <p style="color: rgba(255,255,255,0.85); font-size: 1.1rem; margin: 0.5rem 0 0 0; font-weight: 400; letter-spacing: 0.5px;">
            Professional Document Intelligence Platform
        </p>
        <div style="margin-top: 1.5rem;">
            <span style="background: rgba(255,255,255,0.15); padding: 0.4rem 1.2rem; border-radius: 8px; font-size: 0.85rem; color: white; margin: 0 0.5rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">
                � Analytics
            </span>
            <span style="background: rgba(255,255,255,0.15); padding: 0.4rem 1.2rem; border-radius: 8px; font-size: 0.85rem; color: white; margin: 0 0.5rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">
                🔍 Search
            </span>
            <span style="background: rgba(255,255,255,0.15); padding: 0.4rem 1.2rem; border-radius: 8px; font-size: 0.85rem; color: white; margin: 0 0.5rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">
                🤖 AI Insights
            </span>
        </div>
    </div>
</div>

<style>
@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
    100% { transform: translateY(0px); }
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); }
}

.feature-badge {
    animation: pulse 2s ease-in-out infinite;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1.2rem; background: linear-gradient(135deg, #1e293b 0%, #334155 100%); border-radius: 8px; margin-bottom: 1rem; border: 1px solid #475569;">
        <h2 style="color: white; margin: 0; font-size: 1.4rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.3); font-weight: 700;">
            � ASK YOUR BOOK
        </h2>
        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.85rem; font-weight: 400; letter-spacing: 0.3px;">
            Professional Document Intelligence
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize
    if not st.session_state.initialized:
        st.session_state.available_books = find_available_books()
        st.session_state.initialized = True
        
        if st.session_state.available_books and st.session_state.database is None:
            first_book = st.session_state.available_books[0]
            database, stats = load_book_by_path(first_book['path'], first_book['name'])
            if database:
                st.session_state.database = database
                st.session_state.book_stats = stats
                st.session_state.current_book = first_book['name']
                st.session_state.current_pdf_path = first_book['pdf_path']
    
    # Filters Section
    if st.session_state.available_books:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 0.8rem; border-radius: 8px; margin: 1rem 0; text-align: center; border: 1px solid #475569;">
            <h4 style="color: white; margin: 0; font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                🔍 Advanced Filters
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            # Search
            search_query = st.text_input(
                "Search documents",
                value=st.session_state.filter_search,
                placeholder="Enter document name...",
                key="search_input"
            )
            st.session_state.filter_search = search_query
            
            # Get all categories and tags
            all_categories = get_all_categories()
            all_tags = get_all_tags()
            
            # Categories filter
            if all_categories:
                selected_categories = st.multiselect(
                    "Categories",
                    options=all_categories,
                    default=st.session_state.filter_categories,
                    key="categories_input"
                )
                st.session_state.filter_categories = selected_categories
            
            # Tags filter
            if all_tags:
                selected_tags = st.multiselect(
                    "Tags",
                    options=all_tags,
                    default=st.session_state.filter_tags,
                    key="tags_input"
                )
                st.session_state.filter_tags = selected_tags
            
            # Page count filter
            page_range = st.slider(
                "Page count",
                min_value=0,
                max_value=2000,
                value=st.session_state.filter_page_range,
                step=50,
                key="page_range_input"
            )
            st.session_state.filter_page_range = page_range
            
            # Clear filters button
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Clear Filters", use_container_width=True):
                    st.session_state.filter_search = ""
                    st.session_state.filter_categories = []
                    st.session_state.filter_tags = []
                    st.session_state.filter_page_range = (0, 2000)
                    st.rerun()
        
        st.markdown("---")
    
    # Document Library
    if st.session_state.available_books:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 0.8rem; border-radius: 8px; margin: 1rem 0; text-align: center; border: 1px solid #475569;">
            <h4 style="color: white; margin: 0; font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                📚 Document Library
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Apply filters
        filters = {
            'search': st.session_state.filter_search,
            'categories': st.session_state.filter_categories,
            'tags': st.session_state.filter_tags,
            'page_min': st.session_state.filter_page_range[0],
            'page_max': st.session_state.filter_page_range[1]
        }
        
        # Convert books to metadata format for filtering
        books_with_metadata = []
        for book in st.session_state.available_books:
            if book.get('metadata'):
                book_data = book['metadata'].copy()
                book_data['_book_ref'] = book  # Keep reference to original book
                books_with_metadata.append(book_data)
            else:
                # Books without metadata
                book_data = {
                    'document_name': book['name'],
                    'categories': [],
                    'tags': [],
                    'page_count': book['pages'],
                    '_book_ref': book
                }
                books_with_metadata.append(book_data)
        
        # Apply filters
        filtered_books_metadata = apply_filters(books_with_metadata, filters)
        filtered_books = [item['_book_ref'] for item in filtered_books_metadata]
        
        # Show count
        if is_filter_active(filters):
            st.caption(f"Showing {len(filtered_books)} of {len(st.session_state.available_books)} document(s)")
        else:
            st.caption(f"{len(filtered_books)} document(s)")
        
        # Display filtered books
        if not filtered_books:
            st.info("No documents match the current filters")
        
        for book in filtered_books:
            is_current = st.session_state.current_book == book['name']
            
            status_class = "active" if is_current else "available"
            status_text = "ACTIVE" if is_current else "AVAILABLE"
            
            # Build badges HTML
            badges_html = ""
            tags_html = ""
            
            if book.get('metadata'):
                metadata = book['metadata']
                
                # Categories (max 3)
                categories = metadata.get('categories', [])[:3]
                for cat in categories:
                    badges_html += f'<span class="badge-category">{cat}</span>'
                
                # Tags (max 5)
                tags = metadata.get('tags', [])
                for tag in tags[:5]:
                    tags_html += f'<span class="badge-tag">#{tag}</span>'
                
                if len(tags) > 5:
                    tags_html += f'<span class="badge-more">+{len(tags) - 5} more</span>'
            
            st.markdown(f"""
            <div class="book-card {'active' if is_current else ''}">
                <div class="book-title">{book['name']}</div>
                <div class="book-meta">{book['pages']} pages</div>
                <div class="badges-container">
                    {badges_html}
                </div>
                <div class="tags-container">
                    {tags_html}
                </div>
                <span class="status-badge status-{status_class}">{status_text}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if not is_current:
                if st.button("Load", key=f"load_{book['path']}", use_container_width=True):
                    database, stats = load_book_by_path(book['path'], book['name'])
                    if database:
                        st.session_state.database = database
                        st.session_state.book_stats = stats
                        st.session_state.current_book = book['name']
                        st.session_state.current_pdf_path = book['pdf_path']
                        st.session_state.chat_history = []
                        st.rerun()
    
    st.markdown("---")
    
    # Upload
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 0.8rem; border-radius: 8px; margin: 1rem 0; text-align: center; border: 1px solid #475569;">
        <h4 style="color: white; margin: 0; font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
            📤 Upload Document
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Select PDF file",
        type=['pdf'],
        help="Upload a PDF document",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        st.info(f"Selected: {uploaded_file.name}")
        if st.button("Process", type="primary", use_container_width=True):
            with st.spinner("Processing..."):
                result = process_uploaded_file(uploaded_file)
                
                if result:
                    database, stats, pdf_path = result
                    st.session_state.database = database
                    st.session_state.book_stats = stats
                    st.session_state.current_book = stats['filename']
                    st.session_state.current_pdf_path = pdf_path
                    st.session_state.chat_history = []
                    
                    # Refresh available books list to reflect new document
                    st.session_state.available_books = find_available_books()
                    st.success("Complete! Document categorized and ready.")
                    st.rerun()
    
    # Settings
    st.markdown("---")
    with st.expander("Settings"):
        num_passages = st.slider("Retrieval depth", 1, 10, 5)
        show_sources = st.checkbox("Show sources", value=True)

# View Mode Toggle
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <div style="background: white; padding: 0.5rem; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); display: inline-block;">
""", unsafe_allow_html=True)

col_toggle1, col_toggle2, col_toggle3 = st.columns(3)

with col_toggle1:
    if st.button("📄 Document Viewer", 
                 type="primary" if st.session_state.view_mode == 'pdf' else "secondary",
                 use_container_width=True,
                 key="pdf_mode"):
        st.session_state.view_mode = 'pdf'
        st.rerun()

with col_toggle2:
    if st.button("🤖 AI Assistant", 
                 type="primary" if st.session_state.view_mode == 'chat' else "secondary",
                 use_container_width=True,
                 key="chat_mode"):
        st.session_state.view_mode = 'chat'
        st.rerun()

with col_toggle3:
    if st.button("� Dual View", 
                 type="primary" if st.session_state.view_mode == 'split' else "secondary",
                 use_container_width=True,
                 key="split_mode"):
        st.session_state.view_mode = 'split'
        st.rerun()

st.markdown("</div></div>", unsafe_allow_html=True)

# Dynamic Layout based on view mode
if st.session_state.view_mode == 'split':
    # Split View - 2 columns
    col1, col2 = st.columns([1, 1])
elif st.session_state.view_mode == 'pdf':
    # PDF Only - single column
    col1 = st.container()
    col2 = None
else:  # chat mode
    # Chat Only - single column  
    col1 = None
    col2 = st.container()

# PDF Viewer Section
if col1 is not None:
    # Add full-width class for single PDF view
    if st.session_state.view_mode == 'pdf':
        st.markdown('<div class="single-view-container">', unsafe_allow_html=True)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(90deg, #1e293b 0%, #334155 100%); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center; border: 1px solid #475569;">
            <h3 style="color: white; margin: 0; font-size: 1.2rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.3); font-weight: 600;">
                📄 Document Viewer
            </h3>
            <p style="color: rgba(255,255,255,0.85); margin: 0.3rem 0 0 0; font-size: 0.8rem; font-weight: 400;">
                Interactive Document Analysis
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # PDF Viewer
        if not PDF_VIEWER_AVAILABLE:
            st.warning("📦 PDF viewer not installed. Install with: `pip install streamlit-pdf-viewer`")
        elif st.session_state.current_pdf_path and os.path.exists(st.session_state.current_pdf_path):
            try:
                with open(st.session_state.current_pdf_path, "rb") as f:
                    pdf_data = f.read()
                    
                    # Enhanced PDF viewer with dynamic height
                    pdf_viewer_result = pdf_viewer(
                        pdf_data, 
                        height=700 if st.session_state.view_mode == 'pdf' else 600,
                        key="pdf_viewer_main"
                    )
                    
            except Exception as e:
                st.error(f"Error loading PDF: {e}")
                st.info(f"PDF path: {st.session_state.current_pdf_path}")
        elif st.session_state.current_pdf_path:
            st.warning(f"PDF file not found at: {st.session_state.current_pdf_path}")
            st.info("The document database is available, but the original PDF is missing.")
        else:
            st.info("No PDF available for current document")
            if st.session_state.current_book:
                st.caption("Document is loaded but PDF file was not found.")
    
    if st.session_state.view_mode == 'pdf':
        st.markdown('</div>', unsafe_allow_html=True)

# Chat Section
if col2 is not None:
    # Add full-width class for single chat view
    if st.session_state.view_mode == 'chat':
        st.markdown('<div class="single-view-container">', unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(90deg, #1e293b 0%, #334155 100%); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center; border: 1px solid #475569;">
            <h3 style="color: white; margin: 0; font-size: 1.2rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.3); font-weight: 600;">
                🤖 AI Assistant
            </h3>
            <p style="color: rgba(255,255,255,0.85); margin: 0.3rem 0 0 0; font-size: 0.8rem; font-weight: 400;">
                Intelligent Query Processing
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.database is None:
            st.info("Load a document to start chatting")
        else:
            # Chat history display
            for message in st.session_state.chat_history:
                with st.chat_message(message['role']):
                    st.markdown(message['content'])
                    
                    # Enhanced source display
                    if message['role'] == 'assistant' and message.get('sources') and show_sources:
                        with st.expander("📚 View Sources"):
                            for i, source in enumerate(message['sources'], 1):
                                chunk_id = int(source.get('id', 0))
                                estimated_page = extract_page_from_chunk_id(chunk_id)
                                pages_info = f" (~Page {estimated_page})" if estimated_page else ""
                                
                                st.markdown(f"""
                                <div class="source-passage">
                                    <div class="source-header">
                                        <span>📄 Passage {i}{pages_info}</span>
                                        <span class="source-similarity">{source['similarity']:.3f}</span>
                                    </div>
                                    <div>{source['text'][:300]}...</div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown(f"""
                                        <button class="page-jump-button" onclick="alert('Would jump to page {estimated_page}')">
                                           📍 Jump to Page {estimated_page}
                                        </button>
                                        """,
                                        unsafe_allow_html=True)
            
            # Regular chat input
            if question := st.chat_input("Ask a question..."):
                st.session_state.chat_history.append({'role': 'user', 'content': question})
                
                with st.chat_message("user"):
                    st.markdown(question)
                
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing..."):
                        relevant_chunks = search_book(
                            question,
                            st.session_state.database,
                            top_k=num_passages if 'num_passages' in locals() else 5
                        )
                        
                        answer = generate_answer(question, relevant_chunks, show_context=False)
                        st.markdown(answer)
                        
                        # Regular source display
                        if ('show_sources' not in locals() or show_sources) and relevant_chunks:
                            with st.expander("� View Sources"):
                                for i, source in enumerate(relevant_chunks, 1):
                                    chunk_id = int(source.get('id', 0))
                                    estimated_page = extract_page_from_chunk_id(chunk_id)
                                    pages_info = f" (~Page {estimated_page})" if estimated_page else ""
                                    
                                    st.markdown(f"""
                                    <div class="source-passage">
                                        <div class="source-header">
                                            <span>📄 Passage {i}{pages_info}</span>
                                            <span class="source-similarity">{source['similarity']:.3f}</span>
                                        </div>
                                        <div>{source['text'][:300]}...</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    if estimated_page:
                                        st.markdown(f"""
                                        <button class="page-jump-button" onclick="alert('Would jump to page {estimated_page}')">
                                            📍 Jump to Page {estimated_page}
                                        </button>
                                        """, unsafe_allow_html=True)
                
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': answer,
                    'sources': relevant_chunks if ('show_sources' not in locals() or show_sources) else None
                })
    
    if st.session_state.view_mode == 'chat':
        st.markdown('</div>', unsafe_allow_html=True)
