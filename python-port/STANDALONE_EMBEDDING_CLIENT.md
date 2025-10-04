# 🚀 Standalone GitHub Copilot Embedding Client

A simple, direct interface to GitHub Copilot's embedding API without requiring a server. Perfect for integrating semantic search, similarity analysis, and document processing into your Python applications.

## 📦 Features

- **🔥 No Server Required** - Direct API access without running a web server
- **🔐 Automatic Authentication** - Handles GitHub OAuth and Copilot token management
- **📊 Batch Processing** - Efficiently process large amounts of text
- **🧮 Built-in Similarity** - Cosine similarity calculations included
- **🔍 Semantic Search** - Find similar documents easily
- **🆓 Free Usage** - Embeddings don't consume Copilot quota!

## 🏗️ Installation

The client is part of the Python port. Make sure you have the package installed:

```bash
cd python-port
pip install -e .
```

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from copilot_api.embedding_client import CopilotEmbeddingClient

async def main():
    client = CopilotEmbeddingClient()
    
    # Embed a single text
    result = await client.embed("Hello, world!")
    print(f"Embedding: {len(result.embeddings[0])} dimensions")
    
    # Embed multiple texts
    texts = ["Python is great", "I love coding", "AI is amazing"]
    result = await client.embed(texts)
    print(f"Got {len(result.embeddings)} embeddings")

asyncio.run(main())
```

### Convenience Functions

```python
import asyncio
from copilot_api.embedding_client import embed_text, embed_texts, find_similar

async def quick_example():
    # Single embedding
    embedding = await embed_text("Python programming")
    
    # Multiple embeddings
    embeddings = await embed_texts(["Hello", "World", "AI"])
    
    # Semantic search
    docs = ["Python guide", "JavaScript tutorial", "AI research"]
    similar = await find_similar("Python coding", docs, top_k=2)
    print(similar)  # [(text, similarity_score), ...]

asyncio.run(quick_example())
```

## 📚 Complete API Reference

### CopilotEmbeddingClient

#### Constructor
```python
client = CopilotEmbeddingClient(github_token=None)
```
- `github_token` (optional): Your GitHub token. If not provided, will use saved token or prompt for authentication.

#### Main Methods

##### `embed(texts, model, account_type)`
```python
result = await client.embed(
    texts="Hello world",  # str or List[str]
    model="text-embedding-3-small",  # optional
    account_type="individual"  # optional
)
```
**Returns:** `EmbeddingResult` with:
- `embeddings`: List of embedding vectors
- `model`: Model used
- `usage`: Token usage info
- `texts`: Original texts

##### `embed_batch(texts, model, batch_size, account_type)`
```python
result = await client.embed_batch(
    texts=large_text_list,
    batch_size=100,  # Process in chunks
    model="text-embedding-3-small"
)
```
**For processing large amounts of text efficiently.**

##### `find_most_similar(query, texts, model, top_k)`
```python
similar = await client.find_most_similar(
    query="Python programming",
    texts=["JS guide", "Python tutorial", "AI course"],
    top_k=2
)
# Returns: [("Python tutorial", 0.85), ("AI course", 0.32)]
```

##### `cosine_similarity(embedding1, embedding2)`
```python
similarity = client.cosine_similarity(vec1, vec2)
# Returns: float between -1 and 1
```

### Available Models

- `text-embedding-ada-002` - Legacy model (1536 dimensions)
- `text-embedding-3-small` - **Recommended** (1536 dimensions)
- `text-embedding-3-small-inference` - Inference optimized (1536 dimensions)

## 🎯 Usage Examples

### 1. Document Similarity Search

```python
import asyncio
from copilot_api.embedding_client import CopilotEmbeddingClient

async def document_search():
    client = CopilotEmbeddingClient()
    
    documents = [
        "Python web development with Django",
        "JavaScript frontend frameworks",
        "Machine learning with Python",
        "Database optimization techniques",
        "Cloud computing architectures"
    ]
    
    query = "Python programming for web apps"
    
    # Find most similar documents
    results = await client.find_most_similar(query, documents, top_k=3)
    
    for doc, similarity in results:
        print(f"{similarity:.3f}: {doc}")

