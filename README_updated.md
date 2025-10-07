# VOLTTRON AI Chat Application

A modern chat application built with FastAPI and Pydantic-AI that supports multiple AI model providers including OpenAI, Anthropic, Groq, and custom APIs like PNNL AI Depot.

## Features

🤖 **Multiple AI Model Support**: Works with OpenAI, Anthropic, Groq, and custom API providers  
⚙️ **Configurable**: Set your preferred model via command line or environment variables  
🚀 **Fast**: Built with FastAPI for high performance  
🎨 **Modern UI**: Clean, responsive web interface  
🔧 **Developer Friendly**: Hot reload support for development  
🏗️ **VOLTTRON Integration**: Control VOLTTRON platform with natural language commands  
🌐 **Generic Path Detection**: Automatically finds VOLTTRON installations on any system  

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/VOLTTRON/volttron-ai.git
cd volttron-ai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your environment
Copy the example environment file and configure your API keys:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 4. (Optional) Install VOLTTRON
If you want to use VOLTTRON control features, install VOLTTRON:

**Quick Installation:**
```bash
./install_volttron.sh
```

**Manual Installation:**
```bash
# Clone VOLTTRON
git clone https://github.com/VOLTTRON/volttron.git
cd volttron

# Create virtual environment and install
python3 -m venv env
source env/bin/activate
pip install -e .

# Set up environment
export VOLTTRON_HOME=~/.volttron
```

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AI_MODEL` | The AI model to use | `claude-3-7-sonnet-20250219-v1-birthright` |
| `AI_WEBAPP_URL` | Custom AI API base URL | `https://ai-incubator-api.pnnl.gov` |
| `AI_API_KEY` | API key for custom AI service | `sk-...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `GROQ_API_KEY` | Groq API key | `gsk_...` |
| `HOST` | Server host | `127.0.0.1` |
| `PORT` | Server port | `8000` |
| `VOLTTRON_HOME` | VOLTTRON home directory | `~/.volttron` |

### Supported Models

**PNNL AI Depot:**
- `claude-3-7-sonnet-20250219-v1-birthright`
- And other models available at https://ai-incubator-depot.pnnl.gov/#available-models

**OpenAI:**
- `openai:gpt-3.5-turbo`
- `openai:gpt-4`
- `openai:gpt-4-turbo`

**Anthropic:**
- `anthropic:claude-3-haiku-20240307`
- `anthropic:claude-3-sonnet-20240229`
- `anthropic:claude-3-opus-20240229`

**Groq:**
- `groq:mixtral-8x7b-32768`
- `groq:llama2-70b-4096`

## Usage

### Running the Application

**Method 1: Using environment variables**
```bash
# Set model in .env file
AI_MODEL=claude-3-7-sonnet-20250219-v1-birthright

# Run the application
python -m chat_app
```

**Method 2: Using command line arguments**
```bash
# With PNNL AI Depot
python -m chat_app --model claude-3-7-sonnet-20250219-v1-birthright

# With OpenAI
python -m chat_app --model openai:gpt-3.5-turbo

# Custom host and port
python -m chat_app --model openai:gpt-3.5-turbo --host 0.0.0.0 --port 3000

# Development mode with auto-reload
python -m chat_app --model openai:gpt-3.5-turbo --reload
```

### Accessing the Application

1. Open your web browser
2. Navigate to `http://127.0.0.1:8000` (or your configured host/port)
3. Start chatting with your AI assistant!

### VOLTTRON Commands

The AI assistant can control VOLTTRON platform with natural language:

- **"Start VOLTTRON"** or **"Turn on the platform"** → Starts VOLTTRON
- **"Stop VOLTTRON"** or **"Shutdown the platform"** → Stops VOLTTRON  
- **"Check VOLTTRON status"** or **"How is VOLTTRON doing?"** → Shows status
- **"Show VOLTTRON logs"** or **"What happened?"** → Displays recent logs

