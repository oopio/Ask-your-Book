"""
Metadata Manager for Document Auto-Categorization
Handles metadata generation, storage, and retrieval using LLM analysis
"""

import os
import json
import csv
from typing import List, Dict, Optional
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Configuration
CHAT_MODEL = "gpt-4o-mini"
METADATA_VERSION = "1.0"


def generate_metadata(
    document_text: str,
    document_name: str,
    page_count: int,
    word_count: int,
    csv_path: str,
    file_size_mb: float = 0.0
) -> dict:
    """
    Generate metadata using LLM analysis
    
    Args:
        document_text: First 2000 words of document
        document_name: Name of the document
        page_count: Number of pages
        word_count: Total word count
        csv_path: Path to CSV database file
        file_size_mb: File size in MB
    
    Returns:
        Dictionary with categories, tags, summary, and metadata
    """
    print(f"\n🤖 Generating metadata for: {document_name}")
    
    # Prepare LLM prompt
    prompt = f"""Analyze this document and provide structured metadata.

Document: {document_name}
Content (first 2000 words):
{document_text}

Provide:
1. Categories (1-3): Broad classifications (e.g., "Investment Strategy", "Fantasy Fiction", "Health & Fitness")
2. Tags (5-10): Specific keywords (e.g., "stocks", "magic", "adventure", "bodybuilding")
3. Summary (2-3 sentences): Brief overview of the document's main topics

Return ONLY valid JSON in this exact format:
{{
  "categories": ["category1", "category2"],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "summary": "Brief summary of the document..."
}}"""
    
    try:
        # Call LLM
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a document analysis expert. Analyze documents and provide accurate categories, tags, and summaries in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse response
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        llm_metadata = json.loads(content)
        
        # Validate and clean
        categories = llm_metadata.get("categories", [])[:3]  # Max 3
        tags = llm_metadata.get("tags", [])[:10]  # Max 10
        summary = llm_metadata.get("summary", "")
        
        print(f"✓ Generated {len(categories)} categories and {len(tags)} tags")
        
    except Exception as e:
        print(f"⚠ LLM analysis failed: {e}")
        print("Using fallback metadata...")
        
        # Fallback metadata
        categories = ["Uncategorized"]
        tags = ["document", "pdf"]
        summary = "Metadata generation unavailable. Please regenerate."
    
    # Build complete metadata
    metadata = {
        "document_name": document_name,
        "file_path": csv_path,
        "categories": categories,
        "tags": tags,
        "summary": summary,
        "upload_date": datetime.now().strftime("%Y-%m-%d"),
        "processing_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "page_count": page_count,
        "word_count": word_count,
        "file_size_mb": round(file_size_mb, 2),
        "version": METADATA_VERSION
    }
    
    return metadata


def save_metadata(metadata: dict, csv_path: str):
    """
    Save metadata to JSON file
    
    Args:
        metadata: Metadata dictionary
        csv_path: Path to CSV database file (used to derive JSON path)
    """
    # Derive JSON path from CSV path
    json_path = csv_path.replace('.csv', '_metadata.json')
    
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Metadata saved: {json_path}")
        return json_path
        
    except Exception as e:
        print(f"❌ Error saving metadata: {e}")
        return None


def load_metadata(csv_path: str) -> Optional[dict]:
    """
    Load metadata from JSON file
    
    Args:
        csv_path: Path to CSV database file (used to derive JSON path)
    
    Returns:
        Metadata dictionary or None if not found
    """
    json_path = csv_path.replace('.csv', '_metadata.json')
    
    if not os.path.exists(json_path):
        return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata
        
    except Exception as e:
        print(f"❌ Error loading metadata: {e}")
        return None


def get_all_categories() -> List[str]:
    """
    Get unique categories from all documents
    
    Returns:
        Sorted list of unique categories
    """
    categories = set()
    
    # Find all metadata files in data/books
    books_dir = "data/books"
    if not os.path.exists(books_dir):
        return []
    
    for file in os.listdir(books_dir):
        if file.startswith('book_db_') and file.endswith('_metadata.json'):
            try:
                file_path = os.path.join(books_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    categories.update(metadata.get('categories', []))
            except Exception:
                continue
    
    return sorted(list(categories))


def get_all_tags() -> List[str]:
    """
    Get unique tags from all documents
    
    Returns:
        Sorted list of unique tags
    """
    tags = set()
    
    # Find all metadata files in data/books
    books_dir = "data/books"
    if not os.path.exists(books_dir):
        return []
    
    for file in os.listdir(books_dir):
        if file.startswith('book_db_') and file.endswith('_metadata.json'):
            try:
                file_path = os.path.join(books_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    tags.update(metadata.get('tags', []))
            except Exception:
                continue
    
    return sorted(list(tags))


def load_all_metadata() -> List[dict]:
    """
    Load metadata from all documents
    
    Returns:
        List of metadata dictionaries
    """
    all_metadata = []
    
    # Find all metadata files in data/books
    books_dir = "data/books"
    if not os.path.exists(books_dir):
        return []
    
    for file in os.listdir(books_dir):
        if file.startswith('book_db_') and file.endswith('_metadata.json'):
            try:
                file_path = os.path.join(books_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    all_metadata.append(metadata)
            except Exception:
                continue
    
    return all_metadata


def extract_first_n_words(text: str, n: int = 2000) -> str:
    """
    Extract first N words from text
    
    Args:
        text: Full text
        n: Number of words to extract
    
    Returns:
        First N words
    """
    words = text.split()
    return ' '.join(words[:n])


def generate_metadata_from_csv(csv_path: str) -> Optional[dict]:
    """
    Generate metadata from existing CSV database
    Used for backfilling existing documents
    
    Args:
        csv_path: Path to CSV database file
    
    Returns:
        Generated metadata dictionary or None
    """
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return None
    
    try:
        # Load CSV to get text and stats
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            chunks = list(reader)
        
        if not chunks:
            print(f"❌ CSV file is empty: {csv_path}")
            return None
        
        # Calculate stats
        total_words = sum(int(chunk['word_count']) for chunk in chunks)
        page_count = total_words // 250  # Estimate
        
        # Extract first 2000 words from chunks
        all_text = ' '.join(chunk['text'] for chunk in chunks)
        sample_text = extract_first_n_words(all_text, 2000)
        
        # Extract document name
        document_name = csv_path.replace('book_db_', '').replace('.csv', '').replace('_', ' ')
        
        # Get file size
        file_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
        
        # Generate metadata
        metadata = generate_metadata(
            document_text=sample_text,
            document_name=document_name,
            page_count=page_count,
            word_count=total_words,
            csv_path=csv_path,
            file_size_mb=file_size_mb
        )
        
        return metadata
        
    except Exception as e:
        print(f"❌ Error generating metadata from CSV: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "="*60)
    print("METADATA MANAGER TEST")
    print("="*60)
    
    # Test with existing book
    test_csv = "book_db_Harry_Potter_and_the_sorcerers_stone.csv"
    
    if os.path.exists(test_csv):
        print(f"\nTesting with: {test_csv}")
        
        # Generate metadata
        metadata = generate_metadata_from_csv(test_csv)
        
        if metadata:
            print("\nGenerated Metadata:")
            print(json.dumps(metadata, indent=2))
            
            # Save metadata
            save_metadata(metadata, test_csv)
            
            # Load metadata
            loaded = load_metadata(test_csv)
            print("\nLoaded Metadata:")
            print(json.dumps(loaded, indent=2))
    else:
        print(f"\n❌ Test file not found: {test_csv}")
    
    print("\n" + "="*60)
