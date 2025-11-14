# 📦 Installation Guide

## Quick Start with uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package installer and resolver. It's the recommended way to install and manage this project.

### Install uv
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

## 🚀 Installation Options

### 1. Basic Installation
For users who just want to use the API:
```bash
uv pip install copilot-api
```

### 2. Development Installation
For contributors and developers:
```bash
# Clone the repository
git clone <repository-url>
cd python-port

# Install with development dependencies
uv pip install -e .[dev]
```

### 3. Testing Installation
For running tests:
```bash
uv pip install -e .[test]
```

### 4. Complete Installation
Everything included (development + testing):
```bash
uv pip install -e .[dev,test]
```

## 🎯 Installation Verification

After installation, verify everything works:

```bash
# Test CLI availability
copilot-api --help

# Test imports
python -c "
import copilot_api
from copilot_api.embedding_client import CopilotEmbeddingClient
print('✅ Installation successful!')
"

# Run tests (if test dependencies installed)
pytest
```

## 📋 Dependency Categories

### Core Runtime Dependencies
Required for basic functionality:

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.104.0 | Web framework for API server |
| `uvicorn[standard]` | >=0.24.0 | ASGI server for running FastAPI |
| `httpx` | >=0.25.0 | Async HTTP client for API calls |
| `pydantic` | >=2.0.0 | Data validation and serialization |
| `click` | >=8.0.0 | CLI framework for commands |
| `rich` | >=13.0.0 | Beautiful console output |
| `pyperclip` | >=1.8.0 | Clipboard operations for Claude Code |
| `tiktoken` | >=0.5.0 | Token counting for embeddings |
| `aiofiles` | >=23.0.0 | Async file operations |
| `python-multipart` | >=0.0.6 | Form data parsing for FastAPI |
| `requests` | >=2.31.0 | Synchronous HTTP client |

### Development Dependencies
For code development and maintenance:

| Package | Version | Purpose |
|---------|---------|---------|
| `black` | >=23.0.0 | Code formatting |
| `isort` | >=5.12.0 | Import sorting |
| `flake8` | >=6.0.0 | Code linting |
| `mypy` | >=1.0.0 | Static type checking |
| `types-requests` | >=2.31.0 | Type stubs for requests |

### Testing Dependencies
For running the test suite:

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=7.0.0 | Testing framework |
| `pytest-asyncio` | >=0.21.0 | Async test support |
| `pytest-cov` | >=4.0.0 | Coverage reporting |

## 🐍 Python Version Compatibility

- **Minimum**: Python 3.8
- **Recommended**: Python 3.11+
- **Tested**: 3.8, 3.9, 3.10, 3.11, 3.12

## 🔧 Development Setup

### 1. Clone and Setup
```bash
git clone <repository-url>
cd python-port

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
uv pip install -e .[dev,test]
```

### 2. Verify Development Setup
```bash
# Check code formatting
black --check src/
isort --check-only src/

# Run linting
flake8 src/

# Run type checking
mypy src/

# Run tests
pytest
```

### 3. Pre-commit Setup (Optional)
```bash
# Install pre-commit
uv pip install pre-commit

# Set up git hooks
pre-commit install
```

## 📦 Alternative Installation Methods

### Using pip
```bash
# Basic installation
pip install copilot-api

# Development installation
pip install -e .[dev,test]
```

### Using conda
```bash
# Create environment
conda create -n copilot-api python=3.11
conda activate copilot-api

# Install with pip (conda-forge doesn't have all packages)
pip install copilot-api
```

### Using Poetry
```bash
# If you prefer Poetry
poetry install --with dev,test
```

## 🐳 Docker Installation

### Build from Source
```bash
# Clone repository
git clone <repository-url>
cd python-port

# Build Docker image
docker build -t copilot-api-python .

# Run container
docker run -p 4141:4141 copilot-api-python
```

### Using Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  copilot-api:
    build: .
    ports:
      - "4141:4141"
    volumes:
      - ~/.config/copilot-api:/root/.config/copilot-api
```

```bash
docker-compose up
```

## ⚡ Performance Tips

### Fast Installation with uv
```bash
# Use uv for faster dependency resolution
uv pip install --resolution=highest copilot-api

# Cache dependencies for repeated installs
uv pip install --cache-dir ~/.cache/uv copilot-api
```

### Minimal Installation
For production deployments, install only runtime dependencies:
```bash
uv pip install copilot-api --no-deps
uv pip install fastapi uvicorn httpx pydantic click rich pyperclip tiktoken aiofiles python-multipart requests
```

## 🔍 Troubleshooting

### Common Issues

**1. ModuleNotFoundError: No module named 'copilot_api'**
```bash
# Make sure you're in the right directory and installed correctly
uv pip install -e .
```

**2. Command 'copilot-api' not found**
```bash
# Make sure the virtual environment is activated
source .venv/bin/activate
# Or reinstall
uv pip install -e .
```

**3. pytest: command not found**
```bash
# Install test dependencies
uv pip install .[test]
```

**4. ImportError: No module named 'pytest_asyncio'**
```bash
# Install async test support
uv pip install pytest-asyncio
```

### Dependency Conflicts
If you encounter dependency conflicts:
```bash
# Clear cache and reinstall
uv cache clean
uv pip install --force-reinstall copilot-api
```

### Version Issues
Check installed versions:
```bash
uv pip list | grep copilot
python -c "import copilot_api; print(copilot_api.__version__)"
```

## 📚 Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Project Repository](https://github.com/ericc-ch/copilot-api)

## 🆘 Getting Help

If you encounter issues:

1. **Check this documentation** for common solutions
2. **Search existing issues** on GitHub
3. **Create a new issue** with:
   - Python version (`python --version`)
   - uv version (`uv --version`)
   - Installation command used
   - Full error message
   - Operating system