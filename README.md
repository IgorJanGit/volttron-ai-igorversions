# VOLTTRON AI Chat Application

A modern chat application built with FastAPI and Pydantic-AI that supports multiple AI model providers including OpenAI, Anthropic, and Groq.

## Features

- 🤖 **Multiple AI Model Support**: Works with OpenAI, Anthropic, Groq, and other providers
- ⚙️ **Configurable**: Set your preferred model via command line or environment variables
- 🚀 **Fast**: Built with FastAPI for high performance
- 🎨 **Modern UI**: Clean, responsive web interface
- 🔧 **Developer Friendly**: Hot reload support for development

## Installation

1. **Clone the repository**:
```bash
git clone https://github.com/VOLTTRON/volttron-ai.git
cd volttron-ai
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up your environment**:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# For OpenAI:
# OPENAI_API_KEY=your_openai_api_key_here

# For Anthropic:
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# For Groq:
# GROQ_API_KEY=your_groq_api_key_here
```

## Usage

### Running the Application

#### Method 1: Using command line arguments
```bash
# With OpenAI GPT-3.5 Turbo
python -m chat_app --model openai:gpt-3.5-turbo

# With OpenAI GPT-4
python -m chat_app --model openai:gpt-4

# With Anthropic Claude
python -m chat_app --model anthropic:claude-3-haiku-20240307

# With Groq Mixtral
python -m chat_app --model groq:mixtral-8x7b-32768

# Custom host and port
python -m chat_app --model openai:gpt-3.5-turbo --host 0.0.0.0 --port 3000

# Development mode with auto-reload
python -m chat_app --model openai:gpt-3.5-turbo --reload
```

#### Method 2: Using environment variables
Set the model in your `.env` file:
```bash
AI_MODEL=openai:gpt-3.5-turbo
HOST=127.0.0.1
PORT=8000
```

Then run:
```bash
python -m chat_app
```

### Accessing the Application

1. Open your web browser
2. Navigate to `http://127.0.0.1:8000` (or the host/port you specified)
3. Start chatting with your AI assistant!

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AI_MODEL` | The AI model to use | `openai:gpt-3.5-turbo` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `GROQ_API_KEY` | Groq API key | `gsk_...` |
| `HOST` | Server host | `127.0.0.1` |
| `PORT` | Server port | `8000` |

### Supported Models

#### OpenAI
- `openai:gpt-3.5-turbo`
- `openai:gpt-4`
- `openai:gpt-4-turbo`

#### Anthropic
- `anthropic:claude-3-haiku-20240307`
- `anthropic:claude-3-sonnet-20240229`
- `anthropic:claude-3-opus-20240229`

#### Groq
- `groq:mixtral-8x7b-32768`
- `groq:llama2-70b-4096`

### Command Line Options

```bash
python -m chat_app --help
```

Options:
- `--model`: Specify the AI model to use
- `--host`: Host to bind the server to (default: 127.0.0.1)
- `--port`: Port to bind the server to (default: 8000)
- `--reload`: Enable auto-reload for development

## API Endpoints

The application provides several REST API endpoints:

- `GET /`: Chat interface (web UI)
- `POST /chat`: Send a message and get AI response
- `GET /health`: Health check endpoint
- `GET /models`: Get information about available models

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
```

## Development

### Running in Development Mode

```bash
python -m chat_app --model openai:gpt-3.5-turbo --reload
```

This enables auto-reload, so the server will restart automatically when you make code changes.

### Project Structure

```
volttron-ai/
├── chat_app/
│   ├── __init__.py
│   ├── __main__.py          # Entry point and CLI
│   ├── app.py               # FastAPI application
│   ├── ai_service.py        # Pydantic-AI integration
│   └── templates/
│       └── chat.html        # Web interface
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
└── README.md               # This file
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

For issues and questions, please use the GitHub issue tracker or refer to the main VOLTTRON documentation.