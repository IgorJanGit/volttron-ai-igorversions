import subprocess
import os
import shutil
from pathlib import Path

def find_volttron_command():
    """Find volttron command in various locations."""
    # First, check if it's in PATH
    volttron_cmd = shutil.which("volttron")
    if volttron_cmd:
        return volttron_cmd
    
    # Common VOLTTRON installation locations
    possible_paths = [
        # Virtual environment locations
        os.path.join(os.getenv("VIRTUAL_ENV", ""), "bin", "volttron"),
        # User home directory installations
        os.path.expanduser("~/volttron/bin/volttron"),
        os.path.expanduser("~/VOLTTRON/bin/volttron"),
        os.path.expanduser("~/volttron-env/bin/volttron"),
        os.path.expanduser("~/VOLTTRON/env/bin/volttron"),
        os.path.expanduser("~/VOLTTRON/AI/env/bin/volttron"),
        # Work directory installations (Igor's setup)
        "/home/igor/Work/Volttron_eclispe/env/bin/volttron",
        "/home/igor/Work/Volttron_eclispe/volttron/bin/volttron",
        # Generic work directory patterns
        os.path.expanduser("~/Work/Volttron_eclispe/env/bin/volttron"),
        os.path.expanduser("~/Work/volttron/env/bin/volttron"),
        # System installations
        "/opt/volttron/bin/volttron",
        "/usr/local/bin/volttron",
        "/usr/bin/volttron"
    ]
    
    for path in possible_paths:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    
    return None

def find_vctl_command():
    """Find vctl command in various locations."""
    # First, check if it's in PATH
    vctl_cmd = shutil.which("vctl")
    if vctl_cmd:
        return vctl_cmd
    
    # If volttron is found, vctl should be in the same directory
    volttron_cmd = find_volttron_command()
    if volttron_cmd:
        vctl_path = os.path.join(os.path.dirname(volttron_cmd), "vctl")
        if os.path.isfile(vctl_path) and os.access(vctl_path, os.X_OK):
            return vctl_path
    
    return None

def get_volttron_env_path():
    """Get the path to the VOLTTRON virtual environment."""
    # Check if VIRTUAL_ENV is set (when running in activated venv)
    venv_path = os.getenv("VIRTUAL_ENV")
    if venv_path:
        return venv_path
    
    # Try to detect from volttron command location
    volttron_cmd = find_volttron_command()
    if volttron_cmd:
        # Extract the environment path (remove /bin/volttron)
        bin_dir = os.path.dirname(volttron_cmd)
        if bin_dir.endswith("/bin"):
            return os.path.dirname(bin_dir)
    
    return None

def get_volttron_home():
    """Get the VOLTTRON_HOME directory."""
    # Check if VOLTTRON_HOME is set in environment
    volttron_home = os.getenv("VOLTTRON_HOME")
    if volttron_home:
        return volttron_home
    
    # Try common locations
    possible_homes = [
        os.path.expanduser("~/.volttron"),
        os.path.expanduser("~/volttron_home"),
        os.path.expanduser("~/VOLTTRON/volttron_home"),
        os.path.expanduser("~/VOLTTRON/AI/volttron_home_new"),
        "/tmp/volttron_home",
        "./volttron_home"
    ]
    
    for home in possible_homes:
        if os.path.isdir(home):
            return home
    
    # Default fallback
    return os.path.expanduser("~/.volttron")

def start_volttron():
    """Start volttron in the background using the correct virtual environment."""
    try:
        volttron_cmd = find_volttron_command()
        volttron_home = get_volttron_home()
        
        # Check if the volttron command exists
        if not volttron_cmd:
            return check_volttron_installation()
        
        # Set environment variables for VOLTTRON
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Create VOLTTRON_HOME directory if it doesn't exist
        os.makedirs(volttron_home, exist_ok=True)
        
        # Start volttron in the background
        process = subprocess.Popen(
            [volttron_cmd, "-vv", "-l", "volttron.log"], 
            env=env,
            cwd=volttron_home
        )
        return f"VOLTTRON started with PID {process.pid} (VOLTTRON_HOME: {volttron_home})"
    except Exception as e:
        return f"Error starting VOLTTRON: {str(e)}"

