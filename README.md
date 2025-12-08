# VOLTTRON AI Chat Application

A modern chat application built with FastAPI and Pydantic-AI that supports multiple AI model providers including OpenAI, Anthropic, Groq, and custom APIs like PNNL AI Depot.

## Features

- 🤖 **Multiple AI Model Support**: Works with OpenAI, Anthropic, Groq, and custom API providers
- ⚙️ **Configurable**: Set your preferred model via command line or environment variables
- 🚀 **Fast**: Built with FastAPI for high performance
- 🎨 **Modern UI**: Clean, responsive web interface
- 🔧 **Developer Friendly**: Hot reload support for development
- 🏗️ **VOLTTRON Integration**: Control VOLTTRON platform with natural language commands
- 🌐 **Generic Path Detection**: Automatically finds VOLTTRON installations on any system
- 🧠 **Intelligent Command Discovery**: AI can learn and execute vctl commands dynamically
- 🔨 **Agent Creator**: Guided wizard to scaffold custom VOLTTRON agents with 4 template types
- 📚 **Extensive Comments**: Generated agents include detailed explanations of VOLTTRON patterns

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

3. **Install VOLTTRON dependency (required)**:
```bash
pip install zope.event
```

4. **Set up your environment**:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# For PNNL AI Depot:
# AI_WEBAPP_URL=https://ai-incubator-api.pnnl.gov
# AI_API_KEY=your_api_key_here
# AI_MODEL=claude-3-7-sonnet-20250219-v1-birthright

# For OpenAI:
# OPENAI_API_KEY=your_openai_api_key_here

# For Anthropic:
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# For Groq:
# GROQ_API_KEY=your_groq_api_key_here
```

5. **(Optional) Install VOLTTRON**:

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

## Usage

### Running the Application

#### Method 1: Using environment variables (Recommended)
```bash
# Set model in .env file
AI_MODEL=claude-3-7-sonnet-20250219-v1-birthright
AI_WEBAPP_URL=https://ai-incubator-api.pnnl.gov
AI_API_KEY=your_api_key_here

# Run the application
python -m chat_app
```

#### Method 2: Using command line arguments
```bash
# With PNNL AI Depot
python -m chat_app --model claude-3-7-sonnet-20250219-v1-birthright

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

### Accessing the Application

1. Open your web browser
2. Navigate to `http://127.0.0.1:8000` (or the host/port you specified)
3. Start chatting with your AI assistant!

### VOLTTRON Commands

The AI assistant can control VOLTTRON platform with natural language:

- **"Start VOLTTRON"** or **"Turn on the platform"** → Starts VOLTTRON
- **"Stop VOLTTRON"** or **"Shutdown the platform"** → Stops VOLTTRON
- **"Check VOLTTRON status"** or **"Is VOLTTRON running?"** → Shows status
- **"Show VOLTTRON logs"** or **"What happened?"** → Displays recent logs
- **"Check agent health"** → AI discovers and runs `vctl health`
- **"List agent tags"** → AI discovers and runs `vctl tag`
- **"Show peer list"** → AI discovers and runs `vctl peerlist`

**Automatic VOLTTRON Detection:**
The application automatically detects VOLTTRON installations in common locations:
- Virtual environments (`$VIRTUAL_ENV/bin/volttron`)
- User home directories (`~/volttron/bin/volttron`, `~/VOLTTRON/bin/volttron`)
- System locations (`/opt/volttron/bin/volttron`, `/usr/local/bin/volttron`)
- PATH environment variable

If VOLTTRON is not found, the assistant provides installation instructions.

### Agent Creator

The AI assistant includes a guided wizard for creating custom VOLTTRON agents. This feature scaffolds complete agent projects with extensive comments explaining VOLTTRON patterns.

**How to Use:**

Simply ask the AI to create an agent:
```
You: "Create a new agent"
```

The wizard will guide you through 10 steps with detailed explanations:

1. **Agent Name** - Unique name for your agent (e.g., `temperature-monitor`)
   - *Learn about:* Naming conventions, package structure
   
2. **VIP Identity** - VIP identity string (e.g., `monitor.agent`)
   - *Learn about:* VOLTTRON Interconnect Protocol, inter-agent communication
   
3. **Description** - What the agent does
   - *Learn about:* Documentation best practices
   
4. **Documentation URL (Optional)** - Link to API docs, GitHub repo, or documentation
   - *Learn about:* AI-powered analysis, automatic recommendations
   - *Supports:* API documentation, GitHub repos, service docs
   - *Get:* Implementation guidance as TODO comments in your code
   
