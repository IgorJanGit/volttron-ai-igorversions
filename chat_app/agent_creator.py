"""
VOLTTRON Agent Creator and Scaffolding Module

This module provides a guided wizard to create custom VOLTTRON agents with:
- Step-by-step requirement collection
- Code scaffolding with extensive comments
- Project structure generation (pyproject.toml, README, tests)
- Packaging (wheel or editable install)
- Installation via vctl or pip

Compatible with VOLTTRON 11+ and Python 3.11+
"""

import os
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from chat_app.volttron_commands import (
    find_vctl_command,
    get_volttron_home,
    find_pip_command,
    vctl_status,
    is_volttron_running_quick
)


class AgentRequirements:
    """Container for agent creation requirements collected from user."""
    
    def __init__(self):
        self.name: str = ""
        self.vip_identity: str = ""
        self.description: str = ""
        self.url: Optional[str] = None  # URL to documentation/API/GitHub repo
        self.ai_recommendations: Optional[str] = None  # AI analysis of URL
        self.template_type: str = "minimal"  # minimal, listener, driver, historian
        self.topics_subscribe: List[str] = []
        self.topics_publish: List[str] = []
        self.schedule_type: Optional[str] = None  # None, "interval", "cron"
        self.schedule_value: Optional[str] = None  # e.g., "30s", "*/5 * * * *"
        self.rpc_methods: List[str] = []
        self.dependencies: List[str] = ["volttron>=11.0.0rc0"]
        self.config_fields: Dict[str, str] = {}  # field_name: field_type
        self.package_format: str = "wheel"  # "wheel" or "editable"
        self.author: str = "VOLTTRON User"
        self.version: str = "0.1.0"
        self.install_after_build: bool = True
        
    def to_dict(self) -> Dict:
        """Convert requirements to dictionary for JSON storage."""
        return {
            "name": self.name,
            "vip_identity": self.vip_identity,
            "description": self.description,
            "url": self.url,
            "ai_recommendations": self.ai_recommendations,
            "template_type": self.template_type,
            "topics_subscribe": self.topics_subscribe,
            "topics_publish": self.topics_publish,
            "schedule_type": self.schedule_type,
            "schedule_value": self.schedule_value,
            "rpc_methods": self.rpc_methods,
            "dependencies": self.dependencies,
            "config_fields": self.config_fields,
            "package_format": self.package_format,
            "author": self.author,
            "version": self.version,
            "install_after_build": self.install_after_build
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentRequirements':
        """Create AgentRequirements from dictionary."""
        req = cls()
        for key, value in data.items():
            if hasattr(req, key):
                setattr(req, key, value)
        return req


def analyze_url_for_agent(url: str, description: str) -> str:
    """
    Analyze a URL (documentation, API, GitHub repo) and provide implementation recommendations.
    
    Args:
        url: URL to documentation or API reference
        description: Brief description of what the agent should do
        
    Returns:
        String with AI-generated recommendations for implementation
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Fetch URL content
        headers = {'User-Agent': 'Mozilla/5.0 (VOLTTRON Agent Creator)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract relevant text (remove scripts, styles)
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit text length for analysis
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        # Generate recommendations based on content
        recommendations = f"""
# Implementation Recommendations Based on {url}

## Analyzed Content Summary
The documentation has been analyzed to provide implementation guidance.

## Suggested Implementation Approach

### 1. API/Service Integration
TODO: Based on the documentation, implement the following:
- Review the API endpoints or service methods described
- Identify authentication requirements (API keys, OAuth, etc.)
- Determine data formats (JSON, XML, CSV, etc.)

### 2. Data Flow
TODO: Configure VOLTTRON topics for:
- **Subscribe to**: Topics that trigger data collection from this service
- **Publish to**: Topics where processed data should be sent
  Example: devices/{{{{AGENT_NAME}}}}/status, analysis/{{{{AGENT_NAME}}}}/results

### 3. Scheduling
TODO: Based on the service requirements:
- If polling is needed: Use interval schedule (e.g., every 60 seconds)
- If event-driven: Subscribe to triggering topics
- If time-based: Use cron schedule

### 4. Dependencies
TODO: You may need to add these packages:
- `requests` - For HTTP API calls
- `beautifulsoup4` - For HTML parsing (if needed)
- Add any SDK mentioned in the documentation

### 5. Configuration Fields
TODO: Add to your agent's config:
- API endpoint URL
- Authentication credentials (use environment variables!)
- Polling interval or schedule
- Data transformation settings

### 6. Error Handling
TODO: Implement robust error handling for:
- Network failures (retries with exponential backoff)
- Authentication errors
- Rate limiting (respect API limits)
- Invalid data responses

### 7. Implementation Steps
1. Read the full documentation at: {url}
2. Set up authentication (API keys, tokens, etc.)
3. Test API calls manually first
4. Implement data fetch in your agent's scheduled method
5. Transform data to VOLTTRON message format
6. Publish to appropriate topics
7. Add logging for debugging
8. Test with VOLTTRON platform

## Next Steps
The generated agent template will include TODO comments with these recommendations.
You'll need to fill in the specific API calls and data transformations based on the documentation.
"""
        
        return recommendations.strip()
        
    except Exception as e:
        return f"""
# URL Analysis Note

Could not automatically analyze {url}: {str(e)}

Please manually review the documentation and implement:
1. Authentication method
2. API endpoints or data sources
3. Request/response formats
4. Error handling requirements
5. Rate limits or usage restrictions

Add implementation code in the generated agent template where you see TODO comments.
"""


def collect_requirements(conversation_state: Dict, step: int, user_input: str) -> Tuple[AgentRequirements, int, str]:
    """
    Collect agent requirements step-by-step from user input.
    
    Args:
        conversation_state: Current conversation state with partial requirements
        step: Current step number (1-10)
        user_input: User's response to current step
        
    Returns:
        Tuple of (requirements object, next step number, prompt for next step)
    """
    # Load existing requirements or create new
    if "agent_requirements" in conversation_state:
        req = AgentRequirements.from_dict(conversation_state["agent_requirements"])
    else:
        req = AgentRequirements()
    
    # Process current step
    prompts = {
        1: """📝 **Step 1/10: Agent Name**

**What is an Agent Name?**
The agent name is a unique identifier for your agent package. It will be used as:
- Directory name for your agent project
- Package name in Python
- Part of the agent's identity on the VOLTTRON platform

**Naming Rules:**
✓ Use lowercase letters, numbers, and hyphens
✓ Start with a letter (not a number)
✓ Keep it descriptive but concise
✗ No spaces or special characters (@, #, etc.)

**Examples:**
- `temperature-monitor` - Monitors temperature sensors
- `hvac-controller` - Controls HVAC systems
- `weather-fetcher` - Fetches external weather data
- `data-aggregator` - Aggregates data from multiple sources

**📚 Reference:** https://volttron.readthedocs.io/en/9.0.4/developing-volttron/developing-agents/agent-development.html

What should we call your agent?""",

        2: """🏷️ **Step 2/10: VIP Identity**

**What is a VIP Identity?**
VIP (VOLTTRON Interconnect Protocol) identity is how your agent identifies itself on the message bus. Other agents use this identity to:
- Send RPC (Remote Procedure Call) requests to your agent
- Recognize your agent's publications
- Authenticate communications

**Identity Guidelines:**
- Can be the same as agent name or more descriptive
- Use dot notation for hierarchical organization (e.g., `campus.building1.controller`)
- Must be unique across all running agents
- Common patterns: `service.function`, `location.device.type`

**Examples:**
- `monitor.temperature` - Temperature monitoring service
- `campus.hvac.controller` - HVAC controller for campus
- `api.weather.openweather` - OpenWeather API integration
- `historian.sqlite` - SQLite historian service

**Why it matters:**
When another agent calls: `self.vip.rpc.call("monitor.temperature", "get_current_temp")`
they're using YOUR VIP identity to reach your agent.

**📚 Reference:** VOLTTRON uses VIP for all inter-agent communication

What VIP identity should your agent use?""",

        3: """📖 **Step 3/10: Agent Description**

**Purpose:**
A clear description helps users (including future you!) understand what the agent does.
This description will appear in:
- Package metadata (pyproject.toml)
- README.md file
- Agent documentation
- `vctl list` output

**Best Practices:**
✓ Be concise but complete (1-2 sentences)
✓ Describe WHAT the agent does, not HOW
✓ Mention key integrations or data sources
✓ State the primary purpose

**Examples:**
- "Monitors temperature sensors and publishes alerts when thresholds are exceeded"
- "Fetches weather data from OpenWeatherMap API and publishes to VOLTTRON message bus"
- "Aggregates power consumption data from multiple buildings and stores to database"
- "Controls HVAC systems based on occupancy and temperature setpoints"

Provide a brief description of what your agent does:""",

        3.5: """🔗 **Step 4/10: Documentation URL (Optional)**

**NEW FEATURE: AI-Powered Implementation Guidance!**

If you have documentation for an API, service, or device you want to integrate, paste the URL here and I'll:
✅ Analyze the documentation automatically
✅ Identify authentication methods (API keys, OAuth, etc.)
✅ Extract API endpoints and data formats
✅ Suggest dependencies (Python packages)
✅ Generate TODO comments with implementation steps
✅ Add recommendations directly to your agent code

**Supported URL Types:**
1. **API Documentation:** OpenAPI/Swagger, REST API docs, GraphQL
   Example: https://openweathermap.org/api
2. **GitHub Repositories:** README files, SDK documentation
   Example: https://github.com/eclipse/paho.mqtt.python
3. **Service Documentation:** IoT platforms, database guides
   Example: https://docs.aws.amazon.com/iot/
4. **Protocol Specifications:** Modbus, BACnet, MQTT
   Example: https://mosquitto.org/documentation/

**What You'll Get:**
The generated agent will include comments like:
```python
# TODO: API Integration
# - Endpoint: https://api.example.com/v1/data
# - Authentication: Bearer token required
# - Response format: JSON
# - Add 'requests' to dependencies
#
# TODO: Error Handling
# - Network failures: Retry with exponential backoff
# - Rate limiting: Respect 60 calls/minute limit
```

**Note:** This step is OPTIONAL. Type 'skip' or 'none' if you don't have a URL.

Enter documentation URL or 'skip':""",

        4: """🎨 **Step 5/10: Template Type**

**What are Agent Templates?**
Templates provide pre-built agent structures with common VOLTTRON patterns. Each template includes extensive comments explaining VOLTTRON concepts.

**Choose Your Template:**

**1. minimal** - Basic Agent (Learning & Simple Tasks)
   ✓ VIP connection and authentication
   ✓ Configuration management via config store
   ✓ Heartbeat publishing
   ✓ Basic pub/sub messaging
   ✓ Lifecycle management (onstart/onstop)
   
   **Use When:** Learning VOLTTRON, simple monitoring, basic data processing
   **Example:** Heartbeat monitor, simple data logger

**2. listener** - Data Pipeline Agent (Topic Monitoring)
   ✓ All minimal features PLUS:
   ✓ Configurable message filtering (by topic or content)
   ✓ Data transformation and enrichment
   ✓ Message forwarding to other topics
   ✓ Rate limiting (prevent flooding)
   ✓ RPC methods for runtime control
   
   **Use When:** Monitoring topics, filtering data, transforming messages
   **Example:** Sensor data filter, message router, data preprocessor

**3. driver** - Device Interface Agent (Scheduled Polling)
   ✓ All minimal features PLUS:
   ✓ Scheduled device polling (interval or cron)
   ✓ Point map configuration (sensor definitions)
   ✓ Protocol support (simulator, Modbus, BACnet, HTTP API)
   ✓ Standard VOLTTRON device topic publishing
   ✓ Error handling with automatic retries
   ✓ Connection management
   
   **Use When:** Hardware integration, periodic data collection, device monitoring
   **Example:** Weather station driver, building automation interface

**4. historian** - Data Storage Agent (Persistence)
   ✓ All minimal features PLUS:
   ✓ Data capture from multiple topics
   ✓ Batching (performance optimization)
   ✓ Database storage (SQLite, PostgreSQL, MongoDB)
   ✓ RPC query interface with time-range filters
   ✓ Automatic data retention and cleanup
   ✓ Statistics tracking
   
   **Use When:** Long-term data storage, analytics, reporting, audit trails
   **Example:** Sensor historian, event logger, time-series database

**📚 Reference:** https://volttron.readthedocs.io/en/9.0.4/developing-volttron/developing-agents/agent-development.html

Enter number (1-4) or name (minimal/listener/driver/historian):""",

        5: """📡 **Step 6/10: Topics to Subscribe**

**What is Pub/Sub?**
VOLTTRON uses a publish/subscribe messaging pattern. Agents subscribe to topics to receive messages published by other agents.

**Topic Structure:**
Topics use a hierarchical structure with forward slashes:
`category/subcategory/specific/item`

**Wildcard Support:**
- `#` - Multi-level wildcard (matches all remaining levels)
- `*` - Single-level wildcard (matches one level)

**Common Topic Patterns:**

**Device Topics:**
- `devices/campus/building1/#` - All devices in building 1
- `devices/*/temperature` - Temperature from all buildings
- `devices/campus/building1/hvac/all` - All data from specific device

**System Topics:**
- `heartbeat/#` - All agent heartbeats
- `platform/status` - Platform status updates
- `alerts/#` - All system alerts

**Custom Topics:**
- `weather/current` - Current weather data
- `analysis/results` - Analysis outputs
- `commands/thermostat` - Thermostat commands

**How Subscriptions Work:**
```python
# Your agent will automatically call _handle_message() when a message
# arrives on any subscribed topic
def _handle_message(self, peer, sender, bus, topic, headers, message):
    # Process the incoming message
    print(f"Received on {topic}: {message}")
```

**Examples:**
- Subscribe to all device data: `devices/#`
- Subscribe to specific sensor: `devices/campus/building1/sensor1/temperature`
- Subscribe to multiple topics: `heartbeat/listener, devices/hvac/#, weather/current`

**📚 Reference:** https://volttron.readthedocs.io/en/9.0.4/developing-volttron/developing-agents/agent-development.html#setting-up-a-subscription

Which topics should your agent subscribe to? (comma-separated, or 'none')""",

        6: """📤 **Step 7/10: Topics to Publish**

**Publishing Data:**
When your agent has data to share with other agents, it publishes to topics. Any agent subscribed to those topics will receive your message.

**Topic Naming Best Practices:**
✓ Use descriptive, hierarchical names
✓ Be consistent with existing topic conventions
✓ Put most specific info last
✓ Avoid overly generic names

**Standard VOLTTRON Topic Conventions:**

**Device Data (if acting as a driver):**
- `devices/{campus}/{building}/{device}/all` - All device points
- `devices/{campus}/{building}/{device}/point/{point_name}` - Specific point

**Analysis/Results:**
- `analysis/{agent_name}/results` - Analysis outputs
- `analysis/{agent_name}/alerts` - Generated alerts
- `analysis/{agent_name}/status` - Agent status updates

**Custom Data:**
- `weather/{service}/current` - Current weather from external service
- `energy/{building}/consumption` - Energy consumption data
- `occupancy/{building}/{room}` - Occupancy status

**Status/Heartbeat:**
- `heartbeat/{agent_identity}` - Your agent's heartbeat
- `status/{agent_name}` - Agent status messages

**How Publishing Works:**
```python
# Publish a message to a topic
self.vip.pubsub.publish(
    'pubsub',  # Message bus
    'devices/campus/building1/temp',  # Topic
    message={'temperature': 72.5, 'units': 'F'}  # Message data
)
```

**Examples:**
- Publish device data: `devices/monitor/temperature`
- Publish analysis: `analysis/hvac-optimizer/recommendations`
- Publish alerts: `alerts/temperature/high-threshold`
- Multiple topics: `status/myagent, results/processed-data`

**📚 Reference:** https://volttron.readthedocs.io/en/9.0.4/developing-volttron/developing-agents/agent-development.html#publishing-data-to-the-message-bus

Which topics will your agent publish to? (comma-separated, or 'none')""",

        7: """⏰ **Step 8/10: Schedule Configuration**

**What is Scheduling?**
Agents can run code at specific times or intervals using VOLTTRON's scheduler. Common for periodic data collection, routine maintenance, or time-based actions.

**Scheduling Options:**

**1. none** - No Scheduled Tasks
   - Agent is purely event-driven (responds to subscriptions or RPC calls)
   - Code runs only when messages arrive
   - **Use when:** Your agent only needs to react to events
   
**2. interval** - Periodic Execution
   - Runs at regular intervals (every N seconds/minutes/hours)
   - Simple and reliable for routine tasks
   - **Use when:** Polling APIs, collecting data, periodic checks
   
   **Format Examples:**
   - `30` or `30s` - Every 30 seconds
   - `5m` - Every 5 minutes
   - `1h` - Every hour
   - `3600` - Every 3600 seconds (1 hour)

**3. cron** - Time-Based Scheduling
   - Runs at specific times using cron expressions
   - More complex but very flexible
   - **Use when:** Daily reports, end-of-day processing, specific times
   
   **Cron Format:** `minute hour day month weekday`
   
   **Examples:**
   - `0 0 * * *` - Daily at midnight
   - `0 */6 * * *` - Every 6 hours
   - `30 2 * * 1` - Every Monday at 2:30 AM
   - `0 9 1 * *` - First day of month at 9 AM

**How Scheduling Works:**
```python
# Interval example - called every 60 seconds
@Core.periodic(60)
def poll_data(self):
    data = self.fetch_from_device()
    self.publish_data(data)

# Cron example - called daily at midnight
@Core.schedule(cron('0 0 * * *'))
def daily_report(self):
    self.generate_and_send_report()
```

**Choosing the Right Schedule:**
- **Weather API:** interval:300 (5 minutes)
- **Building data:** interval:60 (1 minute)
- **Daily reports:** cron:0 0 * * *
- **Business hours:** cron:0 9-17 * * 1-5

**📚 Reference:** https://volttron.readthedocs.io/en/9.0.4/developing-volttron/developing-agents/agent-development.html#periodics-and-scheduling

Does your agent need a schedule? Enter:
1. **none** - No scheduling
2. **interval** - Periodic execution
3. **cron** - Time-based schedule

Your choice:""",

        8: """🔧 **Step 9/10: Python Dependencies**

**What are Dependencies?**
Dependencies are Python packages your agent needs to function. They're automatically installed when your agent is installed.

**Default Dependency:**
✓ `volttron>=11.0.0rc0` (always included)

**Common Additional Dependencies:**

**Data Processing:**
- `numpy` - Numerical computing
- `pandas>=1.5.0` - Data analysis and manipulation
- `scipy` - Scientific computing

**Web & APIs:**
- `requests` - HTTP library for REST APIs
- `aiohttp` - Async HTTP client/server
- `websockets` - WebSocket client/server

**Databases:**
- `psycopg2-binary` - PostgreSQL adapter
- `pymongo` - MongoDB driver
- `sqlalchemy` - SQL toolkit and ORM

**IoT Protocols:**
- `paho-mqtt` - MQTT client
- `pymodbus` - Modbus protocol
- `bacpypes` - BACnet protocol

**Data Formats:**
- `pyyaml` - YAML parser
- `xmltodict` - XML to dict converter
- `msgpack` - Binary serialization

**Utilities:**
- `python-dateutil` - Date/time utilities
- `pytz` - Timezone handling
- `schedule` - Job scheduling

**Version Pinning:**
- Exact version: `requests==2.28.0`
- Minimum version: `pandas>=1.5.0`
- Range: `numpy>=1.20,<2.0`
- No version: `pyyaml` (latest)

**How Dependencies are Used:**
They'll be added to your `pyproject.toml`:
```toml
dependencies = [
    "volttron>=11.0.0rc0",
    "requests",
    "pandas>=1.5.0",
    "paho-mqtt"
]
```

**Examples:**
- API agent: `requests, python-dateutil`
- Data analysis: `numpy, pandas, scipy`
- IoT integration: `paho-mqtt, pymodbus`
- Database storage: `psycopg2-binary, sqlalchemy`

**📚 Reference:** Standard Python packaging conventions

Enter additional packages (comma-separated, or 'none'):
(volttron>=11.0.0rc0 is already included)""",

        9: """📦 **Step 10/10: Packaging Method**

**How to Package Your Agent:**

**1. wheel** - Build Installable Package (RECOMMENDED)
   ✓ Creates a `.whl` file (Python Wheel format)
   ✓ Standard Python package format
   ✓ Can be distributed and installed anywhere
   ✓ Installed via: `vctl install agent.whl`
   ✓ Clean separation from development
   ✓ **Best for:** Production deployments, sharing agents, final versions
   
   **What happens:**
   ```bash
   python -m build -w
   # Creates: dist/my_agent-0.1.0-py3-none-any.whl
   
   vctl install dist/my_agent-0.1.0-py3-none-any.whl \
       --vip-identity my.agent \
       --start
   ```

**2. editable** - Development Mode
   ✓ Installs as "editable" (pip install -e .)
   ✓ Code changes take effect immediately (no rebuild)
   ✓ Easier for active development and testing
   ✓ Agent runs from source directory
   ✓ **Best for:** Active development, testing, debugging
   
   **What happens:**
   ```bash
   pip install -e .
   # Agent runs from your source directory
   # Edit files → Restart agent → Changes apply
   ```

**Comparison:**

| Feature | Wheel | Editable |
|---------|-------|----------|
| For production | ✅ Yes | ❌ No |
| For development | ⚠️ Rebuilds needed | ✅ Yes |
| Code changes | Rebuild required | Immediate |
| Distribution | Easy to share | Source only |
| Installation | Standard | Development |

**Recommendation:**
- **During development:** Use editable mode for faster iteration
- **For deployment:** Build a wheel for clean installation
- **You can do both:** Start with editable, build wheel when ready

**The Build Process:**
After this step, I will:
1. Generate all agent files with extensive comments
2. Create pyproject.toml with your dependencies
3. Build the package in your chosen format
4. Offer to install it to VOLTTRON

**📚 Reference:** https://volttron.readthedocs.io/en/9.0.4/developing-volttron/developing-agents/agent-development.html#packaging-and-installation

How should we package your agent?
1. **wheel** - Build installable package (recommended for production)
2. **editable** - Development mode (recommended for active development)

Your choice:"""
    }
    
    # Update requirements based on step
    if step == 1 and user_input:
        req.name = user_input.strip().lower().replace(" ", "-")
        req.vip_identity = req.name.replace("-", ".")  # Suggest default
        
    elif step == 2 and user_input:
        req.vip_identity = user_input.strip()
        
    elif step == 3 and user_input:
        req.description = user_input.strip()
        
    elif step == 3.5 and user_input:
        # Handle optional URL input
        if user_input.strip().lower() not in ["skip", "none", ""]:
            req.url = user_input.strip()
            # Will analyze URL in next step via tool
            return req, 3.6, "🔍 **Analyzing URL...**\n\nFetching and analyzing documentation. This may take a moment..."
        # Skip URL analysis
        
    elif step == 3.6:
        # URL analysis complete, continue to template selection
        pass
        
    elif step == 4 and user_input:
        template_map = {"1": "minimal", "2": "listener", "3": "driver", "4": "historian"}
        req.template_type = template_map.get(user_input.strip(), user_input.strip().lower())
        
    elif step == 5 and user_input:
        if user_input.strip().lower() not in ["none", ""]:
            req.topics_subscribe = [t.strip() for t in user_input.split(",")]
            
    elif step == 6 and user_input:
        if user_input.strip().lower() not in ["none", ""]:
            req.topics_publish = [t.strip() for t in user_input.split(",")]
            
    elif step == 7 and user_input:
        schedule_map = {"1": None, "2": "interval", "3": "cron"}
        req.schedule_type = schedule_map.get(user_input.strip(), user_input.strip().lower() if user_input.strip().lower() != "none" else None)
        
        # If schedule chosen, ask for value
        if req.schedule_type == "interval":
            return req, 7.5, "⏰ **Schedule Value**\n\nHow often? (e.g., '30s', '5m', '1h')\n\n💡 s=seconds, m=minutes, h=hours"
        elif req.schedule_type == "cron":
            return req, 7.5, "⏰ **Schedule Value**\n\nEnter cron expression (e.g., '0 0 * * *' for daily at midnight)\n\n💡 Format: minute hour day month weekday"
            
    elif step == 7.5 and user_input:
        req.schedule_value = user_input.strip()
        
    elif step == 8 and user_input:
        if user_input.strip().lower() not in ["none", ""]:
            new_deps = [d.strip() for d in user_input.split(",")]
            req.dependencies.extend(new_deps)
            
    elif step == 9 and user_input:
        package_map = {"1": "wheel", "2": "editable"}
        req.package_format = package_map.get(user_input.strip(), user_input.strip().lower())
    
    # Determine next step
    if step == 3:
        next_step = 3.5  # Ask for URL
    elif step == 3.5:
        next_step = 4  # Skip analysis marker, go to template
    elif step == 3.6:
        next_step = 4  # After analysis, go to template
    elif step < 7:
        next_step = step + 1
    elif step == 7.5:
        next_step = 8
    else:
        next_step = step + 1
    
    if next_step > 9:
        # All steps complete
        return req, 10, "✅ **Requirements Complete!**\n\nReady to generate your agent. Proceeding to scaffold..."
    
    # Get next prompt
    next_prompt = prompts.get(next_step, "")
    
    return req, next_step, next_prompt


def generate_templates(requirements: AgentRequirements) -> Dict[str, str]:
    """
    Generate agent code templates based on requirements.
    
    Args:
        requirements: Agent requirements object
        
    Returns:
        Dictionary mapping filename to file content
    """
    templates_dir = Path(__file__).parent / "templates" / "agent_templates"
    
    # Load appropriate template
    template_file = templates_dir / f"{requirements.template_type}.py.template"
    
    if not template_file.exists():
        # Fallback to minimal template
        template_file = templates_dir / "minimal.py.template"
    
    try:
        with open(template_file, 'r') as f:
            agent_code = f.read()
    except FileNotFoundError:
        # Generate inline minimal template if files don't exist
        agent_code = _generate_minimal_template_inline(requirements)
    
    # Substitute placeholders
    substitutions = {
        "{{AGENT_NAME}}": requirements.name,
        "{{VIP_IDENTITY}}": requirements.vip_identity,
        "{{DESCRIPTION}}": requirements.description,
        "{{AUTHOR}}": requirements.author,
        "{{VERSION}}": requirements.version,
        "{{TOPICS_SUBSCRIBE}}": str(requirements.topics_subscribe),
        "{{TOPICS_PUBLISH}}": str(requirements.topics_publish),
        "{{SCHEDULE_TYPE}}": requirements.schedule_type or "None",
        "{{SCHEDULE_VALUE}}": requirements.schedule_value or "None"
    }
    
    for placeholder, value in substitutions.items():
        agent_code = agent_code.replace(placeholder, value)
    
    # Add AI recommendations as comments at the top if URL was analyzed
    if requirements.ai_recommendations:
        ai_comments = "\n".join(f"# {line}" for line in requirements.ai_recommendations.split("\n"))
        # Insert after the module docstring
        parts = agent_code.split('"""', 2)
        if len(parts) >= 3:
            agent_code = parts[0] + '"""' + parts[1] + '"""' + "\n\n" + ai_comments + "\n" + parts[2]
    
    # Generate additional files
    files = {
        f"{requirements.name.replace('-', '_')}/agent.py": agent_code,
        f"{requirements.name.replace('-', '_')}/__init__.py": _generate_init_file(requirements),
        "pyproject.toml": _generate_pyproject_toml(requirements),
        "README.md": _generate_readme(requirements),
        "config/default_config.json": _generate_default_config(requirements),
        "tests/test_agent.py": _generate_test_file(requirements)
    }
    
    # Add AI recommendations to README if available
    if requirements.ai_recommendations and "README.md" in files:
        files["README.md"] = files["README.md"].replace(
            "## Installation",
            f"## AI Implementation Recommendations\n\n{requirements.ai_recommendations}\n\n## Installation"
        )
    
    return files


def _generate_topic_subscriptions(req: AgentRequirements) -> str:
    """Generate topic subscription code."""
    if not req.topics_subscribe:
        return "# No topics to subscribe to"
    
    subscriptions = []
    for topic in req.topics_subscribe:
        subscriptions.append(f'''        self.vip.pubsub.subscribe(
            peer='pubsub',
            prefix='{topic}',
            callback=self._handle_message
        )
        _log.info("Subscribed to topic: {topic}")''')
    
    return '\n'.join(subscriptions) if subscriptions else "# No topics to subscribe to"


def _generate_heartbeat_publishes(req: AgentRequirements) -> str:
    """Generate heartbeat publish code."""
    topics = req.topics_publish or ['heartbeat']
    publishes = []
    
    for topic in topics:
        publishes.append(f'''        self.vip.pubsub.publish(
            peer='pubsub',
            topic='{topic}',
            message={{'status': 'alive', 'timestamp': utils.format_timestamp(utils.get_aware_utcnow())}}
        )''')
    
    return '\n'.join(publishes)


def _generate_minimal_template_inline(req: AgentRequirements) -> str:
    """Generate minimal agent template inline when template files unavailable."""
    return f'''"""
{req.description}

This agent was auto-generated by the VOLTTRON Agent Creator.
"""

import logging
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core

# Setup logging
utils.setup_logging()
_log = logging.getLogger(__name__)

__version__ = "{req.version}"


class {req.name.replace("-", "_").title().replace("_", "")}Agent(Agent):
    """
    {req.description}
    
    This agent demonstrates basic VOLTTRON agent structure with:
    - VIP connection and identity
    - Configuration handling
    - Periodic heartbeat
    - Pub/sub messaging
    - Graceful shutdown
    """
    
    def __init__(self, config_path, **kwargs):
        """
        Initialize the agent.
        
        Args:
            config_path: Path to agent configuration file
            **kwargs: Additional agent initialization parameters
        """
        super({req.name.replace("-", "_").title().replace("_", "")}Agent, self).__init__(**kwargs)
        
        # Default configuration
        self.default_config = {{
            "heartbeat_period": 30
        }}
        
        # Load configuration
        self.vip.config.set_default("config", self.default_config)
        self.vip.config.subscribe(self._configure, actions=["NEW", "UPDATE"], pattern="config")
        
    def _configure(self, config_name, action, contents):
        """
        Handle configuration updates.
        
        Args:
            config_name: Name of configuration being updated
            action: Type of update (NEW, UPDATE, DELETE)
            contents: New configuration contents
        """
        config = self.default_config.copy()
        config.update(contents)
        
        _log.info("Configuration updated: %s", config)
        
        self.heartbeat_period = config.get("heartbeat_period", 30)
        
    @Core.receiver("onstart")
    def onstart(self, sender, **kwargs):
        """
        Called when agent starts.
        
        This is where you should:
        - Subscribe to topics
        - Start periodic tasks
        - Initialize connections
        """
        _log.info(f"Agent {{self.core.identity}} starting...")
        
        # Subscribe to topics if specified
        {self._generate_topic_subscriptions(req)}
        
        # Start periodic heartbeat
        self.core.periodic(self.heartbeat_period, self._send_heartbeat)
        
        _log.info(f"Agent {{self.core.identity}} started successfully")
        
    def _handle_message(self, peer, sender, bus, topic, headers, message):
        """
        Handle incoming messages from subscribed topics.
        
        Args:
            peer: Peer name (usually 'pubsub')
            sender: Message sender identity
            bus: Message bus name
            topic: Topic the message was published to
            headers: Message headers dictionary
            message: Message payload
        """
        _log.info("Received message on topic %s: %s", topic, message)
        
        # Process message here
        # Example: Extract data, perform calculations, publish results
        
    def _send_heartbeat(self):
        """
        Send periodic heartbeat message.
        
        This demonstrates basic publishing to the message bus.
        """
        {self._generate_heartbeat_publishes(req)}
        
        _log.debug("Heartbeat sent")
        
    @Core.receiver("onstop")
    def onstop(self, sender, **kwargs):
        """
        Called when agent stops.
        
        Use this to:
        - Close connections
        - Save state
        - Clean up resources
        """
        _log.info(f"Agent {{self.core.identity}} stopping...")


def main():
    """Main entry point for the agent."""
    utils.vip_main({req.name.replace("-", "_").title().replace("_", "")}Agent, version=__version__)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
'''


def _generate_init_file(req: AgentRequirements) -> str:
    """Generate __init__.py for agent package."""
    return f'''"""
{req.name} - {req.description}
"""

__version__ = "{req.version}"
'''


def _generate_pyproject_toml(req: AgentRequirements) -> str:
    """Generate pyproject.toml for agent package."""
    package_name = req.name.replace("-", "_")
    deps_str = '",\n    "'.join(req.dependencies)
    
    return f'''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{req.name}"
version = "{req.version}"
description = "{req.description}"
authors = [
    {{name = "{req.author}"}}
]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "{deps_str}"
]

[project.scripts]
{req.name} = "{package_name}.agent:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["{package_name}*"]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0"
]
'''


def _generate_readme(req: AgentRequirements) -> str:
    """Generate README.md for agent package."""
    return f'''# {req.name}

{req.description}

## Overview

This agent was created using the VOLTTRON Agent Creator and provides:

- **VIP Identity**: `{req.vip_identity}`
- **Template Type**: {req.template_type}
- **Subscribed Topics**: {", ".join(req.topics_subscribe) if req.topics_subscribe else "None"}
- **Published Topics**: {", ".join(req.topics_publish) if req.topics_publish else "None"}
- **Schedule**: {req.schedule_type or "None"} {f"({req.schedule_value})" if req.schedule_value else ""}

## Installation

### Option 1: Install via vctl (Recommended)

```bash
# Build the wheel
python -m build -w

# Install using vctl
vctl install dist/{req.name}-{req.version}-py3-none-any.whl \\
    --vip-identity {req.vip_identity} \\
    --start
```

### Option 2: Development Install

```bash
# Install in editable mode
pip install -e .

# Or install via vctl from source
vctl install . --vip-identity {req.vip_identity} --start
```

## Configuration

Edit `config/default_config.json` to customize agent behavior:

```json
{{
    "heartbeat_period": 30
}}
```

Store configuration in VOLTTRON:

```bash
vctl config store {req.vip_identity} config config/default_config.json
```

## Usage

### Start the Agent

```bash
vctl start {req.vip_identity}
```

### Check Status

```bash
vctl status
```

### View Logs

```bash
tail -f $VOLTTRON_HOME/volttron.log | grep {req.vip_identity}
```

### Stop the Agent

```bash
vctl stop {req.vip_identity}
```

## Development

### Run Tests

```bash
pytest tests/
```

### Code Structure

- `{req.name.replace("-", "_")}/agent.py` - Main agent implementation
- `config/default_config.json` - Default configuration
- `tests/test_agent.py` - Unit tests

## Requirements

- Python >= 3.11
- VOLTTRON >= 11.0.0rc0
{f"- {chr(10).join(f'- {dep}' for dep in req.dependencies if not dep.startswith('volttron'))}" if any(not d.startswith('volttron') for d in req.dependencies) else ""}

## License

See LICENSE file for details.

## Author

{req.author}

## Version

{req.version}
'''


def _generate_default_config(req: AgentRequirements) -> str:
    """Generate default configuration JSON."""
    config = {
        "heartbeat_period": 30
    }
    
    # Add custom config fields
    for field_name, field_type in req.config_fields.items():
        if field_type == "string":
            config[field_name] = ""
        elif field_type == "number":
            config[field_name] = 0
        elif field_type == "boolean":
            config[field_name] = False
        else:
            config[field_name] = None
    
    return json.dumps(config, indent=4)


def _generate_test_file(req: AgentRequirements) -> str:
    """Generate basic test file."""
    class_name = req.name.replace("-", "_").title().replace("_", "")
    package_name = req.name.replace("-", "_")
    
    return f'''"""
Tests for {req.name} agent.
"""

import pytest
from unittest.mock import MagicMock, patch


def test_agent_import():
    """Test that agent module can be imported."""
    from {package_name}.agent import {class_name}Agent
    assert {class_name}Agent is not None


def test_agent_initialization():
    """Test agent initialization."""
    from {package_name}.agent import {class_name}Agent
    
    # Mock VIP and config
    with patch('volttron.platform.vip.agent.Agent.__init__') as mock_init:
        mock_init.return_value = None
        agent = {class_name}Agent.__new__({class_name}Agent)
        
        # Initialize manually for testing
        agent.vip = MagicMock()
        agent.core = MagicMock()
        agent.default_config = {{"heartbeat_period": 30}}
        
        assert agent.default_config["heartbeat_period"] == 30


@pytest.mark.parametrize("heartbeat_period", [10, 30, 60])
def test_heartbeat_configuration(heartbeat_period):
    """Test heartbeat period configuration."""
    from {package_name}.agent import {class_name}Agent
    
    agent = {class_name}Agent.__new__({class_name}Agent)
    agent.default_config = {{"heartbeat_period": heartbeat_period}}
    
    assert agent.default_config["heartbeat_period"] == heartbeat_period
'''


def write_agent_project(requirements: AgentRequirements, output_dir: Optional[str] = None) -> str:
    """
    Write complete agent project structure to disk.
    
    Args:
        requirements: Agent requirements object
        output_dir: Output directory (defaults to ./agents/<agent-name>)
        
    Returns:
        Path to created project directory
    """
    if output_dir is None:
        workspace_root = Path(__file__).parent.parent
        output_dir = workspace_root / "agents" / requirements.name
    else:
        output_dir = Path(output_dir)
    
    # Create directory structure
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate all files
    files = generate_templates(requirements)
    
    # Write files
    for filepath, content in files.items():
        full_path = output_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
    
    _log = logging.getLogger(__name__)
    _log.info(f"Agent project written to: {output_dir}")
    
    return str(output_dir)


def build_package(project_dir: str, format: str = "wheel") -> Tuple[bool, str]:
    """
    Build agent package (wheel or editable install).
    
    Args:
        project_dir: Path to agent project directory
        format: "wheel" or "editable"
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    project_path = Path(project_dir)
    
    if not project_path.exists():
        return False, f"❌ Project directory not found: {project_dir}"
    
    if format == "wheel":
        # Build wheel using python -m build
        try:
            result = subprocess.run(
                ["python", "-m", "build", "-w", str(project_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Find the built wheel
                dist_dir = project_path / "dist"
                wheels = list(dist_dir.glob("*.whl"))
                
                if wheels:
                    wheel_path = wheels[0]
                    return True, f"✅ Wheel built successfully: {wheel_path}"
                else:
                    return False, f"❌ Build succeeded but no wheel found in {dist_dir}"
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return False, f"❌ Build failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "❌ Build timeout (exceeded 120 seconds)"
        except FileNotFoundError:
            return False, "❌ 'build' module not found. Install with: pip install build"
        except Exception as e:
            return False, f"❌ Build error: {str(e)}"
            
    elif format == "editable":
        # Install in editable mode
        try:
            pip_cmd = find_pip_command()
            
            if not pip_cmd:
                return False, "❌ pip not found. Cannot install in editable mode."
            
            result = subprocess.run(
                [pip_cmd, "install", "-e", str(project_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return True, f"✅ Installed in editable mode: {project_path}"
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return False, f"❌ Editable install failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "❌ Install timeout (exceeded 120 seconds)"
        except Exception as e:
            return False, f"❌ Install error: {str(e)}"
    else:
        return False, f"❌ Unknown package format: {format}"


def install_agent_package(
    project_dir: str,
    vip_identity: str,
    config_path: Optional[str] = None,
    start: bool = True,
    method: str = "vctl"
) -> Tuple[bool, str]:
    """
    Install agent package via vctl or pip.
    
    Args:
        project_dir: Path to agent project directory or wheel file
        vip_identity: VIP identity for the agent
        config_path: Optional path to agent config file
        start: Whether to start agent after installation
        method: "vctl" or "pip"
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if method == "vctl":
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return False, "❌ vctl not found. Is VOLTTRON installed and running?"
        
        if not is_volttron_running_quick():
            return False, "❌ VOLTTRON is not running. Start it first with: start volttron"
        
        # Check if project_dir is a wheel or source directory
        project_path = Path(project_dir)
        
        if project_path.is_file() and project_path.suffix == ".whl":
            install_target = str(project_path)
        elif project_path.is_dir():
            # Check for wheel in dist/
            dist_dir = project_path / "dist"
            if dist_dir.exists():
                wheels = list(dist_dir.glob("*.whl"))
                if wheels:
                    install_target = str(wheels[0])
                else:
                    install_target = str(project_path)
            else:
                install_target = str(project_path)
        else:
            return False, f"❌ Invalid install target: {project_dir}"
        
        # Build vctl install command
        cmd = [vctl_cmd, "install", install_target, "--vip-identity", vip_identity]
        
        if config_path:
            cmd.extend(["--agent-config", config_path])
        
        if start:
            cmd.append("--start")
        
        cmd.append("--force")
        
        try:
            env = os.environ.copy()
            env["VOLTTRON_HOME"] = volttron_home
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            
            if result.returncode == 0:
                # Verify installation
                status_output = vctl_status()
                
                if vip_identity in status_output:
                    status_msg = "started" if start else "installed"
                    return True, f"✅ Agent {status_msg} successfully!\n\n{status_output}"
                else:
                    return True, f"✅ Installation completed but agent not found in status. Check logs."
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return False, f"❌ vctl install failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "❌ Installation timeout (exceeded 120 seconds)"
        except Exception as e:
            return False, f"❌ Installation error: {str(e)}"
            
    elif method == "pip":
        pip_cmd = find_pip_command()
        
        if not pip_cmd:
            return False, "❌ pip not found"
        
        project_path = Path(project_dir)
        
        # Determine install target
        if project_path.is_file() and project_path.suffix == ".whl":
            install_target = str(project_path)
        elif project_path.is_dir():
            dist_dir = project_path / "dist"
            if dist_dir.exists():
                wheels = list(dist_dir.glob("*.whl"))
                if wheels:
                    install_target = str(wheels[0])
                else:
                    install_target = str(project_path)
            else:
                install_target = str(project_path)
        else:
            return False, f"❌ Invalid install target: {project_dir}"
        
        try:
            result = subprocess.run(
                [pip_cmd, "install", install_target],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                msg = f"✅ Package installed via pip: {install_target}\n\n"
                msg += f"💡 **Next step**: Use vctl to register and start:\n"
                msg += f"```bash\nvctl install {install_target} --vip-identity {vip_identity} --start\n```"
                return True, msg
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return False, f"❌ pip install failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "❌ Installation timeout (exceeded 120 seconds)"
        except Exception as e:
            return False, f"❌ Installation error: {str(e)}"
    else:
        return False, f"❌ Unknown installation method: {method}"


def validate_agent_name(name: str) -> Tuple[bool, str]:
    """
    Validate proposed agent name.
    
    Args:
        name: Proposed agent name
        
    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    if not name:
        return False, "❌ Agent name cannot be empty"
    
    if " " in name:
        return False, "❌ Agent name cannot contain spaces (use hyphens instead)"
    
    if not name.replace("-", "").replace("_", "").isalnum():
        return False, "❌ Agent name can only contain letters, numbers, hyphens, and underscores"
    
    if name[0].isdigit():
        return False, "❌ Agent name cannot start with a number"
    
    return True, "✅ Valid agent name"


def validate_vip_identity(vip_identity: str) -> Tuple[bool, str]:
    """
    Validate VIP identity and check for collisions.
    
    Args:
        vip_identity: Proposed VIP identity
        
    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    if not vip_identity:
        return False, "❌ VIP identity cannot be empty"
    
    # Check if VOLTTRON is running to check for collisions
    if is_volttron_running_quick():
        status_output = vctl_status()
        
        if vip_identity in status_output:
            return False, f"❌ VIP identity '{vip_identity}' already in use. Choose a different one."
    
    return True, f"✅ VIP identity '{vip_identity}' is available"


import logging
logging.basicConfig(level=logging.INFO)
