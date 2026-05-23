"""
Filter Engine for Document Filtering
Applies various filters to document metadata
"""

from typing import List, Dict, Optional
from datetime import datetime


def apply_filters(documents: List[dict], filters: dict) -> List[dict]:
    """
    Apply all filters to document list
    
    Args:
        documents: List of document metadata dictionaries
        filters: Dictionary with filter criteria:
            - search: str (search query)
            - categories: List[str] (selected categories)
            - tags: List[str] (selected tags)
            - date_start: str (start date YYYY-MM-DD)
            - date_end: str (end date YYYY-MM-DD)
            - page_min: int (minimum pages)
            - page_max: int (maximum pages)
    
    Returns:
        Filtered list of documents
    """
    filtered = documents.copy()
    
    # Apply search filter
    if filters.get('search'):
        filtered = filter_by_search(filtered, filters['search'])
    
    # Apply category filter
    if filters.get('categories'):
        filtered = filter_by_category(filtered, filters['categories'])
    
    # Apply tags filter
    if filters.get('tags'):
        filtered = filter_by_tags(filtered, filters['tags'])
    
    # Apply date range filter
    if filters.get('date_start') or filters.get('date_end'):
        filtered = filter_by_date_range(
            filtered,
            filters.get('date_start'),
            filters.get('date_end')
        )
    
    # Apply page count filter
    if filters.get('page_min') is not None or filters.get('page_max') is not None:
        filtered = filter_by_page_count(
            filtered,
            filters.get('page_min', 0),
            filters.get('page_max', 999999)
        )
    
    return filtered


def filter_by_category(documents: List[dict], categories: List[str]) -> List[dict]:
    """
    Filter documents by categories (OR logic)
    Document matches if it has ANY of the selected categories
    
    Args:
        documents: List of document metadata
        categories: List of category names to filter by
    
    Returns:
        Filtered list of documents
    """
    if not categories:
        return documents
    
    filtered = []
    for doc in documents:
        doc_categories = doc.get('categories', [])
        # Check if any selected category is in document's categories
        if any(cat in doc_categories for cat in categories):
            filtered.append(doc)
    
    return filtered


def filter_by_tags(documents: List[dict], tags: List[str]) -> List[dict]:
    """
    Filter documents by tags (OR logic)
    Document matches if it has ANY of the selected tags
    
    Args:
        documents: List of document metadata
        tags: List of tag names to filter by
    
    Returns:
        Filtered list of documents
    """
    if not tags:
        return documents
    
    filtered = []
    for doc in documents:
        doc_tags = doc.get('tags', [])
        # Check if any selected tag is in document's tags
        if any(tag in doc_tags for tag in tags):
            filtered.append(doc)
    
    return filtered


def filter_by_search(documents: List[dict], query: str) -> List[dict]:
    """
    Filter documents by search query in document name
    Case-insensitive search
    
    Args:
        documents: List of document metadata
        query: Search query string
    
    Returns:
        Filtered list of documents
    """
    if not query:
        return documents
    
    query_lower = query.lower()
    filtered = []
    
    for doc in documents:
        doc_name = doc.get('document_name', '').lower()
        # Check if query is in document name
        if query_lower in doc_name:
            filtered.append(doc)
    
    return filtered


def filter_by_date_range(
    documents: List[dict],
    start_date: Optional[str],
    end_date: Optional[str]
) -> List[dict]:
    """
    Filter documents by upload date range
    
    Args:
        documents: List of document metadata
        start_date: Start date (YYYY-MM-DD) or None
        end_date: End date (YYYY-MM-DD) or None
    
    Returns:
        Filtered list of documents
    """
    if not start_date and not end_date:
        return documents
    
    filtered = []
    
    for doc in documents:
        doc_date_str = doc.get('upload_date', '')
        
        if not doc_date_str:
            continue
        
        try:
            doc_date = datetime.strptime(doc_date_str, '%Y-%m-%d')
            
            # Check start date
            if start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                if doc_date < start:
                    continue
            
            # Check end date
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                if doc_date > end:
                    continue
            
            filtered.append(doc)
            
        except ValueError:
            # Skip documents with invalid dates
            continue
    
    return filtered


def filter_by_page_count(
    documents: List[dict],
    min_pages: int,
    max_pages: int
) -> List[dict]:
    """
    Filter documents by page count range
    
    Args:
        documents: List of document metadata
        min_pages: Minimum page count
        max_pages: Maximum page count
    
    Returns:
        Filtered list of documents
    """
    filtered = []
    
    for doc in documents:
        page_count = doc.get('page_count', 0)
        
        if min_pages <= page_count <= max_pages:
            filtered.append(doc)
    
    return filtered