5. **Template Type** - Choose from 4 templates (see below)
   - *Learn about:* Agent patterns, use cases, VOLTTRON architecture
   - *Options:* minimal, listener, driver, historian
   
6. **Subscribe Topics** - Topics to listen to
   - *Learn about:* Pub/sub messaging, topic structure, wildcards
   - *Examples:* Device topics, system topics, custom patterns
   
7. **Publish Topics** - Topics to publish to
   - *Learn about:* Topic naming conventions, VOLTTRON standards
   - *Examples:* Device data, analysis results, status updates
   
8. **Schedule** - Periodic tasks (interval or cron)
   - *Learn about:* Scheduling patterns, periodic vs cron, use cases
   - *Options:* none, interval (every N seconds), cron (specific times)
   
9. **Dependencies** - Additional Python packages
   - *Learn about:* Package management, common libraries
   - *Examples:* requests, pandas, numpy, paho-mqtt
   
10. **Packaging** - Wheel or editable install
    - *Learn about:* Python packaging, development vs production
    - *Options:* wheel (production), editable (development)

**🎓 Educational Features:**
Each step includes:
- ✅ Clear explanation of VOLTTRON concepts
- ✅ Best practices and conventions  
- ✅ Real-world examples
- ✅ Links to official documentation
- ✅ Common patterns and use cases

**Available Templates:**

| Template | Purpose | Use Case |
|----------|---------|----------|
| **minimal** | Basic agent with VIP connection | Learning VOLTTRON, simple monitoring |
| **listener** | Data pipeline with filtering/transformation | Topic monitoring, data forwarding |
| **driver** | Device interface with scheduled polling | Hardware integration, data acquisition |
| **historian** | Data storage with batching and queries | Persistence, analytics, reporting |

**What Gets Generated:**

```
agents/<agent-name>/
├── <agent_name>/
│   ├── __init__.py
│   └── agent.py          # Main agent code with extensive comments
├── config/
│   └── default_config.json
├── tests/
│   └── test_agent.py
├── pyproject.toml        # PEP 517 project metadata
└── README.md             # Usage instructions
```

**Features:**

- ✅ **Extensively Commented Code** - Every function and pattern explained
- ✅ **AI-Powered URL Analysis** - Paste any documentation URL and get implementation recommendations
- ✅ **Best Practices** - Follows VOLTTRON conventions for topics, configs, lifecycle
- ✅ **Ready to Run** - Builds wheel and installs with one command
- ✅ **Customizable** - Templates include TODO markers for easy modification
- ✅ **Validation** - Checks agent names and VIP identity collisions

**🆕 URL Analysis Feature:**

When creating an agent, you can provide a URL to any documentation (API docs, GitHub repo, service documentation) and the AI will:
- Fetch and analyze the content
- Identify authentication methods
- Suggest API endpoints or data sources
- Recommend dependencies
- Generate implementation TODO comments in your code
- Include full recommendations in README

**Example with URL Analysis:**

```
You: "Create a new agent"
AI: "Step 1/10: What's your agent name?"

You: "weather-service"
AI: "Step 2/10: What VIP identity?"

You: "weather.service"
AI: "Step 3/10: Describe your agent..."

You: "Fetches weather data from external API"
AI: "Step 4/10: Documentation URL (Optional)..."

You: "https://openweathermap.org/api"
AI: "🔍 Analyzing URL... ✅ Analysis Complete!
     Found: REST API, requires API key, JSON responses
     Recommendations will be included in generated code.
     
     Step 5/10: Template Type..."

... (continues through remaining steps) ...
```

The generated agent will include detailed comments like:
```python
# Implementation Recommendations Based on https://openweathermap.org/api
#
# TODO: API Integration
# - Endpoint: https://api.openweathermap.org/data/2.5/weather
# - Authentication: API key in query parameter
# - Response format: JSON
# - Add 'requests' to dependencies
#
# TODO: Configuration
# - api_key: Store in config or environment variable
# - base_url: API endpoint
# - update_interval: How often to fetch data
```

**Example Workflow (Without URL):**

```
You: "Create a new agent"
AI: "Step 1/10: What's your agent name?"

You: "temperature-monitor"
AI: "Step 2/10: What VIP identity?"

You: "monitor.temp"
AI: "Step 3/10: Describe your agent..."

... (continues through 10 steps) ...

AI: "Agent project created at agents/temperature-monitor/
     Building package... Done!
     Install with: vctl install agents/temperature-monitor --vip-identity monitor.temp --start"

You: "Install the agent"
AI: "Agent installed and started successfully!"
```

