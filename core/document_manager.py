"""
Enhanced Document Manager
Centralized document operations with caching and optimization
"""

import os
import csv
import json
import tempfile
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import streamlit as st

from core.ingestion import (
    extract_text_from_book,
    clean_text,
    chunk_text_by_sentences,
    get_embedding
)
from core.metadata import (
    generate_metadata,
    save_metadata,
    load_metadata,
    extract_first_n_words
)
from ui.error_handler import ErrorHandler

class DocumentManager:
    """Enhanced document management with caching and error handling"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.cache = {}
        self.books_dir = Path("data/books")
        self.pdfs_dir = Path("data/pdfs")
        
        # Ensure directories exist
        self.books_dir.mkdir(parents=True, exist_ok=True)
        self.pdfs_dir.mkdir(parents=True, exist_ok=True)
    
    def find_available_books(self) -> List[Dict]:
        """Find all available book databases with metadata and caching"""
        cache_key = "available_books"
        
        # Check cache first
        if cache_key in self.cache:
            cache_time, cached_books = self.cache[cache_key]
            # Cache for 5 minutes
            if (datetime.now() - cache_time).seconds < 300:
                return cached_books
        
        books = []
        
        try:
            for file in self.books_dir.glob("book_db_*.csv"):
                try:
                    database = self._load_database_from_csv(file)
                    if not database:
                        continue
                    
                    total_words = sum(int(chunk.get('word_count', 0)) for chunk in database)
                    book_name = self._extract_book_name_from_path(file.name)
                    pdf_path = self._find_pdf_for_book(book_name)
                    
                    # Load metadata if available
                    metadata = load_metadata(str(file))
                    
                    book_info = {
                        'name': book_name,
                        'path': str(file),
                        'pdf_path': pdf_path,
                        'chunks': len(database),
                        'words': total_words,
                        'pages': max(1, total_words // 250),
                        'metadata': metadata,
                        'file_size': file.stat().st_size,
                        'modified': datetime.fromtimestamp(file.stat().st_mtime)
                    }
                    
                    books.append(book_info)
                    
                except Exception as e:
                    self.error_handler.handle_file_error(e, str(file), "loading book info")
                    continue
            
            # Sort by modification date (newest first)
            books.sort(key=lambda x: x['modified'], reverse=True)
            
            # Cache the results
            self.cache[cache_key] = (datetime.now(), books)
            
            return books
            
        except Exception as e:
            self.error_handler.handle_critical_error(e, "Finding available books")
            return []
    
    def load_book_by_path(self, book_path: str, book_name: str) -> Tuple[Optional[List], Optional[Dict]]:
        """Load a book database by file path with caching"""
        cache_key = f"book_data_{book_path}"
        
        # Check cache first
        if cache_key in self.cache:
            cache_time, cached_data = self.cache[cache_key]
            # Cache for 10 minutes
            if (datetime.now() - cache_time).seconds < 600:
                return cached_data
        
        try:
            database = self._load_database_from_csv(book_path)
            if not database:
                return None, None
            
            total_words = sum(int(chunk.get('word_count', 0)) for chunk in database)
            
            stats = {
                'filename': book_name,
                'total_chunks': len(database),
                'total_words': total_words,
                'csv_path': book_path,
                'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'estimated_pages': max(1, total_words // 250)
            }
            
            # Cache the results
            result = (database, stats)
            self.cache[cache_key] = (datetime.now(), result)
            
            return result
            
        except Exception as e:
            self.error_handler.handle_file_error(e, book_path, "loading book database")
            return None, None
    
    def process_uploaded_file(self, uploaded_file) -> Optional[Tuple[List, Dict, str]]:
        """Process uploaded file with enhanced error handling and progress tracking"""
        
        # Create temporary file
        try:
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=Path(uploaded_file.name).suffix
            ) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
        except Exception as e:
            self.error_handler.handle_file_error(e, uploaded_file.name, "creating temporary file")
            return None
        
        try:
            # Setup progress tracking
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Extract text
                status_text.text("Step 1/6: Extracting text from document...")
                progress_bar.progress(10)
                
                text = extract_text_from_book(tmp_path)
                if not text:
                    self.error_handler.handle_processing_error(
                        Exception("No text extracted"), "text extraction"
                    )
                    return None
                
                # Step 2: Clean text
                status_text.text("Step 2/6: Cleaning and normalizing text...")
                progress_bar.progress(20)
                
                text = clean_text(text)
                
                # Step 3: Chunk text
                status_text.text("Step 3/6: Splitting text into chunks...")
                progress_bar.progress(30)
                
                chunks = chunk_text_by_sentences(text, chunk_size=500, overlap=50)
                
                if not chunks:
                    self.error_handler.handle_processing_error(
                        Exception("No chunks created"), "text chunking"
                    )
                    return None
                
                # Step 4: Generate embeddings
                status_text.text(f"Step 4/6: Generating embeddings ({len(chunks)} chunks)...")
                
                processed_chunks = []
                for i, chunk in enumerate(chunks):
                    progress = 30 + int((i / len(chunks)) * 40)
                    progress_bar.progress(progress)
                    status_text.text(f"Step 4/6: Processing chunk {i+1}/{len(chunks)}...")
                    
                    try:
                        embedding = get_embedding(chunk['text'])
                        if embedding:
                            processed_chunks.append({
                                'id': chunk['id'],
                                'text': chunk['text'],
                                'word_count': chunk['word_count'],
                                'embedding': embedding
                            })
                    except Exception as e:
                        self.error_handler.handle_api_error(e, "embedding generation")
                        # Continue with other chunks
                        continue
                
                if not processed_chunks:
                    self.error_handler.handle_processing_error(
                        Exception("No embeddings generated"), "embedding generation"
                    )
                    return None
                
                # Step 5: Save database
                status_text.text("Step 5/6: Saving vector database...")
                progress_bar.progress(75)
                
                safe_filename = self._create_safe_filename(uploaded_file.name)
                csv_path = self._save_database_to_csv(processed_chunks, safe_filename)
                
                # Calculate stats
                total_words = sum(int(c['word_count']) for c in processed_chunks)
                page_count = max(1, total_words // 250)
                file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                
                # Step 6: Generate metadata
                status_text.text("Step 6/6: Generating AI metadata...")
                progress_bar.progress(85)
                
                try:
                    sample_text = extract_first_n_words(text, 2000)
                    
                    metadata = generate_metadata(
                        document_text=sample_text,
                        document_name=Path(uploaded_file.name).stem,
                        page_count=page_count,
                        word_count=total_words,
                        csv_path=csv_path,
                        file_size_mb=file_size_mb
                    )
                    
                    save_metadata(metadata, csv_path)
                    
                except Exception as e:
                    self.error_handler.handle_warning(
                        "Metadata generation failed",
                        f"Document uploaded successfully but AI categorization failed: {e}"
                    )
                
                progress_bar.progress(100)
                status_text.text("✅ Document processed successfully!")
                
                # Clear cache to reflect new document
                self.clear_cache()
                
                stats = {
                    'filename': uploaded_file.name,
                    'total_chunks': len(processed_chunks),
                    'total_words': total_words,
                    'csv_path': csv_path,
                    'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'estimated_pages': page_count
                }
                
                return processed_chunks, stats, tmp_path
                
        except Exception as e:
            self.error_handler.handle_processing_error(e, "document processing")
            return None
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def find_text_in_chunks(self, search_text: str, database: List[Dict], threshold: float = 0.7) -> List[Dict]:
        """Find chunks that contain or are similar to the search text"""
        if not search_text or not database:
            return []
        
        try:
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
                            from core.query import cosine_similarity
                            similarity = cosine_similarity(search_embedding, chunk['embedding'])
                            if similarity >= threshold:
                                matching_chunks.append({
                                    'chunk': chunk,
                                    'match_type': 'semantic',
                                    'relevance': similarity
                                })
                    except Exception as e:
                        # Skip this chunk if embedding fails
                        continue
            
            # Sort by relevance and return top 5
            matching_chunks.sort(key=lambda x: x['relevance'], reverse=True)
            return matching_chunks[:5]
            
        except Exception as e:
            self.error_handler.handle_critical_error(e, "text matching")
            return []
    
    def get_context_around_chunk(self, chunk_id: str, database: List[Dict], context_size: int = 2) -> List[Dict]:
        """Get surrounding chunks for context"""
        if not database:
            return []
        
        try:
            # Find the target chunk
            target_chunk = None
            chunk_index = None
            
            for i, chunk in enumerate(database):
                if str(chunk['id']) == str(chunk_id):
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
                position = 'before' if i < chunk_index else 'after' if i > chunk_index else 'target'
                
                context_chunks.append({
                    'chunk': chunk,
                    'is_target': is_target,
                    'position': position
                })
            
            return context_chunks
            
        except Exception as e:
            self.error_handler.handle_critical_error(e, "context extraction")
            return []
    
    def estimate_page_from_chunk_id(self, chunk_id: str, total_pages: int = None) -> int:
        """Estimate page number from chunk ID"""
        try:
            chunk_num = int(chunk_id)
            if not total_pages:
                total_pages = 300  # Default estimate
            
            # Rough estimation: assume chunks are distributed evenly across pages
            estimated_page = min(int((chunk_num / 100) * total_pages), total_pages)
            return max(1, estimated_page)
            
        except (ValueError, TypeError):
            return 1
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'cached_items': len(self.cache),
            'cache_size_mb': sum(
                len(str(data)) for _, data in self.cache.values()
            ) / (1024 * 1024)
        }
    
    # Private helper methods
    
    def _load_database_from_csv(self, csv_path) -> Optional[List[Dict]]:
        """Load database from CSV file"""
        try:
            database = []
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
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
                        
                    except (json.JSONDecodeError, KeyError) as e:
                        # Skip malformed rows
                        continue
            
            return database
            
        except Exception as e:
            self.error_handler.handle_file_error(e, str(csv_path), "loading CSV database")
            return None
    
    def _save_database_to_csv(self, chunks: List[Dict], filename: str) -> str:
        """Save processed chunks to CSV database"""
        csv_path = self.books_dir / f"book_db_{filename}.csv"
        
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
        
        return str(csv_path)
    
    def _extract_book_name_from_path(self, file_path: str) -> str:
        """Extract a clean book name from file path"""
        if file_path.startswith('book_db_') and file_path.endswith('.csv'):
            name = file_path.replace('book_db_', '').replace('.csv', '')
            name = name.replace('_', ' ')
            return name
        
        return Path(file_path).stem
    
    def _find_pdf_for_book(self, book_name: str) -> Optional[str]:
        """Find the PDF file for a given book name"""
        if not self.pdfs_dir.exists():
            return None
        
        book_name_clean = book_name.lower().replace('_', ' ').replace('-', ' ')
        
        # Try exact match first
        for pdf_file in self.pdfs_dir.glob("*.pdf"):
            file_name_clean = pdf_file.stem.lower()
            
            if book_name_clean == file_name_clean:
                return str(pdf_file)
        
        # Try fuzzy match
        for pdf_file in self.pdfs_dir.glob("*.pdf"):
            file_name_clean = pdf_file.stem.lower()
            
            if book_name_clean in file_name_clean or file_name_clean in book_name_clean:
                return str(pdf_file)
        
        # Try matching key words (for books with long names)
        book_words = set(book_name_clean.split())
        best_match = None
        best_score = 0
        
        for pdf_file in self.pdfs_dir.glob("*.pdf"):
            file_name_clean = pdf_file.stem.lower()
            file_words = set(file_name_clean.split())
            
            matching_words = book_words.intersection(file_words)
            score = len(matching_words)
            
            if score > best_score and score >= 2:  # At least 2 words match
                best_score = score
                best_match = str(pdf_file)
        
        return best_match
    
    def _create_safe_filename(self, filename: str) -> str:
        """Create a safe filename for database storage"""
        safe_name = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return safe_name or "document"