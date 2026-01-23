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
from typing import Any, Dict, List, Optional, Tuple
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
    Enhanced to better extract API endpoints, authentication, and code examples.
    
    Args:
        url: URL to documentation or API reference
        description: Brief description of what the agent should do
        
    Returns:
        String with AI-generated recommendations for implementation
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        import json
        
        # Fetch URL content
        headers = {'User-Agent': 'Mozilla/5.0 (VOLTTRON Agent Creator)'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract code blocks (pre, code tags)
        code_blocks = []
        for tag in soup.find_all(['pre', 'code']):
            code = tag.get_text().strip()
            if code and len(code) > 10:
                code_blocks.append(code)
        
        # Look for API endpoints
        endpoints = []
        endpoint_patterns = [
            r'https?://[^\s<>"]+/api/[^\s<>"]+',
            r'GET|POST|PUT|DELETE|PATCH\s+/[^\s<>"]+',
            r'endpoint[:\s]+[\'"]?(/[^\s<>"\'\)]+)',
        ]
        
        page_text = soup.get_text()
        for pattern in endpoint_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            endpoints.extend(matches[:5])  # Limit to 5
        
        # Look for authentication mentions
        auth_info = []
        auth_keywords = ['api key', 'api_key', 'apikey', 'authorization', 'bearer', 'token', 'authentication', 'oauth']
        for keyword in auth_keywords:
            if keyword in page_text.lower():
                # Find context around keyword
                pattern = rf'.{{0,100}}{keyword}.{{0,100}}'
                match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                if match:
                    context = ' '.join(match.group().split())
                    if context not in auth_info:
                        auth_info.append(context[:200])
        
        # Look for request/response examples
        examples = []
        for block in code_blocks:
            if any(keyword in block.lower() for keyword in ['request', 'response', 'curl', 'http', 'json', '{', 'example']):
                examples.append(block[:300])
                if len(examples) >= 3:
                    break
        
        # Extract main content text
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Build enhanced recommendations
        recommendations = f"""
# 📋 Implementation Recommendations Based on {url}

## 🎯 Agent Purpose
{description}

"""
        
        # Add discovered API endpoints
        if endpoints:
            recommendations += "## 🌐 Discovered API Endpoints\n"
            for i, endpoint in enumerate(set(endpoints[:5]), 1):
                recommendations += f"{i}. `{endpoint}`\n"
            recommendations += "\n"
        
        # Add authentication info
        if auth_info:
            recommendations += "## 🔐 Authentication Information\n"
            for info in auth_info[:2]:
                recommendations += f"- {info}\n"
            recommendations += """

**💡 IMPLEMENTATION TIP - API Keys**: 
Store API keys securely in your agent's config file, never in source code!

**In config.json**:
```json
{
    "api_key": "your-key-here",
    "api_url": "https://api.example.com"
}
```

**In your agent code**:
```python
api_key = self.config.get('api_key')
api_url = self.config.get('api_url')
```

🔒 **Security Best Practice**: Use config files or environment variables. Never commit API keys to git!

"""
        
        # Add code examples if found
        if examples:
            recommendations += "## 📝 Found Code Examples\n\n"
            for i, example in enumerate(examples, 1):
                recommendations += f"### Example {i}:\n```\n{example}\n```\n\n"
        
        recommendations += """
## 🛠️ Implementation Guide

### Step 1: Agent Configuration
Add to your agent's config file:
```python
# In config file
{
    "api_url": "BASE_API_URL_HERE",
    "api_key": "YOUR_API_KEY_HERE",
    "poll_interval": 60,
    "publish_topic": "devices/{agent_name}/data"
}
```

### Step 2: Make API Calls
In your agent's scheduled method:
```python
def fetch_data(self):
    \"\"\"Fetch data from API and publish to VOLTTRON.\"\"\"
    try:
        # Get config
        api_url = self.config.get('api_url')
        api_key = self.config.get('api_key')
        
        # Make API request
        headers = {
            'Authorization': f'Bearer {api_key}',  # Or 'X-API-Key': api_key
            'Content-Type': 'application/json'
        }
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        # Publish to VOLTTRON
        topic = self.config.get('publish_topic')
        self.vip.pubsub.publish(
            'pubsub',
            topic,
            message=data
        )
        
        _log.info(f"Published data to {topic}")
        
    except requests.exceptions.RequestException as e:
        _log.error(f"API request failed: {e}")
    except Exception as e:
        _log.error(f"Error processing data: {e}")
```

### Step 3: Dependencies
Add to your pyproject.toml:
```toml
dependencies = [
    "requests>=2.28.0",
]
```

### Step 4: Error Handling Best Practices

**Essential Error Handling**:
- ✅ **Network timeouts**: Set 10-30 seconds, log with context
- ✅ **Retry logic**: Use exponential backoff for transient failures
- ✅ **Rate limits**: Check API docs, implement delays between requests
- ✅ **HTTP errors**: Handle 401 (auth), 404 (not found), 500 (server errors)
- ✅ **Invalid responses**: Validate JSON structure before processing
- ✅ **Connection failures**: Handle DNS errors, network outages
- ✅ **Logging**: Log ALL errors with timestamps and request details

**💡 Pro Tip**: Test your agent offline to verify error handling works!

**Example Error Handling**:
```python
except requests.exceptions.Timeout:
    _log.error(f"⏱️ Request timeout after {timeout}s - {api_url}")
except requests.exceptions.HTTPError as e:
    _log.error(f"❌ HTTP {e.response.status_code}: {e.response.text[:200]}")
except json.JSONDecodeError:
    _log.error(f"📄 Invalid JSON response from {api_url}")
```

### Step 5: Testing
1. Test API call manually with curl or Postman
2. Verify authentication works
3. Check response format matches expectations
4. Test agent with VOLTTRON platform
5. Monitor logs for errors

## 🔗 Reference
Full documentation: {url}

## ⚠️ Important Notes
- Store API keys securely (use config, not hardcode)
- Handle rate limits (add delays between requests if needed)
- Log all API calls for debugging
- Validate all response data before publishing
- Add comprehensive error handling

## 📦 Next Steps
The generated agent code includes TODO comments at key integration points.
Fill in the specific API calls based on the documentation above.
"""
        
        return recommendations.strip()
        
    except requests.exceptions.RequestException as e:
        return f"""
# ⚠️ URL Fetch Failed

Could not fetch {url}: {str(e)}

## Manual Implementation Guide

Since automatic analysis failed, please manually review the documentation and implement:

### 1. Find the Base API URL
Look for the API endpoint in documentation

### 2. Check Authentication
- API key in header?
- Bearer token?
- OAuth required?

### 3. Identify Key Endpoints
List the endpoints you'll use (GET, POST, etc.)

### 4. Review Response Format
- JSON? XML? CSV?
- What fields are important?

### 5. Check Rate Limits
- How many requests per minute/hour?
- Do you need delays?

### Implementation Template
```python
# In your agent's scheduled method:
def fetch_data(self):
    api_url = self.config.get('api_url', 'https://api.example.com')
    api_key = self.config.get('api_key')
    
    headers = {{'Authorization': f'Bearer {{api_key}}'}}
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        self.vip.pubsub.publish('pubsub', 'your/topic', message=data)
```

Visit {url} to review the full documentation.
"""
    except Exception as e:
        return f"""
# ⚠️ Analysis Error

Error analyzing {url}: {str(e)}

Please review the documentation manually and implement the agent based on the API requirements.
Add your implementation in the generated agent template where you see TODO comments.
"""




def check_agent_name_exists(agent_name: str, base_dir: str = "agents") -> Tuple[bool, str]:
    """
    Check if an agent with this name already exists in the agents directory.
    
    Args:
        agent_name: The agent name to check
        base_dir: The base directory where agents are stored
        
    Returns:
        Tuple of (exists: bool, message: str)
    """
    try:
        agent_dir = os.path.join(base_dir, agent_name)
        if os.path.exists(agent_dir):
            return True, f"⚠️ An agent named '{agent_name}' already exists in {agent_dir}."
        return False, ""
    except Exception as e:
        return False, ""


def check_vip_identity_exists(vip_identity: str) -> Tuple[bool, str]:
    """
    Check if a VIP identity is already in use by an installed agent.
    
    Args:
        vip_identity: The VIP identity to check
        
    Returns:
        Tuple of (exists: bool, message: str)
    """
    try:
        # Try to find vctl command
        vctl_paths = [
            os.path.expanduser("~/.local/bin/vctl"),
            "/usr/local/bin/vctl",
            os.path.expanduser("~/volttron/env/bin/vctl")
        ]
        
        vctl_cmd = None
        for path in vctl_paths:
            if os.path.exists(path):
                vctl_cmd = path
                break
        
        if not vctl_cmd:
            # Can't check without vctl, allow it
            return False, ""
        
        # Get VOLTTRON_HOME
        volttron_home = os.environ.get("VOLTTRON_HOME", os.path.expanduser("~/.volttron"))
        
        # Check if VOLTTRON is running
        ps_result = subprocess.run(
            "ps aux | grep bin/volttron | grep -v grep",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if ps_result.returncode != 0:
            # VOLTTRON not running, can't check
            return False, ""
        
        # Get installed agents
        cmd_str = f"export VOLTTRON_HOME={volttron_home} && {vctl_cmd} status"
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout:
            # Parse the output to find VIP identities
            # Format is usually: UUID AGENT_NAME VIP_IDENTITY STATUS
            lines_output = result.stdout.strip().split('\n')
            for line in lines_output:
                parts = line.split()
                # VIP identity is typically the 3rd column
                if len(parts) >= 3 and parts[2] == vip_identity:
                    return True, f"⚠️ VIP identity '{vip_identity}' is already in use by agent '{parts[1]}'."
        
        return False, ""
        
    except Exception as e:
        # If we can't check, allow it
        return False, ""


def collect_requirements(conversation_state: Dict, step: float, user_input: str) -> Tuple[AgentRequirements, float, str]:
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
    # Allow blank/empty input to continue (for steps that just need confirmation)
    blank_continue_steps = [3.6]  # Steps where blank input means "continue"
    blank_skip_steps = [5, 6, 8]  # Steps where blank input means "none/skip"
    required_steps = [1, 2]  # Steps that CANNOT be blank
    
    # Check for blank input on required steps
    if step in required_steps and not user_input.strip():
        error_messages = {
            1: "❌ **Agent name is required and cannot be blank.**\n\nPlease provide a name for your agent:",
            2: "❌ **VIP identity is required and cannot be blank.**\n\nPlease provide a VIP identity for your agent:"
        }
        return req, step, error_messages.get(step, "❌ This field is required.")
    
    if step in blank_continue_steps and not user_input.strip():
        user_input = "continue"
    elif step in blank_skip_steps and not user_input.strip():
        user_input = "none"
    
    prompts = {
        1: """📝  Step 1/10: Agent Name

Choose a name for your agent (like naming a file or folder).

Rules:
  ✓ Use lowercase letters and hyphens
  ✓ Start with a letter
  ✓ Be descriptive
  ✗ No spaces or special characters

Examples:
  • temperature-monitor
  • hvac-controller
  • weather-fetcher
  • data-aggregator

What should we call your agent?""",

        2: """🏷️  Step 2/10: VIP Identity

Think of this as your agent's unique ID (like a phone number).
Other agents use this to communicate with your agent.

Examples:
  • monitor.temperature
  • campus.hvac.controller
  • weather.openweather

Guidelines:
  • Must be unique across all agents
  • Can use dots for organization
  • Often similar to your agent name

What VIP identity should your agent use?""",

        3: """📖  Step 3/10: Agent Description

Describe what your agent does in 1-2 sentences.

Examples:
  • "Monitors temperature sensors and sends alerts when too hot"
  • "Fetches weather data every hour and shares it"
  • "Tracks building energy usage and saves to database"
  • "Controls thermostat based on room occupancy"

Provide a brief description of what your agent does:""",

        3.5: """🔗  Step 4/10: Documentation URL (Optional)

Got a link to API docs or device documentation?
I'll read it and add helpful hints to your code!

What I'll do:
  • Figure out how to connect (API keys, etc.)
  • Suggest Python packages you'll need
  • Add TODO notes with implementation steps

Examples:
  • https://openweathermap.org/api
  • https://github.com/eclipse/paho.mqtt.python
  • https://docs.aws.amazon.com/iot/

Don't have a URL? Just press Enter to skip (completely optional).

Enter documentation URL (or press Enter to skip):""",

        4: """🎨  Step 5/10: Template Type

Choose a starting template for your agent:

  1. minimal - Basic agent (for learning or simple tasks)
     • Starts, stops, sends simple messages
     • Good for: Learning VOLTTRON basics

  2. listener - Monitors and reacts to data
     • Listens to topics and processes messages
     • Good for: Sensor monitoring, filtering data

  3. driver - Polls devices on a schedule
     • Connects to devices/APIs regularly
     • Good for: Weather data, periodic sensor reads

  4. historian - Saves data to a database
     • Stores all sensor data for later analysis
     • Good for: Long-term data storage, reporting

Not sure? Pick 2 (listener) - it's the most flexible.

Enter number (1-4) or name (minimal/listener/driver/historian):""",

        5: """📡  Step 6/10: Subscribe Topics

What messages should your agent listen for?

Examples:
  • devices/building1/temperature  (one sensor)
  • devices/*/temperature  (all temperature sensors)
  • devices/building1/#  (everything from building 1)
  • weather/current  (weather updates)

Wildcards:
  • * = one level
  • # = everything after this point

Multiple topics? Separate with commas.
Not sure? Just press Enter to skip.

Which topics should your agent subscribe to? (comma-separated, or press Enter)""",

        6: """📤  Step 7/10: Publish Topics

What messages will your agent send out?

Examples:
  • devices/myagent/temperature  (sensor data)
  • alerts/temperature/high  (alerts)
  • status/myagent  (status updates)
  • analysis/myagent/results  (analysis results)

Tips:
  • Be specific (include your agent name)
  • Other agents will listen to these topics

Multiple topics? Separate with commas.
Don't need to publish? Just press Enter to skip.

Which topics will your agent publish to? (comma-separated, or press Enter)""",

        7: """⏰  Step 8/10: Schedule

Should your agent run on a schedule or just react to events?

Options:

  1. none - Only reacts when messages arrive
     Choose for: Monitoring and responding to sensors

  2. interval - Runs every X seconds/minutes/hours
     Choose for: Polling APIs, periodic data collection
     Examples: '30s', '5m', '1h'

  3. cron - Runs at specific times
     Choose for: Daily reports, specific time tasks
     Examples: '0 0 * * *' (daily at midnight)

Not sure? Pick 'none'.

Your choice:""",

        8: """🔧  Step 9/10: Dependencies

Need any extra Python packages?

Common packages:
  • requests  (for APIs and web requests)
  • pandas  (for data analysis)
  • paho-mqtt  (for MQTT messaging)
  • psycopg2-binary  (for PostgreSQL)

Multiple packages? Separate with commas.
Not sure? Just press Enter to skip.

Enter additional packages (comma-separated, or press Enter):
(volttron is already included)""",

        9: """📦  Step 10/10: Packaging

How should we package your agent?

Options:

  1. wheel (recommended)
     • Standard installable package
     • Easy to share and deploy
     • Need to rebuild if you change code

  2. editable
     • For active development
     • Code changes apply immediately
     • Not for sharing/production

Not sure? Pick 'wheel' (option 1).

Your choice:"""
    }
    
    # Update requirements based on step
    if step == 1 and user_input:
        proposed_name = user_input.strip().lower().replace(" ", "-")
        
        # Check if agent name already exists
        exists, warning_msg = check_agent_name_exists(proposed_name)
        if exists:
            # Agent name is already used, ask user to choose another
            return req, 1, f"""{warning_msg}

Please choose a different agent name:"""
        
        req.name = proposed_name
        req.vip_identity = req.name.replace("-", ".")  # Suggest default
        
    elif step == 2 and user_input:
        proposed_vip = user_input.strip()
        
        # Check if VIP identity already exists
        exists, warning_msg = check_vip_identity_exists(proposed_vip)
        if exists:
            # VIP identity is in use, ask user to choose another
            return req, 2, f"""{warning_msg}

Please choose a different VIP identity:"""
        
        req.vip_identity = proposed_vip
        
    elif step == 3 and user_input:
        req.description = user_input.strip()
        
    elif step == 3.5:
        # Handle optional URL input (including blank/empty responses)
        if user_input and user_input.strip() and user_input.strip().lower() not in ["skip", "none"]:
            req.url = user_input.strip()
            # Will analyze URL in next step via tool
            return req, 3.6, "🔍 **Analyzing URL...**\n\nFetching and analyzing documentation. This may take a moment..."
        # Skip URL analysis if blank, 'skip', or 'none'
        
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

=== BEGINNER'S GUIDE ===
This file contains your VOLTTRON agent code. An agent is a program that:
1. Connects to the VOLTTRON platform (a message bus system)
2. Can send and receive messages to/from other agents
3. Can run tasks on a schedule (like every 30 seconds)
4. Can subscribe to data topics and react to new data

Key Concepts:
- VIP (VOLTTRON Interconnect Protocol): How agents communicate
- Pub/Sub: Publishing and subscribing to data topics
- RPC: Remote procedure calls between agents
- Config Store: Dynamic configuration without restarting
"""

# === IMPORTS ===
# These are Python libraries we need to make our agent work
import logging  # For writing log messages (like print statements but better)
from volttron.platform.agent import utils  # VOLTTRON utility functions
from volttron.platform.vip.agent import Agent, Core  # Base classes for building agents

# === LOGGING SETUP ===
# Logging helps you debug by writing messages to log files
# Instead of print(), use _log.info(), _log.debug(), _log.error()
utils.setup_logging()
_log = logging.getLogger(__name__)  # Creates a logger specifically for this agent

# === VERSION ===
# Update this when you make changes to your agent
__version__ = "{req.version}"


# === MAIN AGENT CLASS ===
# This is your agent! It inherits from the VOLTTRON Agent base class
# which provides all the communication and message bus functionality
class {req.name.replace("-", "_").title().replace("_", "")}Agent(Agent):
    """
    {req.description}
    
    === WHAT THIS AGENT DOES ===
    This agent demonstrates basic VOLTTRON patterns:
    - Connecting to the message bus with a VIP identity
    - Loading configuration from the config store
    - Running periodic tasks (heartbeat every N seconds)
    - Publishing messages to topics (pub/sub pattern)
    - Subscribing to topics and handling incoming messages
    - Gracefully shutting down when stopped
    
    === HOW TO CUSTOMIZE ===
    1. Modify __init__() to add your own configuration parameters
    2. Update onstart() to subscribe to topics or start tasks
    3. Add your logic to _handle_message() for processing incoming data
    4. Modify _send_heartbeat() or add new methods for your functionality
    """
    
    def __init__(self, config_path, **kwargs):
        """
        Initialize the agent - this runs ONCE when agent is first loaded.
        
        === WHAT HAPPENS HERE ===
        - Calls parent Agent.__init__() to set up VIP connection
        - Defines default configuration values
        - Subscribes to configuration updates (so you can change config without restart)
        
        Args:
            config_path: Path to the agent's configuration file (JSON format)
            **kwargs: Additional parameters passed by VOLTTRON (identity, address, etc.)
        
        === FOR BEGINNERS ===
        The super() call is important - it initializes the parent Agent class
        which sets up all the message bus connections and VIP subsystems.
        Don't remove it!
        """
        # Call parent class initialization - THIS IS REQUIRED
        super({req.name.replace("-", "_").title().replace("_", "")}Agent, self).__init__(**kwargs)
        
        # === DEFAULT CONFIGURATION ===
        # These values are used if no config file is provided
        # You can add your own parameters here (database URL, API keys, etc.)
        self.default_config = {{
            "heartbeat_period": 30  # How often to send heartbeat (seconds)
            # Add more config parameters here as needed:
            # "api_url": "http://example.com/api",
            # "polling_interval": 60,
            # "data_topics": ["devices/building1/sensor1"]
        }}
        
        # === CONFIGURATION STORE SETUP ===
        # This tells VOLTTRON to:
        # 1. Use default_config if no config exists
        # 2. Call _configure() whenever config changes
        # This means you can update config while agent is running!
        self.vip.config.set_default("config", self.default_config)
        self.vip.config.subscribe(
            self._configure,  # Function to call when config changes
            actions=["NEW", "UPDATE"],  # Call on new or updated configs
            pattern="config"  # Name of the config to watch
        )
        
    def _configure(self, config_name, action, contents):
        """
        Handle configuration updates - called when config changes in the store.
        
        === WHAT THIS DOES ===
        - Merges new configuration with defaults
        - Updates agent's internal settings
        - Gets called automatically by VOLTTRON when config changes
        
        Args:
            config_name: Name of the configuration being updated (usually "config")
            action: Type of update - "NEW" (first time) or "UPDATE" (changed)
            contents: Dictionary containing the new configuration values
        
        === FOR BEGINNERS ===
        This is like a "reload configuration" function that runs automatically.
        You don't call this yourself - VOLTTRON calls it for you.
        Add code here to update your agent's behavior when config changes.
        """
        # Start with defaults, then merge in new values from config store
        config = self.default_config.copy()
        config.update(contents)  # Override defaults with new values
        
        _log.info("Configuration updated: %s", config)
        
        # === EXTRACT CONFIGURATION VALUES ===
        # Pull out specific values from config and store them as instance variables
        self.heartbeat_period = config.get("heartbeat_period", 30)
        
        # Add more configuration parsing here:
        # self.api_url = config.get("api_url")
        # self.polling_interval = config.get("polling_interval", 60)
        
    @Core.receiver("onstart")
    def onstart(self, sender, **kwargs):
        """
        Called automatically when agent starts up and connects to message bus.
        
        === WHAT TO PUT HERE ===
        - Subscribe to data topics you want to listen to
        - Start periodic tasks (polling, heartbeats, etc.)
        - Initialize database connections or external APIs
        - Publish an initial status message
        
        Args:
            sender: The Core subsystem that sent this signal
            **kwargs: Additional parameters (usually empty)
        
        === FOR BEGINNERS ===
        This is like a "main()" function for your agent. It runs once after
        the agent connects to VOLTTRON. Put your startup code here.
        
        The @Core.receiver("onstart") decorator tells VOLTTRON to call this
        method automatically - you don't call it yourself.
        """
        _log.info(f"Agent {{self.core.identity}} starting...")
        _log.info(f"My VIP identity is: {{self.core.identity}}")
        _log.info(f"I'm connected to the platform at: {{self.core.address}}")
        
        # === SUBSCRIBE TO TOPICS ===
        # If you want to listen to data from other agents, subscribe here
        {_generate_topic_subscriptions(req)}
        
        # === START PERIODIC TASKS ===
        # Schedule the _send_heartbeat method to run every N seconds
        # self.core.periodic(interval_seconds, function_to_call)
        self.core.periodic(self.heartbeat_period, self._send_heartbeat)
        
        # You can add more periodic tasks:
        # self.core.periodic(60, self._poll_api)  # Poll API every 60 seconds
        # self.core.periodic(300, self._cleanup)   # Run cleanup every 5 minutes
        
        _log.info(f"Agent {{self.core.identity}} started successfully")
        _log.info(f"Heartbeat will run every {{self.heartbeat_period}} seconds")
        
    def _handle_message(self, peer, sender, bus, topic, headers, message):
        """
        Handle incoming messages from topics you've subscribed to.
        
        === WHAT THIS DOES ===
        This is a callback function - it gets called automatically whenever
        a message arrives on a topic you subscribed to.
        
        Args:
            peer: Usually "pubsub" (the message bus)
            sender: VIP identity of the agent that sent the message
            bus: Name of the message bus (usually empty string)
            topic: The full topic string the message was published to
            headers: Dictionary with metadata (timestamps, content-type, etc.)
            message: The actual message payload (can be string, dict, list, etc.)
        
        === FOR BEGINNERS ===
        This is where you process incoming data. For example:
        - A temperature sensor publishes {"temp": 72.5, "units": "F"}
        - This function receives it
        - You can process it, store it, or publish new data based on it
        
        === EXAMPLE ===
        If message = {{"temperature": 72.5, "location": "room1"}}
        You might:
        1. Check if temperature is too high
        2. Calculate an average
        3. Store in database
        4. Publish an alert
        """
        _log.info("=" * 60)
        _log.info("RECEIVED MESSAGE:")
        _log.info(f"  Topic: {{topic}}")
        _log.info(f"  From: {{sender}}")
        _log.info(f"  Message: {{message}}")
        _log.info("=" * 60)
        
        # === YOUR MESSAGE PROCESSING CODE GOES HERE ===
        # Example: Extract data from message
        # if isinstance(message, dict):
        #     temperature = message.get("temperature")
        #     if temperature and temperature > 75:
        #         _log.warning(f"High temperature alert: {{temperature}}")
        #         self._publish_alert("high_temp", temperature)
        
        # Example: Transform and re-publish data
        # processed_data = self._process_data(message)
        # self.vip.pubsub.publish("pubsub", "my/output/topic", message=processed_data)
        
    def _send_heartbeat(self):
        """
        Send periodic heartbeat message - runs automatically based on schedule.
        
        === WHAT THIS DOES ===
        Publishes a message to show the agent is alive and working.
        This runs every self.heartbeat_period seconds (set in config).
        
        === FOR BEGINNERS ===
        This demonstrates how to publish messages. The pattern is:
        self.vip.pubsub.publish(
            peer="pubsub",           # Always "pubsub" for pub/sub messages
            topic="your/topic/here",  # Topic string (like a channel name)
            message={{"your": "data"}}   # Your message (dict, string, list, etc.)
        )
        
        Other agents subscribed to your topic will receive this message.
        """
        {_generate_heartbeat_publishes(req)}
        
        _log.debug("Heartbeat sent")
        
        # === ADD YOUR OWN PERIODIC TASKS ===
        # You can add more code here or create new periodic functions:
        # 
        # def _poll_api(self):
        #     'Fetch data from external API'
        #     response = requests.get(self.api_url)
        #     data = response.json()
        #     self.vip.pubsub.publish("pubsub", "api/data", message=data)
        
    @Core.receiver("onstop")
    def onstop(self, sender, **kwargs):
        """
        Called automatically when agent is stopping or shutting down.
        
        === WHAT TO PUT HERE ===
        - Close database connections
        - Save any state that needs to persist
        - Clean up temporary files
        - Cancel pending operations
        - Publish a "going offline" message
        
        Args:
            sender: The Core subsystem that sent this signal
            **kwargs: Additional parameters (usually empty)
        
        === FOR BEGINNERS ===
        This is like a destructor or cleanup function. It ensures your agent
        shuts down gracefully. VOLTTRON calls this automatically when you stop
        the agent with "vctl stop <agent>".
        
        The @Core.receiver("onstop") decorator is similar to @Core.receiver("onstart")
        but for shutdown instead of startup.
        """
        _log.info(f"Agent {{self.core.identity}} stopping...")
        
        # === ADD YOUR CLEANUP CODE HERE ===
        # Example: Close database connection
        # if hasattr(self, 'db_connection'):
        #     self.db_connection.close()
        #     _log.info("Database connection closed")
        
        # Example: Save state
        # self._save_state()
        
        # Example: Publish shutdown message
        # self.vip.pubsub.publish("pubsub", "agent/status", 
        #     message={{"status": "offline", "identity": self.core.identity}})
        
        _log.info("Agent stopped successfully")


# === MAIN ENTRY POINT ===
def main():
    """
    Main entry point for the agent - called when you run the agent.
    
    === FOR BEGINNERS ===
    This function is called when you start the agent with vctl:
      vctl start --tag <your_agent_tag>
    
    It uses VOLTTRON's vip_main utility which:
    1. Parses command line arguments
    2. Sets up the VIP connection
    3. Creates an instance of your Agent class
    4. Starts the agent event loop
    
    You typically don't need to modify this function.
    """
    utils.vip_main({req.name.replace("-", "_").title().replace("_", "")}Agent, version=__version__)


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
    config: Dict[str, Any] = {
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
        output_path = workspace_root / "agents" / requirements.name
    else:
        output_path = Path(output_dir)
    
    # Create directory structure
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate all files
    files = generate_templates(requirements)
    
    # Write files
    for filepath, content in files.items():
        full_path = output_path / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
    
    _log = logging.getLogger(__name__)
    _log.info(f"Agent project written to: {output_path}")
    
    return str(output_path)


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
    
    # Check for invalid starting characters
    if not name[0].isalpha():
        return False, "❌ Agent name must start with a letter (a-z, A-Z)"
    
    # Check for emojis and special characters
    import unicodedata
    for char in name:
        category = unicodedata.category(char)
        # Allow letters, numbers, hyphens, and underscores only
        if char not in ['-', '_'] and not char.isalnum():
            return False, "❌ Agent name can only contain letters, numbers, hyphens, and underscores"
        # Reject emojis and symbols
        if category.startswith('S') or category.startswith('C'):
            return False, "❌ Agent name cannot contain emojis or special symbols"
    
    # Additional check: name should be reasonable length
    if len(name) > 50:
        return False, "❌ Agent name is too long (maximum 50 characters)"
    
    if len(name) < 2:
        return False, "❌ Agent name is too short (minimum 2 characters)"
    
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