**Manual Installation (if preferred):**

```bash
# After wizard completes, navigate to generated project
cd agents/temperature-monitor

# Build wheel package
python -m build -w

# Install to VOLTTRON
vctl install dist/temperature_monitor-0.1.0-py3-none-any.whl \
  --vip-identity monitor.temp \
  --agent-config config/default_config.json \
  --start --force

# Or install in editable mode for development
pip install -e .
```

**Template Details:**

**Minimal Template:**
- VIP connection and authentication
- Configuration management via `vip.config`
- Heartbeat publishing (every 30 seconds)
- Topic subscription with message handling
- `onstart`/`onstop` lifecycle management

**Listener Template:**
- All minimal features plus:
- Configurable message filtering (by topic or keys)
- Data transformation and enrichment
- Message forwarding to output topics
- Rate limiting (max messages per minute)
- RPC methods for stats and filter control

**Driver Template:**
- All minimal features plus:
- Scheduled device polling (interval or cron)
- Point map configuration (name, type, units, writable, range)
- Device protocol support (simulator, modbus, bacnet, API)
- Standard VOLTTRON device topic publishing
- Error handling with automatic retries
- Connection management

**Historian Template:**
- All minimal features plus:
- Data capture from multiple topics
- Batching (100 records or 60 seconds)
- SQLite storage (adaptable to PostgreSQL/MongoDB)
- RPC query interface with time range filters
- Automatic retention and cleanup
- Stats tracking (records/topics/errors)

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

#### PNNL AI Depot
- `claude-3-7-sonnet-20250219-v1-birthright`
- And other models available at https://ai-incubator-depot.pnnl.gov/#available-models

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

## Troubleshooting

### VOLTTRON Not Found
If you get "VOLTTRON not found" errors:

1. **Check if VOLTTRON is installed:**
   ```bash
   which volttron
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

### Intelligent Discovery Issues
If the AI isn't discovering vctl commands correctly:

1. **Ensure VOLTTRON is in PATH or VOLTTRON_HOME is set**
2. **Check vctl is accessible:** `which vctl`
3. **Run the diagnostic tests:** `python3 tests/test_discovery_quick.py`

## API Endpoints

The application provides several REST API endpoints:

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

# Stop VOLTTRON
curl -X POST "http://127.0.0.1:8000/volttron/stop"
```

## Development

### Running in Development Mode

```bash
python -m chat_app --model claude-3-7-sonnet-20250219-v1-birthright --reload
```

This enables auto-reload, so the server will restart automatically when you make code changes.

### Testing

Run the comprehensive test suite:
```bash
# Quick tests
python3 tests/test_discovery_quick.py

# Full intelligent discovery tests
python3 tests/test_intelligent_discovery.py

# Context retention tests
python3 tests/test_context_retention.py

# Interactive demo
python3 tests/demo_intelligent_discovery.py
```

For more details, see [tests/README_TESTS.md](tests/README_TESTS.md)

### Project Structure

```
volttron-ai/
├── chat_app/
│   ├── __init__.py
│   ├── __main__.py              # Entry point and CLI
│   ├── app.py                   # FastAPI application
│   ├── ai_service.py            # AI model integration
│   ├── agent_creator.py         # Agent scaffolding and wizard
│   ├── volttron_commands.py     # VOLTTRON platform control
│   └── templates/
│       ├── chat.html            # Web interface
│       └── agent_templates/     # Agent code templates
│           ├── minimal.py.template
│           ├── listener.py.template
│           ├── driver.py.template
│           └── historian.py.template
├── agents/                      # Generated agent projects (created at runtime)
├── tests/                       # Test suite
│   ├── test_intelligent_discovery.py
│   ├── test_discovery_quick.py
│   ├── test_context_retention.py
│   ├── demo_intelligent_discovery.py
│   └── README_TESTS.md
├── requirements.txt             # Python dependencies
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
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
- Refer to the main VOLTTRON documentation at https://volttron.readthedocs.io/
- Check the [tests documentation](tests/README_TESTS.md) for testing guidance

---

**Note:** This application provides a modern chat interface for VOLTTRON platform management using AI assistants. The intelligent command discovery feature allows the AI to learn and execute VOLTTRON commands dynamically, making it easier to interact with the platform using natural language.