**Automatic VOLTTRON Detection:**
The application automatically detects VOLTTRON installations in common locations:
- Virtual environments (`$VIRTUAL_ENV/bin/volttron`)
- User home directories (`~/volttron/bin/volttron`, `~/VOLTTRON/bin/volttron`)
- System locations (`/opt/volttron/bin/volttron`, `/usr/local/bin/volttron`)
- PATH environment variable

If VOLTTRON is not found, the assistant provides installation instructions.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Chat interface (web UI) |
| `/chat` | POST | Send a message and get AI response |
| `/health` | GET | Health check endpoint |
| `/models` | GET | Get information about available models |
| `/volttron/start` | POST | Start VOLTTRON platform |
| `/volttron/stop` | POST | Stop VOLTTRON platform |

### Example API Usage

```bash
# Send a chat message
curl -X POST "http://127.0.0.1:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, how are you?"}'

# Check health
curl "http://127.0.0.1:8000/health"

# Get model information
curl "http://127.0.0.1:8000/models"

# Start VOLTTRON
curl -X POST "http://127.0.0.1:8000/volttron/start"
```

## Development

### Running in Development Mode
```bash
python -m chat_app --model claude-3-7-sonnet-20250219-v1-birthright --reload
```

This enables auto-reload, so the server will restart automatically when you make code changes.

### Testing

**Test API functionality:**
```bash
python test_api.py
```

**Diagnose VOLTTRON installation:**
```bash
python volttron_diagnostic.py
```

### Project Structure
```
volttron-ai/
├── chat_app/
│   ├── __init__.py
│   ├── __main__.py              # Entry point and CLI
│   ├── app.py                   # FastAPI application
│   ├── ai_service.py            # AI model integration
│   ├── volttron_commands.py     # VOLTTRON platform control
│   └── templates/
│       └── chat.html            # Web interface
├── requirements.txt             # Python dependencies
├── .env.example                # Environment template
├── install_volttron.sh         # VOLTTRON installation script
├── test_api.py                 # API testing script
├── volttron_diagnostic.py      # VOLTTRON diagnostic tool
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

### Command Line Options
```bash
python -m chat_app --help
```

Options:
- `--model`: Specify the AI model to use
- `--host`: Host to bind the server to (default: 127.0.0.1)
- `--port`: Port to bind the server to (default: 8000)
- `--reload`: Enable auto-reload for development

## Troubleshooting

### VOLTTRON Not Found
If you get "VOLTTRON not found" errors:

1. **Check if VOLTTRON is installed:**
   ```bash
   python volttron_diagnostic.py
   ```

2. **Install VOLTTRON:**
   ```bash
   ./install_volttron.sh
   ```

3. **Activate VOLTTRON environment:**
   ```bash
   source ~/volttron/env/bin/activate
   export VOLTTRON_HOME=~/.volttron
   ```

### API Key Issues
If you get 401 authentication errors:

1. **Check your API key is correct in `.env`**
2. **Verify the API endpoint URL**
3. **For PNNL AI Depot, ensure you're using:**
   - URL: `https://ai-incubator-api.pnnl.gov`
   - Valid API key from PNNL

### Port Already in Use
If you get "address already in use" errors:
```bash
# Find and kill the process using port 8000
lsof -i :8000
kill <PID>

# Or use a different port
python -m chat_app --port 8001
```

## Requirements

- Python 3.8+
- FastAPI
- Pydantic-AI
- Uvicorn
- Python-dotenv

## License

This project is part of the VOLTTRON platform. Please refer to the main VOLTTRON repository for licensing information.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- Use the GitHub issue tracker
- Refer to the main VOLTTRON documentation
- Visit https://volttron.readthedocs.io/

---

**Note:** This application provides a modern chat interface for VOLTTRON platform management using AI assistants. The generic path detection ensures it works on any system with VOLTTRON installed.