def stop_volttron():
    """Stop volttron platform using the correct virtual environment."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        # Check if the vctl command exists
        if not vctl_cmd:
            return check_volttron_installation()
        
        # Set environment variables for VOLTTRON
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Stop volttron platform
        result = subprocess.run(
            [vctl_cmd, "shutdown", "--platform"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home
        )
        
        if result.returncode == 0:
            return "VOLTTRON stopped successfully"
        else:
            return f"VOLTTRON stop result: {result.stdout or result.stderr}"
    except Exception as e:
        return f"Error stopping VOLTTRON: {str(e)}"

def vctl_status(explain=False):
    """Get detailed VOLTTRON agent status using vctl status command."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Get detailed agent status
        result = subprocess.run(
            [vctl_cmd, "status"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home
        )
        
        if result.returncode == 0:
            status_output = result.stdout.strip()
            
            # Parse and explain the status output
            if not status_output:
                if explain:
                    return """
🟡 **VOLTTRON is running, but it looks pretty quiet in here!**

No agents are currently installed or running. This is normal for a fresh VOLTTRON installation.

💡 **Want to get started?**
   • Install some agents
   • Check out the platform driver for connecting to devices
   • Ask me "How do I install agents?" for help

Your VOLTTRON platform is ready - it just needs some agents to manage! 🤖
"""
                else:
                    return "I'm up and running, but I don't have any agents installed yet. Pretty quiet around here!"
            
            # Make the status output more readable and conversational
            readable_status = make_status_readable(status_output)
            conversational_summary = make_status_conversational(status_output)
            
            # Return brief status by default, detailed explanation if requested
            if explain:
                explanation = """
📊 **Here's what's happening with your VOLTTRON agents:**

Let me break down what you're seeing:
• **UUID** = Each agent gets a unique ID number  
• **AGENT** = The agent's name and version (like volttron-listener-2.0.0rc3)
• **IDENTITY** = How the agent introduces itself on the message bus
• **TAG** = Optional nickname you can give agents
• **PRIORITY** = Startup order (lower numbers start first)  
• **STATUS** = What the agent is doing right now
• **HEALTH** = How the agent is feeling (good/bad/unknown)

**Current Status:**
"""
                return f"{explanation}\n{readable_status}\n\n💬 Need help with any of these agents? Just ask!"
            else:
                # Return conversational summary instead of raw table
                return conversational_summary
                
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            if "not connected" in error_msg.lower() or "connection" in error_msg.lower():
                if explain:
                    return """
❌ **Oops! VOLTTRON isn't running right now.**

The platform needs to be started before I can check on your agents.

🚀 **Ready to fire it up?** Just say:
   • "Start VOLTTRON"
   • "Launch the platform"  
   • "Get VOLTTRON running"

I'll get it started for you! ⚡
"""
                else:
                    return "Uh oh, I'm not running right now! Want to start me up?"
            else:
                return f"I'm having trouble checking my status: {error_msg}"
    except Exception as e:
        return f"Something went wrong while I was checking on myself: {str(e)}"

def make_status_conversational(status_output):
    """Convert status output to conversational summary."""
    if not status_output:
        return "I'm running but don't have any agents yet."
    
    lines = status_output.strip().split('\n')
    if len(lines) < 2:
        return "I'm running but something seems off with my agent status."
    
    agents = []
    running_count = 0
    not_running_count = 0
    bad_health_count = 0
    
    # Parse each agent line
    for line in lines[1:]:
        if not line.strip():
            continue
            
        parts = line.split()
        if len(parts) >= 3:
            uuid = parts[0]
            agent_name = parts[1]
            identity = parts[2]
            
            # Determine status - since we don't have explicit status in the output,
            # assume agents listed are installed but not running
            status = "NOT_RUNNING"
            health = "UNKNOWN"
            not_running_count += 1
            
            # Extract just the agent type from full name
            agent_type = agent_name.split('-')[1] if '-' in agent_name else agent_name
            
            agents.append({
                'uuid': uuid,
                'name': agent_name,
                'type': agent_type,
                'identity': identity,
                'status': status,
                'health': health
            })
    
    if not agents:
        return "I'm running but don't see any agents right now."
    
    # Create conversational summary
    agent_count = len(agents)
    if agent_count == 1:
        agent = agents[0]
        if agent['status'] == 'RUNNING':
            return f"I've got 1 agent running - my {agent['type']} agent. It's working fine!"
        else:
            return f"I have 1 agent installed - the {agent['type']} agent - but it's not running right now. Want me to start it?"
    else:
        agent_types = [agent['type'] for agent in agents]
        
        if not_running_count == agent_count:
            agent_list = ", ".join(agent_types[:-1]) + f" and {agent_types[-1]}" if len(agent_types) > 1 else agent_types[0]
            return f"I have {agent_count} agents installed ({agent_list}) but none of them are running. Should I start them up?"
        elif running_count == agent_count:
            agent_list = ", ".join(agent_types[:-1]) + f" and {agent_types[-1]}" if len(agent_types) > 1 else agent_types[0]
            if bad_health_count > 0:
                return f"I've got {agent_count} agents running ({agent_list}), but {bad_health_count} of them seem to be having issues. Want me to check what's wrong?"
            else:
                return f"All {agent_count} agents are running great! ({agent_list})"
        else:
            return f"I have {agent_count} agents - {running_count} running and {not_running_count} stopped. The running ones are working fine!"

def make_status_readable(status_output):
    """Convert vctl status output to more readable format."""
    if not status_output:
        return "No agents running"
    
    lines = status_output.strip().split('\n')
    if len(lines) < 2:
        return status_output
    
    header = lines[0]
    result_lines = []
    
    # Always add a clear header
    result_lines.append("UUID   AGENT                      IDENTITY             STATUS       HEALTH")
    
    # Process each agent line
    for line in lines[1:]:
        if not line.strip():
            continue
            
        # Parse the line - handle the case where STATUS/HEALTH columns are empty
        parts = line.split()
        if len(parts) >= 3:  # UUID, AGENT, IDENTITY at minimum
            uuid = parts[0]
            agent = parts[1]
            identity = parts[2] if len(parts) > 2 else ""
            
            # Check if there are more parts that might be tag, priority, status, health
            tag = parts[3] if len(parts) > 3 and parts[3] else ""
            priority = parts[4] if len(parts) > 4 and parts[4] else ""
            status = parts[5] if len(parts) > 5 and parts[5] else ""
            health = parts[6] if len(parts) > 6 and parts[6] else ""
            
            # Determine readable status
            readable_status = "NOT_RUNNING"  # Default assumption for installed agents
            readable_health = "UNKNOWN"
            
            # Convert status codes
            if status:
                if status.upper() in ["RUNNING", "STARTED", "ACTIVE"] or status == "1":
                    readable_status = "RUNNING"
                elif status.upper() in ["STOPPED", "INACTIVE", "DISABLED"] or status == "0":
                    readable_status = "STOPPED"
                elif status:
                    readable_status = status.upper()
            
            # Convert health codes  
            if health:
                if health.upper() in ["GOOD", "OK", "HEALTHY"] or health == "1":
                    readable_health = "GOOD"
                elif health.upper() in ["BAD", "ERROR", "UNHEALTHY"] or health == "0":
                    readable_health = "BAD"
                elif health:
                    readable_health = health.upper()
            
            # Format the line with consistent spacing
            formatted_line = f"{uuid:<6} {agent:<26} {identity:<20} {readable_status:<12} {readable_health}"
            result_lines.append(formatted_line)
        else:
            # If we can't parse it, keep the original line
            result_lines.append(line)
    
    return '\n'.join(result_lines)

def vctl_status_detailed():
    """Get detailed VOLTTRON agent status with explanations."""
    return vctl_status(explain=True)

def check_volttron_status(brief=True):
    """Check VOLTTRON status and show recent log entries."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Get status
        result = subprocess.run(
            [vctl_cmd, "status"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home
        )
        
        status_output = result.stdout or result.stderr or "No status output"
        
        if brief:
            # Just show platform status briefly
            if result.returncode == 0:
                if status_output.strip():
                    return f"✅ VOLTTRON platform is running with agents active."
                else:
                    return f"🟡 VOLTTRON platform is running but no agents are active."
            else:
                return f"❌ VOLTTRON platform is not running."
        else:
            # Show detailed status with logs
            log_entries = read_volttron_log(5)  # Last 5 lines
            return f"VOLTTRON Platform Status:\n{status_output}\n\nRecent Log Entries:\n{log_entries}"
    except Exception as e:
        return f"Error checking VOLTTRON status: {str(e)}"

def vctl_list_agents():
    """List all installed agents with their details."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Get list of agents (same as status but with explanation)
        result = subprocess.run(
            [vctl_cmd, "list"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if not output:
                return "📋 No agents are currently installed."
            return f"📋 Installed Agents:\n\n{output}"
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return f"❌ Error listing agents: {error_msg}"
    except Exception as e:
        return f"Error running vctl list: {str(e)}"

def vctl_start_agent(agent_uuid_or_tag):
    """Start a specific agent by UUID or tag."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        if not agent_uuid_or_tag:
            return "❌ Please specify an agent UUID or tag to start. Use 'vctl status' to see available agents."
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Start the specific agent
        result = subprocess.run(
            [vctl_cmd, "start", agent_uuid_or_tag], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home
        )
        
        if result.returncode == 0:
            return f"✅ Agent '{agent_uuid_or_tag}' started successfully."
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return f"❌ Error starting agent '{agent_uuid_or_tag}': {error_msg}"
    except Exception as e:
        return f"Error starting agent: {str(e)}"

def vctl_stop_agent(agent_uuid_or_tag):
    """Stop a specific agent by UUID or tag."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        if not agent_uuid_or_tag:
            return "❌ Please specify an agent UUID or tag to stop. Use 'vctl status' to see running agents."
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Stop the specific agent
        result = subprocess.run(
            [vctl_cmd, "stop", agent_uuid_or_tag], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home
        )
        
        if result.returncode == 0:
            return f"🛑 Agent '{agent_uuid_or_tag}' stopped successfully."
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return f"❌ Error stopping agent '{agent_uuid_or_tag}': {error_msg}"
    except Exception as e:
        return f"Error stopping agent: {str(e)}"

def vctl_health():
    """Get health status of all agents."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # First get the list of agents
        status_result = subprocess.run(
            [vctl_cmd, "status"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home
        )
        
        if status_result.returncode != 0:
            return "I can't check my health right now - I might not be running. Want to start me up?"
        
        status_output = status_result.stdout.strip()
        if not status_output:
            return "I'm running but don't have any agents to check the health of. Everything's fine though!"
        
        # Parse agent list and check health for each
        lines = status_output.strip().split('\n')
        health_reports = []
        
        for line in lines[1:]:  # Skip header
            if not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 3:
                uuid = parts[0]
                agent_name = parts[1]
                
                # Try to get health for this agent using UUID
                health_result = subprocess.run(
                    [vctl_cmd, "health", "--uuid", uuid], 
                    capture_output=True, 
                    text=True,
                    env=env,
                    cwd=volttron_home
                )
                
                agent_type = agent_name.split('-')[1] if '-' in agent_name else agent_name
                
                if health_result.returncode == 0:
                    health_output = health_result.stdout.strip()
                    if health_output:
                        health_reports.append(f"• {agent_type} agent (UUID {uuid}): {health_output}")
                    else:
                        health_reports.append(f"• {agent_type} agent (UUID {uuid}): No health data available")
                else:
                    # Agent might not be running or have health monitoring
                    health_reports.append(f"• {agent_type} agent (UUID {uuid}): Not running or no health monitoring")
        
        if not health_reports:
            return "I have agents installed but none are reporting health status. They might not be running."
        
        # Create conversational health summary
        problem_agents = []
        good_agents = []
        
        for report in health_reports:
            if "No health data" in report or "Not running" in report or "error" in report.lower():
                problem_agents.append(report)
            else:
                good_agents.append(report)
        
        summary = []
        if good_agents:
            summary.append(f"Good news! {len(good_agents)} of my agents are reporting healthy:")
            summary.extend(good_agents)
        
        if problem_agents:
            summary.append(f"\nI'm having issues with {len(problem_agents)} agents:")
            summary.extend(problem_agents)
            summary.append("\nWant me to try restarting the problematic ones?")
        
        if not problem_agents and good_agents:
            summary.append("\nEverything looks great! All my agents are healthy.")
        
        return "\n".join(summary)
        
    except Exception as e:
        return f"I ran into trouble checking my health: {str(e)}"

def read_volttron_log(num_lines=10):
    """Read the last N lines from the VOLTTRON log file and interpret them conversationally."""
    try:
        volttron_home = get_volttron_home()
        log_file_path = os.path.join(volttron_home, "volttron.log")
        
        if not os.path.exists(log_file_path):
            return "I don't have any logs yet - probably just started up!"
        
        # Read last N lines
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-num_lines:] if len(lines) >= num_lines else lines
            raw_logs = ''.join(recent_lines).strip()
        
        # Interpret the logs conversationally
        interpreted_logs = interpret_logs_conversationally(raw_logs)
        
        return interpreted_logs
    except Exception as e:
        return f"I'm having trouble reading my own logs: {str(e)}"

def interpret_logs_conversationally(raw_logs):
    """Convert technical log entries into conversational summaries."""
    if not raw_logs:
        return "My logs are empty - I've been pretty quiet!"
    
    lines = raw_logs.strip().split('\n')
    activities = []
    
    # Count different types of activities
    connections = 0
    disconnections = 0
    rpc_calls = 0
    control_activities = 0
    errors = 0
    
    recent_activity = []
    
    for line in lines:
        if 'ACCEPTED' in line or 'HANDSHAKE_SUCCEEDED' in line:
            connections += 1
        elif 'DISCONNECTED' in line:
            disconnections += 1
        elif 'CONTROL RPC' in line:
            rpc_calls += 1
            if 'list_agents' in line:
                control_activities += 1
        elif 'ERROR' in line or 'WARN' in line:
            errors += 1
        
        # Extract timestamp for recent activity context
        if line.strip():
            try:
                # Extract just the time part
                if '2025-' in line:
                    time_part = line.split(' ')[1].split(',')[0]  # Get HH:MM:SS
                    recent_activity.append(time_part)
            except:
                pass
    
    # Create conversational summary
    summary_parts = []
    
    if connections > 0:
        summary_parts.append(f"I've been busy handling {connections} connection{'s' if connections != 1 else ''}")
    
    if control_activities > 0:
        summary_parts.append(f"Someone's been asking me about my agents {control_activities} time{'s' if control_activities != 1 else ''}")
    
    if rpc_calls > 0:
        summary_parts.append(f"I processed {rpc_calls} command{'s' if rpc_calls != 1 else ''}")
    
    if disconnections > 0:
        summary_parts.append(f"Had {disconnections} client{'s' if disconnections != 1 else ''} disconnect")
    
    if errors > 0:
        summary_parts.append(f"⚠️ I encountered {errors} error{'s' if errors != 1 else ''} - might want to check that out")
    
    if not summary_parts:
        summary_parts.append("I've been running quietly - not much exciting happening")
    
    # Add time context if available
    time_context = ""
    if recent_activity:
        if len(recent_activity) > 1:
            time_context = f"\n\nMost recent activity was around {recent_activity[-1]}."
        else:
            time_context = f"\n\nLast activity was at {recent_activity[0]}."
    
    main_summary = f"Here's what I've been up to recently:\n\n• " + "\n• ".join(summary_parts) + time_context
    
    # Add raw logs for technical users who want details
    main_summary += f"\n\n💻 **Technical Details** (if you need them):\n```\n{raw_logs}\n```"
    
    return main_summary

def get_volttron_installation_help():
    """Provide installation instructions for VOLTTRON."""
    return """
🤖 Hey there! I don't see VOLTTRON installed on your system yet.

VOLTTRON is the IoT platform that lets you control smart building devices, collect sensor data, and run automation agents. Think of it as the brain that connects and manages all your smart devices!

📦 **Quick Setup** (2 minutes):
```
pip install volttron
export VOLTTRON_HOME=~/.volttron
vcfg
```

That's it! Then you can start it with: `volttron -vv -l volttron.log &`

💡 **Want more detailed instructions?** Just ask me:
   • "Show me the detailed VOLTTRON installation steps"
   • "How do I install VOLTTRON from source?"
   • "What is VOLTTRON_HOME?"

Once it's installed, you can chat with me to control VOLTTRON using commands like:
   • "Start VOLTTRON" 
   • "Show me the agent status"
   • "Stop all agents"

Ready to get started? 🚀
"""

def get_detailed_installation_help():
    """Provide detailed installation instructions for VOLTTRON."""
    return """
🔧 **Detailed VOLTTRON Installation Guide**
==========================================

🎯 **What is VOLTTRON?**
VOLTTRON is an open-source platform for distributed sensing and control. It helps you:
• Connect to smart building devices (thermostats, sensors, meters)
• Collect and analyze energy data
• Run automated control algorithms
• Integrate with cloud services

📦 **Method 1: Quick Install (Recommended)**
-------------------------------------------
```bash
# Install from PyPI (easiest way)
pip install volttron

# Set up your workspace
export VOLTTRON_HOME=~/.volttron

# Configure VOLTTRON (interactive setup)
vcfg

# Start the platform
volttron -vv -l volttron.log &
```

🛠️ **Method 2: Developer Install**
----------------------------------
If you want to modify VOLTTRON or install from source:

```bash
# Clone the repository
git clone https://github.com/VOLTTRON/volttron.git
cd volttron

# Create virtual environment
python3 -m venv env
source env/bin/activate

# Install in development mode
pip install -e .

# Set up environment
export VOLTTRON_HOME=~/.volttron

# Configure and start
vcfg
volttron -vv -l volttron.log &
```

🏠 **What is VOLTTRON_HOME?**
This is where VOLTTRON stores:
• Configuration files
• Agent installations  
• Log files
• Security certificates
• Database files

📚 **Need More Help?**
• Official docs: https://volttron.readthedocs.io
• GitHub: https://github.com/VOLTTRON/volttron
• Community: https://volttron.org

✅ **After Installation:**
Once installed, come back and chat with me! I can help you:
• Start and stop the platform
• Install and manage agents
• Check system status
• View logs and troubleshoot

Questions? Just ask! 😊
"""

def show_formatting_test():
    """Show a test of the improved formatting capabilities."""
    return """
🧪 FORMATTING TEST - This shows the improved display formatting:

📋 VOLTTRON Agent Status Example:
================================
UUID   AGENT                      IDENTITY             TAG PRIORITY STATUS    HEALTH
0      volttron-listener-2.0.0rc3 default-listener-vip     50      RUNNING   GOOD
1      platform-driver-4.1.0     platform.driver          40      STOPPED   UNKNOWN
2      actuator-1.0              platform.actuator        30      RUNNING   GOOD

📊 Key Information:
------------------
• UUID: Unique identifier for each agent instance
• AGENT: The agent name and version number  
• IDENTITY: How the agent identifies itself on the VIP message bus
• TAG: Optional user-defined tag for easier identification
• PRIORITY: Startup priority (lower numbers start first)
• STATUS: Current state (RUNNING, STOPPED, STARTING, etc.)
• HEALTH: Health status (GOOD, BAD, UNKNOWN)

💡 Available Commands:
---------------------
• "vctl status" - Show current agent status
• "start agent [UUID]" - Start a specific agent
• "stop agent [UUID]" - Stop a specific agent  
• "list agents" - Show all installed agents
• "check health" - Show agent health information
• "start volttron" - Start the VOLTTRON platform
• "stop volttron" - Stop the VOLTTRON platform

✅ Formatting test complete! The text above should display with:
   • Proper line breaks and spacing
   • Monospace font for tables and code
   • Clear section headers and bullets
   • Preserved indentation and alignment
"""

def get_volttron_next_steps():
    """Provide conversational next steps after VOLTTRON is started."""
    return """
🎉 **Awesome! VOLTTRON is up and running!** 

Hey there! So you've got me started - that's fantastic! 🚀 Now let's get you set up with some cool stuff to do. Think of this as your first day with a new smart home system!

## � **First thing - let's see what's going on with me:**

Want to check how I'm feeling? Just ask me **"How are you doing?"** or **"Show me your status"** and I'll tell you what agents I have and how they're doing!

## 🎯 **Next up - let's get you a listener agent:**

This is like getting your first smart device! The listener agent is super helpful - it watches all the messages flowing through me and can help you understand what's happening.

Just say something like:
- **"Can you install a listener agent for me?"**
- **"I want to add a listener"**
- **"Help me get a listener going"**

And I'll take care of the installation for you! No need to remember complicated commands 😊

## 🏥 **Then we'll do a health check:**

Once we get that set up, I can show you how to check that all my agents are happy and healthy. It's like taking my temperature!

## 🎮 **What else can we explore?**

After that, you can ask me to:
- **"Show me all my agents"** - See your whole agent family
- **"Start this agent"** or **"Stop that agent"** - Control individual agents  
- **"What's in your logs?"** - See what I've been up to lately
- **"How do I shut you down properly?"** - When you're done for the day

## � **The best part?**

You don't need to remember any technical commands! Just chat with me naturally and I'll figure out what you want to do. I'm here to make VOLTTRON easy and fun! 

**Ready to dive in? What would you like to try first?** 🌟
"""

def check_volttron_installation():
    """Check if VOLTTRON is installed and provide helpful feedback."""
    volttron_cmd = find_volttron_command()
    vctl_cmd = find_vctl_command()
    
    if volttron_cmd and vctl_cmd:
        return f"""
🎉 Great news! VOLTTRON is installed and ready to go!

📍 **Found VOLTTRON at:**
   • Platform: {volttron_cmd}
   • Control tool: {vctl_cmd}

✅ You can now use commands like:
   • "Start VOLTTRON"
   • "Show me the agent status" 
   • "List all agents"

Ready to control your IoT platform? Just ask! 🚀
"""
    elif volttron_cmd:
        return f"""
⚠️ **Found VOLTTRON but something's missing...**

✅ Platform found: {volttron_cmd}
❌ Control tool (vctl) not found

This usually means your VOLTTRON installation is incomplete. Try reinstalling VOLTTRON or check your installation.
"""
    elif vctl_cmd:
        return f"""
⚠️ **Found VOLTTRON control tool but missing the main platform...**

✅ Control tool found: {vctl_cmd}  
❌ Main platform (volttron) not found

This usually means your VOLTTRON installation is incomplete. Try reinstalling VOLTTRON or check your installation.
"""
    else:
        return get_volttron_installation_help()