"""
Enhanced Book Ingestion with Page Number Tracking
"""

import os
import re
import csv
import json
from typing import List, Dict, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import PyPDF2

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

EMBEDDING_MODEL = "text-embedding-3-small"


def extract_text_from_pdf_with_pages(file_path: str) -> List[Dict]:
    """
    Extract text from PDF with page number tracking
    
    Returns:
        List of dicts with 'page_num' and 'text' for each page
    """
    try:
        pages_data = []
        
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            num_pages = len(pdf_reader.pages)
            
            print(f"Processing PDF: {num_pages} pages...")
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                pages_data.append({
                    'page_num': page_num + 1,  # 1-indexed
                    'text': text
                })
                
                if (page_num + 1) % 10 == 0:
                    print(f"  Processed {page_num + 1}/{num_pages} pages...")
        
        print(f"✓ Extracted {len(pages_data)} pages")
        return pages_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def chunk_text_with_page_tracking(pages_data: List[Dict], chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """
    Chunk text while tracking which pages each chunk came from
    
    Args:
        pages_data: List of dicts with page_num and text
        chunk_size: Target chunk size in words
        overlap: Overlap in words
    
    Returns:
        List of chunks with page number ranges
    """
    chunks = []
    chunk_id = 1
    
    current_chunk_words = []
    current_chunk_pages = set()
    
    for page_data in pages_data:
        page_num = page_data['page_num']
        page_text = page_data['text']
        
        # Split page into sentences
        sentences = re.split(r'(?<=[.!?])\s+', page_text)
        
        for sentence in sentences:
            words = sentence.split()
            
            # Add words to current chunk
            current_chunk_words.extend(words)
            current_chunk_pages.add(page_num)
            
            # Check if chunk is large enough
            if len(current_chunk_words) >= chunk_size:
                chunk_text = ' '.join(current_chunk_words)
                page_range = f"{min(current_chunk_pages)}-{max(current_chunk_pages)}" if len(current_chunk_pages) > 1 else str(min(current_chunk_pages))
                
                chunks.append({
                    'id': chunk_id,
                    'text': chunk_text,
                    'word_count': len(current_chunk_words),
                    'pages': page_range,
                    'page_numbers': sorted(list(current_chunk_pages))
                })
                
                # Start new chunk with overlap
                overlap_words = current_chunk_words[-overlap:] if len(current_chunk_words) > overlap else current_chunk_words
                current_chunk_words = overlap_words
                # Keep last page in the set for overlap
                current_chunk_pages = {page_num}
                chunk_id += 1
    
    # Add final chunk if any words remain
    if current_chunk_words:
        chunk_text = ' '.join(current_chunk_words)
        page_range = f"{min(current_chunk_pages)}-{max(current_chunk_pages)}" if len(current_chunk_pages) > 1 else str(min(current_chunk_pages))
        
        chunks.append({
            'id': chunk_id,
            'text': chunk_text,
            'word_count': len(current_chunk_words),
            'pages': page_range,
            'page_numbers': sorted(list(current_chunk_pages))
        })
    
    return chunks


def get_embedding(text: str):
    """Generate embedding for text"""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error: {e}")
        return None


def ingest_pdf_with_pages(pdf_path: str, output_csv: str):
    """
    Complete ingestion pipeline with page tracking
    
    Args:
        pdf_path: Path to PDF file
        output_csv: Output CSV path
    
    Returns:
        True if successful
    """
    print("\n" + "="*70)
    print("PDF INGESTION WITH PAGE TRACKING")
    print("="*70)
    
    # Extract with page numbers
    pages_data = extract_text_from_pdf_with_pages(pdf_path)
    if not pages_data:
        return False
    
    # Chunk with page tracking
    print("\nChunking text with page tracking...")
    chunks = chunk_text_with_page_tracking(pages_data, chunk_size=500, overlap=50)
    print(f"✓ Created {len(chunks)} chunks")
    
    # Generate embeddings
    print(f"\nGenerating embeddings...")
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'text', 'word_count', 'pages', 'page_numbers', 'embedding'])
        
        for i, chunk in enumerate(chunks, 1):
            print(f"  Processing chunk {i}/{len(chunks)}...", end='\r')
            
            embedding = get_embedding(chunk['text'])
            if embedding:
                writer.writerow([
                    chunk['id'],
                    chunk['text'],
                    chunk['word_count'],
                    chunk['pages'],
                    json.dumps(chunk['page_numbers']),
                    json.dumps(embedding)
                ])
    
    print(f"\n✓ Complete! Saved to {output_csv}")
    print(f"✓ Total chunks: {len(chunks)}")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    # Example usage
    pdf_file = input("Enter PDF filename: ").strip()
    
    if os.path.exists(pdf_file):
        output = f"book_db_with_pages_{pdf_file.replace('.pdf', '')}.csv"
        ingest_pdf_with_pages(pdf_file, output)
    else:
        print(f"File not found: {pdf_file}")
