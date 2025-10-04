# Copilot API (Python Port)

Turn GitHub Copilot into OpenAI/Anthropic API compatible server. Usable with Claude Code!

This is a Python port of the original TypeScript/Node.js [Copilot API](https://github.com/ericc-ch/copilot-api) project.

## 🚀 Features

- **OpenAI Compatible API** - Drop-in replacement for OpenAI API
- **Anthropic Compatible API** - Works with Claude Code and other Anthropic clients
- **GitHub Authentication** - Secure OAuth device flow
- **Auto-refreshing Tokens** - Automatic Copilot token renewal
- **Rate Limiting** - Built-in request throttling
- **Manual Approval** - Interactive request approval mode
- **Rich CLI** - Beautiful command-line interface
- **Streaming Support** - Real-time response streaming

## 📦 Installation

### From Source

```bash
git clone <repository-url>
cd python-port
pip install -e .
```

### From PyPI (when published)

```bash
pip install copilot-api
```

## 🔧 Usage

### 1. Authenticate with GitHub

```bash
copilot-api auth
```

This will open GitHub device flow authentication. Follow the instructions to authorize the application.

### 2. Start the Server

```bash
copilot-api start
```

The server will start on `http://localhost:4141` by default.

### 3. Use with Your Favorite Tools

#### OpenAI-Compatible Tools

```bash
export OPENAI_API_BASE="http://localhost:4141"
export OPENAI_API_KEY="dummy"
```

#### Claude Code

```bash
copilot-api start --claude-code
```

This will generate and copy the required environment variables to your clipboard.

## 🛠️ CLI Commands

### `copilot-api auth`

Authenticate with GitHub without starting the server.

**Options:**
- `--verbose, -v` - Enable verbose logging
- `--show-token` - Show GitHub token during authentication

### `copilot-api start`

Start the Copilot API server.

**Options:**
- `--port, -p` - Port to listen on (default: 4141)
- `--verbose, -v` - Enable verbose logging
- `--account-type, -a` - Account type (individual, business, enterprise)
- `--manual` - Enable manual request approval
- `--rate-limit, -r` - Rate limit in seconds between requests
- `--wait, -w` - Wait instead of error when rate limit is hit
- `--github-token, -g` - Provide GitHub token directly
- `--claude-code, -c` - Generate Claude Code configuration
- `--show-token` - Show tokens during operation

### `copilot-api check-usage`

Check GitHub Copilot usage statistics.

**Options:**
- `--verbose, -v` - Enable verbose logging
- `--show-token` - Show GitHub token

### `copilot-api debug`

Run diagnostic checks and show system information.

**Options:**
- `--verbose, -v` - Show detailed internal state
- `--show-token` - Show tokens (truncated)

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat/completions` | POST | OpenAI-compatible chat completions |
| `/v1/chat/completions` | POST | OpenAI-compatible chat completions (v1) |
| `/models` | GET | List available models |
| `/v1/models` | GET | List available models (v1) |
| `/embeddings` | POST | Create embeddings (placeholder) |
| `/v1/embeddings` | POST | Create embeddings (v1, placeholder) |
| `/v1/messages` | POST | Anthropic-compatible messages |
| `/v1/messages/count_tokens` | POST | Anthropic token counting |
| `/usage` | GET | Usage statistics |
| `/token` | GET | Token status information |

## 🐳 Docker Support

Build and run with Docker:

```bash
docker build -t copilot-api-python .
docker run -p 4141:4141 -v ~/.config/copilot-api:/root/.config/copilot-api copilot-api-python
```

## 🧪 Development

### Setup Development Environment

```bash
git clone <repository-url>
cd python-port
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
isort src/
```

### Type Checking

```bash
mypy src/
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