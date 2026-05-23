"""
Query system for book RAG
Ask questions about your ingested book
"""

import os
import csv
import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
BOOK_DATABASE = "book_vector_database.csv"


def get_embedding(text: str):
    """Get embedding vector for text"""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return None


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    magnitude1 = np.linalg.norm(vec1)
    magnitude2 = np.linalg.norm(vec2)
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    
    return dot_product / (magnitude1 * magnitude2)


def load_book_database(csv_file: str = BOOK_DATABASE):
    """Load book database from CSV"""
    if not os.path.exists(csv_file):
        print(f"❌ Database not found: {csv_file}")
        print("Please run book_ingestion.py first to ingest a book.")
        return []
    
    database = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            embedding = json.loads(row['embedding'])
            database.append({
                'id': row['id'],
                'text': row['text'],
                'word_count': row['word_count'],
                'embedding': embedding
            })
    
    return database


def search_book(query: str, database: list, top_k: int = 5):
    """Search for relevant chunks in the book"""
    print(f"\n🔍 Searching book for: '{query}'")
    
    # Get query embedding
    query_embedding = get_embedding(query)
    if not query_embedding:
        return []
    
    # Calculate similarities
    results = []
    for chunk in database:
        similarity = cosine_similarity(query_embedding, chunk['embedding'])
        results.append({
            'id': chunk['id'],
            'text': chunk['text'],
            'similarity': similarity
        })
    
    # Sort by similarity and get top_k
    results.sort(key=lambda x: x['similarity'], reverse=True)
    top_results = results[:top_k]
    
    print(f"✓ Found {len(top_results)} relevant passages\n")
    return top_results


def generate_answer(query: str, context_chunks: list, show_context: bool = True):
    """Generate answer using retrieved context"""
    
    # Build context
    context = "\n\n".join([
        f"[Passage {i+1}] {chunk['text'][:500]}..."
        if len(chunk['text']) > 500 else f"[Passage {i+1}] {chunk['text']}"
        for i, chunk in enumerate(context_chunks)
    ])
    
    if show_context:
        print("="*60)
        print("RETRIEVED CONTEXT FROM BOOK:")
        print("="*60)
        for i, chunk in enumerate(context_chunks, 1):
            preview = chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
            print(f"\n[Passage {i}] (Similarity: {chunk['similarity']:.3f})")
            print(f"{preview}")
        print("\n" + "="*60 + "\n")
    
    # Create prompt
    prompt = f"""You are a helpful assistant that answers questions based on a book.
Answer the question using ONLY the information provided in the passages below.
If the passages don't contain enough information, say so.
Provide a clear, comprehensive answer.

Passages from the book:
{context}

Question: {query}

Answer:"""
    
    # Generate answer
    print("🤖 Generating answer...\n")
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions about books based on provided passages."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error generating answer: {e}"


def query_book(question: str, top_k: int = 5, show_context: bool = True):
    """
    Complete pipeline to query the book
    
    Args:
        question: User's question
        top_k: Number of passages to retrieve
        show_context: Whether to show retrieved passages
    
    Returns:
        Generated answer
    """
    print("\n" + "="*60)
    print("BOOK RAG QUERY")
    print("="*60)
    
    # Load database
    database = load_book_database()
    if not database:
        return None
    
    print(f"✓ Loaded book database: {len(database)} chunks")
    
    # Search for relevant passages
    relevant_chunks = search_book(question, database, top_k)
    
    if not relevant_chunks:
        return "❌ No relevant passages found"
    
    # Generate answer
    answer = generate_answer(question, relevant_chunks, show_context)
    
    print("="*60)
    print("ANSWER:")
    print("="*60)
    print(answer)
    print("="*60 + "\n")
    
    return answer


def interactive_book_query():
    """Interactive mode for querying the book"""
    print("\n" + "="*60)
    print("INTERACTIVE BOOK QUERY SYSTEM")
    print("="*60)
    print("\nAsk questions about your book!")
    print("Type 'quit' or 'exit' to stop.")
    print("Type 'stats' to see book statistics.\n")
    
    # Check if database exists
    if not os.path.exists(BOOK_DATABASE):
        print(f"❌ Book database not found!")
        print("Please run 'python book_ingestion.py' first to ingest a book.\n")
        return
    
    # Load database once
    database = load_book_database()
    if not database:
        return
    
    print(f"✓ Loaded book: {len(database)} chunks")
    total_words = sum(int(chunk['word_count']) for chunk in database)
    print(f"✓ Total words: {total_words:,}")
    print(f"✓ Estimated pages: ~{total_words / 250:.0f}\n")
    
    while True:
        try:
            question = input("📚 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if question.lower() == 'stats':
                print(f"\n📊 Book Statistics:")
                print(f"   Chunks: {len(database)}")
                print(f"   Words: {total_words:,}")
                print(f"   Pages: ~{total_words / 250:.0f}")
                continue
            
            if not question:
                continue
            
            # Query the book
            query_book(question, top_k=5, show_context=True)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    interactive_book_query()
