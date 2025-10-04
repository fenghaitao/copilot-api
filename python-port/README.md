# Copilot API (Python Port)

Turn GitHub Copilot into OpenAI/Anthropic API compatible server. Usable with Claude Code!

This is a **complete Python port** of the original TypeScript/Node.js [Copilot API](https://github.com/ericc-ch/copilot-api) project, offering both **server mode** and **standalone client** functionality.

## ✨ Key Features

### 🌐 **Server Mode**
- **OpenAI Compatible API** - Drop-in replacement for OpenAI API
- **Anthropic Compatible API** - Works with Claude Code and other Anthropic clients  
- **FastAPI Backend** - Modern, fast web framework with automatic docs
- **Real-time Streaming** - Server-sent events for chat completions
- **CORS Support** - Ready for web applications

### 🚀 **Standalone Mode** ⭐ NEW!
- **No Server Required** - Direct API access without infrastructure
- **Embeddings Client** - Free unlimited semantic search and similarity
- **Batch Processing** - Efficient handling of large datasets
- **Built-in Utilities** - Cosine similarity, semantic search, clustering

### 🔐 **Authentication & Security**
- **GitHub OAuth** - Secure device flow authentication
- **Auto-refreshing Tokens** - Automatic Copilot token renewal
- **Rate Limiting** - Built-in request throttling with wait/error modes
- **Manual Approval** - Interactive request approval mode

### 🎨 **Developer Experience**
- **Rich CLI** - Beautiful command-line interface with colors and tables
- **Multiple Models** - Support for all GitHub Copilot embedding models
- **Comprehensive Testing** - 25+ test cases covering all functionality
- **Type Safety** - Full TypeScript-level type hints with Pydantic

## 📦 Installation

### 🚀 Quick Start (Recommended)

Using [uv](https://docs.astral.sh/uv/) for fastest installation:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Copilot API
uv pip install copilot-api
```

### 📋 Installation Options

```bash
# Basic installation
pip install copilot-api
uv pip install copilot-api

# Development installation
git clone <repository-url>
cd python-port
uv pip install -e .[dev,test]

# From PyPI (when published)
pip install copilot-api
```

**💡 See [INSTALLATION.md](./INSTALLATION.md) for detailed installation guide and troubleshooting.**

## 🔧 Usage

### 🌐 Server Mode

#### 1. Authenticate with GitHub

```bash
copilot-api auth
```

This will open GitHub device flow authentication. Follow the instructions to authorize the application.

#### 2. Start the Server

```bash
copilot-api start
```

The server will start on `http://localhost:4141` by default.

#### 3. Use with Your Favorite Tools

**OpenAI-Compatible Tools:**

```bash
export OPENAI_API_BASE="http://localhost:4141"
export OPENAI_API_KEY="dummy"
```

**Claude Code Integration:**

```bash
copilot-api start --claude-code
```

This will generate and copy the required environment variables to your clipboard.

### 🚀 Standalone Mode ⭐ NEW!

Use embeddings directly without running a server:

```python
# Quick start
from copilot_api.embedding_client import embed_text

embedding = await embed_text("Hello, world!")
print(f"Got {len(embedding)} dimensions")

# Advanced usage
from copilot_api.embedding_client import CopilotEmbeddingClient

client = CopilotEmbeddingClient()

# Batch embeddings
texts = ["Python programming", "Machine learning", "Web development"]
result = await client.embed(texts)

# Semantic search
similar = await client.find_most_similar(
    "Python coding", 
    ["Java development", "Python programming", "JavaScript"], 
    top_k=2
)
print(similar)  # [("Python programming", 0.85), ...]

# Batch processing
large_texts = [f"Document {i}" for i in range(1000)]
result = await client.embed_batch(large_texts, batch_size=50)
```

**💡 See [STANDALONE_EMBEDDING_CLIENT.md](./STANDALONE_EMBEDDING_CLIENT.md) for complete standalone usage guide.**

## 🛠️ CLI Commands

| Command | Description | Key Options |
|---------|-------------|-------------|
| `copilot-api auth` | GitHub authentication | `--verbose`, `--show-token` |
| `copilot-api start` | Start API server | `--port`, `--claude-code`, `--manual` |
| `copilot-api check-usage` | View usage statistics | `--verbose` |
| `copilot-api debug` | System diagnostics | `--verbose`, `--show-token` |

### Detailed Command Options

**`copilot-api start`** - Start the API server
- `--port, -p` - Port to listen on (default: 4141)
- `--account-type, -a` - Account type (individual, business, enterprise)  
- `--claude-code, -c` - Generate Claude Code integration command
- `--manual` - Enable manual request approval mode
- `--rate-limit, -r` - Rate limit seconds between requests
- `--wait, -w` - Wait instead of error when rate limited
- `--github-token, -g` - Provide GitHub token directly
- `--verbose, -v` - Enable verbose logging
- `--show-token` - Show tokens during operation

**Examples:**
```bash
# Basic server
copilot-api start

# With Claude Code integration
copilot-api start --claude-code

# Business account with rate limiting
copilot-api start --account-type business --rate-limit 2

# Manual approval mode
copilot-api start --manual --verbose
```

## 🔌 API Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/chat/completions` | POST | OpenAI-compatible chat completions | ✅ Streaming |
| `/v1/chat/completions` | POST | OpenAI chat completions (v1) | ✅ Streaming |
| `/embeddings` | POST | Create embeddings | ✅ **Free** |
| `/v1/embeddings` | POST | Create embeddings (v1) | ✅ **Free** |
| `/v1/messages` | POST | Anthropic-compatible messages | ✅ Streaming |
| `/v1/messages/count_tokens` | POST | Anthropic token counting | ✅ Utility |
| `/models` | GET | List available models | ✅ Metadata |
| `/v1/models` | GET | List available models (v1) | ✅ Metadata |
| `/usage` | GET | Usage statistics | ✅ Monitoring |
| `/token` | GET | Token status information | ✅ Diagnostics |

### 🆓 **Free Embeddings!**
Embeddings don't consume your Copilot quota - use them unlimited for:
- Semantic search and document similarity
- RAG (Retrieval Augmented Generation) systems  
- Text clustering and classification
- Content recommendation engines

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [INSTALLATION.md](./INSTALLATION.md) | Comprehensive installation guide with uv, pip, and troubleshooting |
| [DEPENDENCIES.md](./DEPENDENCIES.md) | Complete dependency reference and rationale |
| [STANDALONE_EMBEDDING_CLIENT.md](./STANDALONE_EMBEDDING_CLIENT.md) | Standalone client usage and examples |
| `verify_installation.py` | Installation verification script |

## 🧪 Testing

The Python port includes comprehensive test coverage:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=copilot_api

# Run specific test suites
pytest tests/test_basic.py                          # Server API tests
pytest tests/test_standalone_embedding_client.py   # Standalone client tests

# Verify installation
python verify_installation.py
```

**Test Coverage:**
- ✅ 25+ test cases covering all functionality
- ✅ Server API endpoints (6 tests)
- ✅ Standalone embedding client (19 tests)
- ✅ Real API integration tests
- ✅ Error handling and edge cases

## 🐳 Docker Support

Build and run with Docker:

```bash
docker build -t copilot-api-python .
docker run -p 4141:4141 -v ~/.config/copilot-api:/root/.config/copilot-api copilot-api-python
```

## 🌟 Why Choose the Python Port?

### ⚡ **Performance & Modern Stack**
- **FastAPI** - Automatic API docs, async-first, production-ready
- **Rich CLI** - Beautiful terminal output with progress bars and tables
- **Type Safety** - Full Pydantic validation and mypy support
- **Async Everything** - Non-blocking I/O for all operations

### 🚀 **Unique Features**
- **Standalone Client** - Use embeddings without any server infrastructure
- **Free Embeddings** - Unlimited semantic search and similarity analysis
- **Comprehensive Testing** - 25+ tests covering real API integration
- **Multiple Installation Methods** - uv, pip, Docker, development modes

### 🎯 **Developer Experience**
- **Modern Python** - Uses latest Python features and best practices
- **Excellent Documentation** - Multiple guides and examples
- **Easy Integration** - Drop-in replacement for OpenAI/Anthropic APIs
- **Production Ready** - Used in real-world applications

## 🧪 Development

### Quick Development Setup

```bash
git clone <repository-url>
cd python-port

# Using uv (recommended)
uv pip install -e .[dev,test]

# Using pip
pip install -e ".[dev,test]"
```

### Development Workflow

```bash
# Run tests
pytest                                    # All tests
pytest tests/test_basic.py               # Server tests
pytest tests/test_standalone_embedding_client.py  # Client tests

# Code quality
black src/ tests/                        # Format code
isort src/ tests/                        # Sort imports  
flake8 src/                              # Lint code
mypy src/                                # Type check

# Verify installation
python verify_installation.py           # Check all dependencies
```

## 📁 Configuration

Configuration files are stored in:
- Linux/macOS: `~/.config/copilot-api/`
- Windows: `%APPDATA%/copilot-api/`

Files:
- `github_token` - GitHub OAuth token
- `vscode_version` - Cached VS Code version

## 🔒 Security

- Tokens are stored locally in configuration directory
- GitHub OAuth uses secure device flow
- No tokens are transmitted to external services
- Rate limiting prevents abuse

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Original TypeScript implementation by [Erick Christian](https://github.com/ericc-ch)
- GitHub Copilot team for the excellent AI assistance
- FastAPI and Rich communities for excellent Python libraries