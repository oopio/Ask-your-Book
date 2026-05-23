# Ask Your Book - Document Intelligence Platform

> AI-powered document Q&A system with PDF viewer, smart categorization, and advanced filtering

Transform your documents into an intelligent knowledge base. Upload PDFs, ask questions, and get AI-generated answers with source citations.

## ✨ Features

- **📄 PDF Processing** - Upload and process PDF, TXT, and EPUB documents
- **🤖 AI-Powered Q&A** - Ask questions and get accurate answers with source citations
- **📚 Multi-Book Library** - Manage multiple documents with smart categorization
- **🏷️ Auto-Categorization** - AI automatically tags and categorizes your documents
- **🔍 Advanced Filtering** - Filter by categories, tags, page count, and search
- **📖 PDF Viewer** - View your documents alongside the chat interface
- **💬 Chat Interface** - Natural conversation with your documents
- **🎯 Source Citations** - See exactly where answers come from

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create or edit `.env` file:

```bash
OPENAI_API_KEY=your-api-key-here
```

### 3. Launch Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### 4. Upload and Chat

1. Click "Select PDF file" in the sidebar
2. Choose a PDF document
3. Click "Process" and wait for completion
4. Start asking questions in the chat!

## 📁 Project Structure

```
ASK YOUR BOOK/
├── app.py                    # Main application (single entry point)
├── requirements.txt          # Python dependencies
├── .env                      # API keys (create this)
├── .gitignore               # Git ignore rules
│
├── core/                    # Core RAG functionality
│   ├── ingestion.py         # Document processing
│   ├── query.py             # RAG query system
│   ├── metadata.py          # Auto-categorization
│   └── filters.py           # Filtering engine
│
├── utils/                   # Utility functions
│
├── data/                    # Data storage
│   ├── books/               # Processed databases (*.csv, *.json)
│   └── pdfs/                # Original PDF files
│
├── scripts/                 # Utility scripts
│   ├── backfill_metadata.py    # Generate metadata for existing books
│   ├── example_queries.py      # Example usage
│   └── interactive_rag.py      # CLI query interface
│
├── docs/                    # Documentation
│   ├── SETUP.md            # Detailed setup guide
│   ├── USAGE.md            # Usage instructions
│   └── ARCHITECTURE.md     # Technical details
│
└── archive/                 # Archived files (old versions, tests)
```

## 💡 How It Works

### 1. Document Processing
- Extract text from PDF/TXT/EPUB
- Clean and normalize text
- Split into semantic chunks (500 words with overlap)
- Generate embeddings using OpenAI
- Store in CSV vector database

### 2. AI Categorization
- Analyze document content
- Generate categories (e.g., "Investment Strategy", "Fantasy Fiction")
- Extract relevant tags
- Create summary
- Save metadata for filtering

### 3. Question Answering
- Convert question to embedding
- Find most similar document chunks (cosine similarity)
- Retrieve top 5 relevant passages
- Generate answer using GPT-4o-mini with context
- Display answer with source citations

## 🎯 Example Questions

### For Fiction Books
- "Who are the main characters?"
- "Summarize chapter 3"
- "What happens at the end?"

### For Non-Fiction
- "What is the main argument?"
- "Explain the concept of [topic]"
- "What evidence supports [claim]?"

### For Technical Books
- "How does [algorithm] work?"
- "What are the key principles?"
- "Compare [A] and [B]"

## 🔧 Configuration

### Adjust Retrieval Settings

In the sidebar under "Settings":
- **Retrieval depth**: 1-10 passages (default: 5)
- **Show sources**: Toggle source passage display

### Customize Models

Edit `core/ingestion.py` and `core/query.py`:

```python
# Embedding model
EMBEDDING_MODEL = "text-embedding-3-small"  # or "text-embedding-3-large"

# Chat model
CHAT_MODEL = "gpt-4o-mini"  # or "gpt-4o", "gpt-4-turbo"
```

### Adjust Chunking

Edit `core/ingestion.py`:

```python
chunks = chunk_text_by_sentences(
    text,
    chunk_size=500,  # words per chunk
    overlap=50       # overlap between chunks
)
```

## 📊 Data Storage

### Vector Databases
- Location: `data/books/book_db_*.csv`
- Format: CSV with embeddings as JSON
- Contains: chunk ID, text, word count, embedding vector

### Metadata
- Location: `data/books/book_db_*_metadata.json`
- Contains: categories, tags, summary, stats
- Used for: filtering and organization

### Original PDFs
- Location: `data/pdfs/*.pdf`
- Preserved for PDF viewer functionality

## 💰 Cost Estimation

### Per Document Upload
- Small (50 pages): ~$0.002
- Medium (200 pages): ~$0.008
- Large (500 pages): ~$0.020

### Per Question
- ~$0.0001 per query

### Example: 200-page book + 50 questions
- Upload: $0.008
- Queries: $0.005
- **Total: ~$0.013** (about 1 cent!)

## 🛠️ Troubleshooting

### PDF Viewer Not Working

**Quick fix:**
```bash
pip install streamlit-pdf-viewer
```

**Diagnostic:**
```bash
python scripts/check_pdf_paths.py
```

### Import Errors
```bash
# If you see "ModuleNotFoundError"
pip install -r requirements.txt
```

### PDF Viewer Not Working
```bash
# Install optional PDF viewer
pip install streamlit-pdf-viewer
```

### Database Not Found
- Make sure you've processed at least one document
- Check `data/books/` directory for CSV files

### API Key Issues
- Verify `.env` file exists in project root
- Check API key is valid at platform.openai.com
- Ensure no extra spaces in `.env` file

**For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

## 📚 Documentation

- **[Setup Guide](docs/SETUP.md)** - Detailed installation instructions
- **[Usage Guide](docs/USAGE.md)** - How to use all features
- **[Architecture](docs/ARCHITECTURE.md)** - Technical implementation details

## 🔒 Security & Privacy

- Documents stored locally as CSV files
- No data sent to external servers (except OpenAI API for processing)
- API key stored in `.env` (never commit to git)
- `.gitignore` configured to protect sensitive files

## 🤝 Contributing

This is a learning/personal project. Feel free to fork and modify for your needs!

## 📄 License

Open source - use and modify as needed.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [OpenAI](https://openai.com/)
- RAG architecture inspired by modern AI best practices

---

**Need Help?** Check the [docs/](docs/) directory for detailed guides or review archived documentation in [archive/old_docs/](archive/old_docs/)