def get_filter_summary(filters: dict) -> str:
    """
    Generate a human-readable summary of active filters
    
    Args:
        filters: Dictionary with filter criteria
    
    Returns:
        Summary string
    """
    active_filters = []
    
    if filters.get('search'):
        active_filters.append(f"Search: '{filters['search']}'")
    
    if filters.get('categories'):
        active_filters.append(f"Categories: {len(filters['categories'])}")
    
    if filters.get('tags'):
        active_filters.append(f"Tags: {len(filters['tags'])}")
    
    if filters.get('date_start') or filters.get('date_end'):
        active_filters.append("Date range")
    
    if filters.get('page_min', 0) > 0 or filters.get('page_max', 999999) < 999999:
        active_filters.append("Page count")
    
    if not active_filters:
        return "No filters active"
    
    return " | ".join(active_filters)


def is_filter_active(filters: dict) -> bool:
    """
    Check if any filters are currently active
    
    Args:
        filters: Dictionary with filter criteria
    
    Returns:
        True if any filter is active, False otherwise
    """
    return (
        bool(filters.get('search')) or
        bool(filters.get('categories')) or
        bool(filters.get('tags')) or
        bool(filters.get('date_start')) or
        bool(filters.get('date_end')) or
        (filters.get('page_min', 0) > 0) or
        (filters.get('page_max', 999999) < 999999)
    )


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FILTER ENGINE TEST")
    print("="*60)
    
    # Sample documents
    test_docs = [
        {
            "document_name": "Harry Potter and the Sorcerer's Stone",
            "categories": ["Fantasy Fiction", "Young Adult"],
            "tags": ["magic", "wizards", "adventure", "friendship"],
            "upload_date": "2025-05-01",
            "page_count": 339
        },
        {
            "document_name": "The Intelligent Investor",
            "categories": ["Investment Strategy", "Financial Education"],
            "tags": ["stocks", "bonds", "value investing", "finance"],
            "upload_date": "2025-05-02",
            "page_count": 932
        },
        {
            "document_name": "Bodybuilding Encyclopedia",
            "categories": ["Health & Fitness", "Sports"],
            "tags": ["bodybuilding", "exercise", "nutrition", "training"],
            "upload_date": "2025-04-30",
            "page_count": 836
        }
    ]
    
    print(f"\nTotal documents: {len(test_docs)}")
    
    # Test 1: Filter by category
    print("\n--- Test 1: Filter by category ---")
    filters = {'categories': ['Fantasy Fiction']}
    result = apply_filters(test_docs, filters)
    print(f"Filter: {filters}")
    print(f"Results: {len(result)} documents")
    for doc in result:
        print(f"  - {doc['document_name']}")
    
    # Test 2: Filter by tags
    print("\n--- Test 2: Filter by tags ---")
    filters = {'tags': ['stocks', 'magic']}
    result = apply_filters(test_docs, filters)
    print(f"Filter: {filters}")
    print(f"Results: {len(result)} documents")
    for doc in result:
        print(f"  - {doc['document_name']}")
    
    # Test 3: Filter by search
    print("\n--- Test 3: Filter by search ---")
    filters = {'search': 'invest'}
    result = apply_filters(test_docs, filters)
    print(f"Filter: {filters}")
    print(f"Results: {len(result)} documents")
    for doc in result:
        print(f"  - {doc['document_name']}")
    
    # Test 4: Filter by page count
    print("\n--- Test 4: Filter by page count ---")
    filters = {'page_min': 500, 'page_max': 1000}
    result = apply_filters(test_docs, filters)
    print(f"Filter: {filters}")
    print(f"Results: {len(result)} documents")
    for doc in result:
        print(f"  - {doc['document_name']} ({doc['page_count']} pages)")
    
    # Test 5: Multiple filters
    print("\n--- Test 5: Multiple filters ---")
    filters = {
        'categories': ['Health & Fitness', 'Investment Strategy'],
        'page_min': 800
    }
    result = apply_filters(test_docs, filters)
    print(f"Filter: {filters}")
    print(f"Results: {len(result)} documents")
    for doc in result:
        print(f"  - {doc['document_name']}")
    
    print("\n" + "="*60)