asyncio.run(document_search())
```

### 2. Clustering Documents

```python
async def cluster_documents():
    client = CopilotEmbeddingClient()
    
    texts = [
        "Python programming",
        "Java development", 
        "Dog training tips",
        "Cat care guide",
        "JavaScript coding",
        "Pet nutrition"
    ]
    
    result = await client.embed(texts)
    
    # Calculate all pairwise similarities
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = client.cosine_similarity(
                result.embeddings[i], 
                result.embeddings[j]
            )
            print(f"{texts[i]} <-> {texts[j]}: {sim:.3f}")
```

### 3. Large Batch Processing

```python
async def process_large_dataset():
    client = CopilotEmbeddingClient()
    
    # Process thousands of documents
    large_dataset = [f"Document {i} content..." for i in range(1000)]
    
    result = await client.embed_batch(
        texts=large_dataset,
        batch_size=50,  # Process 50 at a time
        model="text-embedding-3-small"
    )
    
    print(f"Processed {len(result.embeddings)} documents")
    print(f"Total tokens: {result.usage['total_tokens']}")
```

## 🔐 Authentication

### First Time Setup
When you first use the client, it will prompt for GitHub authentication:

```
🔐 GitHub authentication required...
📱 Please go to: https://github.com/login/device
🔑 Enter code: ABCD-1234
⏳ Waiting for authentication...
✅ Authentication successful!
```

### Using Existing Token
```python
# Use existing token
client = CopilotEmbeddingClient(github_token="your_token_here")

# Or let it auto-detect from saved config
client = CopilotEmbeddingClient()  # Will use saved token
```

## 💰 Cost & Quotas

**🎉 Great news: Embeddings are FREE!**

- ✅ No quota consumption
- ✅ Unlimited usage
- ✅ No rate limits (beyond reasonable use)

Based on our testing, embedding requests don't count against your Copilot premium quota.

## 🚨 Error Handling

```python
from copilot_api.embedding_client import CopilotEmbeddingClient
from copilot_api.lib.error import HTTPError

async def robust_embedding():
    client = CopilotEmbeddingClient()
    
    try:
        result = await client.embed("Test text")
        return result
    except HTTPError as e:
        print(f"API Error: {e}")
        print(f"Status: {e.response.status_code}")
    except Exception as e:
        print(f"General Error: {e}")
```

## 🔧 Advanced Usage

### Custom Account Types
```python
# For business/enterprise accounts
result = await client.embed(
    texts=["Business document"],
    account_type="business"  # or "enterprise"
)
```

### Model Performance Comparison
```python
async def compare_models():
    client = CopilotEmbeddingClient()
    text = "Sample text for comparison"
    
    models = [
        "text-embedding-ada-002",
        "text-embedding-3-small",
        "text-embedding-3-small-inference"
    ]
    
    for model in models:
        result = await client.embed(text, model=model)
        print(f"{model}: {result.usage['total_tokens']} tokens")
```

## 📊 Performance Tips

1. **Batch Processing**: Use `embed_batch()` for large datasets
2. **Model Selection**: Use `text-embedding-3-small` for best performance
3. **Caching**: Save embeddings to avoid re-computation
4. **Token Efficiency**: Longer texts aren't always better - focus on key content

## 🤝 Integration Examples

### With RAG (Retrieval Augmented Generation)
```python
async def rag_example():
    client = CopilotEmbeddingClient()
    
    # Build knowledge base
    knowledge_base = ["doc1", "doc2", "doc3"]
    kb_embeddings = await client.embed(knowledge_base)
    
    # Query
    query = "user question"
    query_embedding = await client.embed(query)
    
    # Find relevant docs
    similarities = [
        client.cosine_similarity(query_embedding.embeddings[0], kb_emb)
        for kb_emb in kb_embeddings.embeddings
    ]
    
    # Use top results for context...
```

## 🎯 Summary

The standalone embedding client provides:
- **Simple API** for quick integration
- **No infrastructure** required
- **Free unlimited usage**
- **Production ready** performance
- **Built-in utilities** for common tasks

Perfect for building semantic search, document analysis, recommendation systems, and AI applications!