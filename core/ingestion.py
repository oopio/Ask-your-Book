"""
Book Ingestion System for RAG
Supports: TXT, PDF, EPUB formats
"""

import os
import re
import csv
import json
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
BOOK_DATABASE = "book_vector_database.csv"


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from a TXT file
    
    Args:
        file_path: Path to TXT file
    
    Returns:
        Extracted text as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"✓ Extracted text from TXT file: {len(text)} characters")
        return text
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            text = f.read()
        print(f"✓ Extracted text from TXT file (latin-1): {len(text)} characters")
        return text


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        Extracted text as string
    """
    try:
        import PyPDF2
        
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            num_pages = len(pdf_reader.pages)
            
            print(f"Processing PDF: {num_pages} pages...")
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
                
                if (page_num + 1) % 10 == 0:
                    print(f"  Processed {page_num + 1}/{num_pages} pages...")
        
        print(f"✓ Extracted text from PDF: {len(text)} characters")
        return text
    except ImportError:
        print("❌ PyPDF2 not installed. Install with: pip install PyPDF2")
        return ""
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        return ""


def extract_text_from_epub(file_path: str) -> str:
    """
    Extract text from an EPUB file
    
    Args:
        file_path: Path to EPUB file
    
    Returns:
        Extracted text as string
    """
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        
        book = epub.read_epub(file_path)
        text = ""
        
        chapters = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        print(f"Processing EPUB: {len(chapters)} chapters...")
        
        for i, item in enumerate(chapters):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text += soup.get_text() + "\n"
            
            if (i + 1) % 5 == 0:
                print(f"  Processed {i + 1}/{len(chapters)} chapters...")
        
        print(f"✓ Extracted text from EPUB: {len(text)} characters")
        return text
    except ImportError:
        print("❌ ebooklib or beautifulsoup4 not installed.")
        print("Install with: pip install ebooklib beautifulsoup4")
        return ""
    except Exception as e:
        print(f"❌ Error extracting EPUB: {e}")
        return ""


def extract_text_from_book(file_path: str) -> str:
    """
    Extract text from a book file (auto-detects format)
    
    Args:
        file_path: Path to book file
    
    Returns:
        Extracted text as string
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return ""
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    print(f"\n{'='*60}")
    print(f"EXTRACTING TEXT FROM BOOK")
    print(f"{'='*60}")
    print(f"File: {file_path}")
    print(f"Format: {file_ext}")
    print()
    
    if file_ext == '.txt':
        return extract_text_from_txt(file_path)
    elif file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext == '.epub':
        return extract_text_from_epub(file_path)
    else:
        print(f"❌ Unsupported format: {file_ext}")
        print("Supported formats: .txt, .pdf, .epub")
        return ""


def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Raw text
    
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Remove special characters that might cause issues
    text = text.replace('\x00', '')
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def chunk_text_by_sentences(text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """
    Split text into chunks with sentence boundaries and overlap
    
    Args:
        text: Text to chunk
        chunk_size: Target size in words
        overlap: Number of words to overlap between chunks
    
    Returns:
        List of dictionaries with chunk info
    """
    # Split into sentences (simple approach)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_word_count = 0
    chunk_id = 1
    
    for sentence in sentences:
        words = sentence.split()
        word_count = len(words)
        
        # If adding this sentence exceeds chunk_size, save current chunk
        if current_word_count + word_count > chunk_size and current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'id': chunk_id,
                'text': chunk_text,
                'word_count': current_word_count
            })
            
            # Start new chunk with overlap
            overlap_words = ' '.join(current_chunk).split()[-overlap:]
            current_chunk = [' '.join(overlap_words), sentence]
            current_word_count = len(overlap_words) + word_count
            chunk_id += 1
        else:
            current_chunk.append(sentence)
            current_word_count += word_count
    
    # Add the last chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunks.append({
            'id': chunk_id,
            'text': chunk_text,
            'word_count': current_word_count
        })
    
    return chunks


