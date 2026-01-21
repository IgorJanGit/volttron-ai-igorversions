# VOLTTRON AI Chat Application

AI-powered chat interface for VOLTTRON platform management and agent creation.

## Features

- 🤖 **Multiple AI Providers**: OpenAI, Anthropic, Groq, custom APIs
- 🏗️ **VOLTTRON Control**: Start/stop platform, manage agents with natural language
- 🔨 **Agent Creator**: Guided wizard to scaffold custom agents (4 templates)
- 🧠 **Intelligent Discovery**: AI learns and executes vctl commands dynamically
- 📚 **Auto-Documentation**: Analyzes API docs and generates implementation guidance

## Quick Start

```bash
# Requires Python 3.9 or higher
# Clone and install
git clone https://github.com/VOLTTRON/volttron-ai.git
cd volttron-ai
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API key

# Run chat agent
python -m chat_app
```

Open http://127.0.0.1:8000 to access the chat interface

## Configuration

### Required Environment Variables

```bash
# For PNNL AI Depot
AI_WEBAPP_URL=https://ai-incubator-api.pnnl.gov
AI_API_KEY=your_api_key_here
AI_MODEL=claude-3-7-sonnet-20250219-v1-birthright

# For OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# For Anthropic  
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Command Line Options

```bash
python -m chat_app --model MODEL_NAME [--host HOST] [--port PORT] [--reload]
```

## Agent Creator

Create custom VOLTTRON agents through a guided 10-step wizard:

```
You: "Create a new agent"
```

### Features
- **4 Templates**: minimal, listener, driver, historian
- **URL Analysis**: Paste API docs, get implementation recommendations
- **Auto-scaffolding**: Complete project with tests, config, README
- **Extensive comments**: Every pattern explained

### Example with URL

```
You: "Create a new agent"
AI: "Step 1/10: Agent name?"
You: "weather-service"
...
AI: "Step 4/10: Documentation URL?"
You: "https://openweathermap.org/api"
AI: "🔍 Analyzing... Found: REST API, requires API key
     Recommendations included in code"
```

## VOLTTRON Commands

Control VOLTTRON with natural language:

| Command | Action |
|---------|--------|
| "Start VOLTTRON" | Starts platform |
| "Stop VOLTTRON" | Stops platform |
| "Check status" | Shows agent status |
| "Install agent X" | Installs agent |
| "Show logs" | Displays recent logs |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Chat interface |
| `/chat` | POST | Send message |
| `/health` | GET | Health check |
| `/ping` | GET | Test AI connection |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Quick tests
python3 tests/test_discovery_quick.py
```

## Troubleshooting

### VOLTTRON Not Found
```bash
# Check if installed
which volttron

# Install if needed
./install_volttron.sh
```

### Port Already in Use
```bash
# Kill existing process
lsof -i :8000
kill <PID>

# Or use different port
python -m chat_app --port 8001
```

### API Key Issues
- Verify API key in `.env`
- Check API endpoint URL
- Ensure key has proper permissions

## Project Structure

```
volttron-ai/
├── chat_app/
│   ├── ai_service.py          # AI integration
│   ├── agent_creator.py       # Agent wizard
│   ├── volttron_commands.py   # Platform control
│   └── templates/             # Agent templates
├── agents/                    # Generated agents
├── tests/                     # Test suite
└── requirements.txt
```

## Requirements

- Python 3.9+
- FastAPI, Pydantic-AI, Uvicorn
- Optional: VOLTTRON platform

## Documentation

- **Agent Templates**: See generated agent README files
- **Testing**: [tests/README_TESTS.md](tests/README_TESTS.md)
- **VOLTTRON**: https://volttron.readthedocs.io/

## Contributing

Contributions welcome! Submit Pull Requests to the VOLTTRON organization.

## License

Part of the VOLTTRON platform. See main VOLTTRON repository for licensing.