def chunk_text_fixed_size(text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """
    Split text into fixed-size chunks with overlap
    
    Args:
        text: Text to chunk
        chunk_size: Size in words
        overlap: Number of words to overlap
    
    Returns:
        List of dictionaries with chunk info
    """
    words = text.split()
    chunks = []
    chunk_id = 1
    
    i = 0
    while i < len(words):
        # Get chunk
        chunk_words = words[i:i + chunk_size]
        chunk_text = ' '.join(chunk_words)
        
        chunks.append({
            'id': chunk_id,
            'text': chunk_text,
            'word_count': len(chunk_words)
        })
        
        # Move forward by (chunk_size - overlap)
        i += chunk_size - overlap
        chunk_id += 1
    
    return chunks


def get_embedding(text: str) -> List[float]:
    """
    Get embedding vector for text.
    Returns the embedding list on success, or None on failure.
    Stores the last exception message in a module-level variable so callers
    can surface the real error rather than a generic message.
    """
    global _last_embedding_error
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        _last_embedding_error = None
        return response.data[0].embedding
    except Exception as e:
        _last_embedding_error = f"{type(e).__name__}: {e}"
        print(f"❌ Error generating embedding: {e}")
        return None


# Module-level variable to hold the last embedding error for callers to inspect
_last_embedding_error = None


def ingest_book(
    file_path: str,
    output_csv: str = BOOK_DATABASE,
    chunk_size: int = 500,
    overlap: int = 50,
    chunking_method: str = "sentences"
) -> bool:
    """
    Complete book ingestion pipeline
    
    Args:
        file_path: Path to book file
        output_csv: Output CSV file path
        chunk_size: Target chunk size in words
        overlap: Overlap between chunks in words
        chunking_method: "sentences" or "fixed"
    
    Returns:
        True if successful, False otherwise
    """
    print("\n" + "="*60)
    print("BOOK INGESTION PIPELINE")
    print("="*60)
    
    # Step 1: Extract text
    text = extract_text_from_book(file_path)
    if not text:
        return False
    
    # Step 2: Clean text
    print("\nCleaning text...")
    text = clean_text(text)
    word_count = len(text.split())
    print(f"✓ Cleaned text: {word_count} words")
    
    # Step 3: Chunk text
    print(f"\nChunking text (method: {chunking_method}, size: {chunk_size}, overlap: {overlap})...")
    if chunking_method == "sentences":
        chunks = chunk_text_by_sentences(text, chunk_size, overlap)
    else:
        chunks = chunk_text_fixed_size(text, chunk_size, overlap)
    
    print(f"✓ Created {len(chunks)} chunks")
    
    # Step 4: Generate embeddings and save to CSV
    print(f"\nGenerating embeddings and saving to {output_csv}...")
    print("⚠ This will use OpenAI API credits")
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'text', 'word_count', 'embedding'])
        
        for i, chunk in enumerate(chunks, 1):
            print(f"  Processing chunk {i}/{len(chunks)}...", end='\r')
            
            embedding = get_embedding(chunk['text'])
            if embedding:
                embedding_str = json.dumps(embedding)
                writer.writerow([
                    chunk['id'],
                    chunk['text'],
                    chunk['word_count'],
                    embedding_str
                ])
            else:
                print(f"\n⚠ Skipping chunk {i} due to embedding error")
    
    print(f"\n✓ Book ingestion complete!")
    print(f"✓ Database saved: {output_csv}")
    print(f"✓ Total chunks: {len(chunks)}")
    print(f"✓ Average chunk size: {sum(c['word_count'] for c in chunks) / len(chunks):.0f} words")
    print("="*60 + "\n")
    
    return True


def get_book_stats(csv_file: str = BOOK_DATABASE):
    """
    Display statistics about the ingested book
    
    Args:
        csv_file: Path to book database CSV
    """
    if not os.path.exists(csv_file):
        print(f"❌ Database not found: {csv_file}")
        return
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        chunks = list(reader)
    
    if not chunks:
        print("❌ Database is empty")
        return
    
    total_chunks = len(chunks)
    total_words = sum(int(chunk['word_count']) for chunk in chunks)
    avg_words = total_words / total_chunks
    
    print("\n" + "="*60)
    print("BOOK DATABASE STATISTICS")
    print("="*60)
    print(f"Database file: {csv_file}")
    print(f"Total chunks: {total_chunks}")
    print(f"Total words: {total_words:,}")
    print(f"Average words per chunk: {avg_words:.0f}")
    print(f"Estimated book length: ~{total_words / 250:.0f} pages")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("BOOK INGESTION SYSTEM")
    print("="*60)
    print("\nThis script ingests a book into the RAG system.")
    print("Supported formats: TXT, PDF, EPUB")
    print("\nUsage:")
    print("  1. Place your book file in this directory")
    print("  2. Run this script")
    print("  3. Enter the filename when prompted")
    print("\n" + "="*60 + "\n")
    
    # Get book file from user
    book_file = input("Enter book filename (e.g., mybook.txt): ").strip()
    
    if not book_file:
        print("❌ No filename provided")
    elif not os.path.exists(book_file):
        print(f"❌ File not found: {book_file}")
        print("\nMake sure the file is in the current directory.")
    else:
        # Ingest the book
        success = ingest_book(
            file_path=book_file,
            chunk_size=500,
            overlap=50,
            chunking_method="sentences"
        )
        
        if success:
            # Show statistics
            get_book_stats()
            print("\n✓ You can now query the book using book_rag_query.py")
