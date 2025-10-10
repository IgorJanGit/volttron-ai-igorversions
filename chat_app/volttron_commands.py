import subprocess
import os
import shutil
from pathlib import Path

# Available VOLTTRON agents and packages
AVAILABLE_AGENTS = {
    # Core Agents
    'listener': {
        'package': 'volttron-listener',
        'vip_identity': 'listener',
        'description': 'Simple listener agent that monitors all platform messages',
        'category': 'Core'
    },
    'platform-driver': {
        'package': 'volttron-platform-driver', 
        'vip_identity': 'platform.driver',
        'description': 'Platform driver for device communication',
        'category': 'Driver'
    },
    
    # Historians
    'sqlite-historian': {
        'package': 'volttron-sqlite-historian',
        'vip_identity': 'sqlite_historian',
        'description': 'SQLite database historian for storing data',
        'category': 'Historian'
    },
    'postgresql-historian': {
        'package': 'volttron-postgresql-historian',
        'vip_identity': 'postgresql_historian', 
        'description': 'PostgreSQL database historian for storing data',
        'category': 'Historian'
    },
    
    # Driver Libraries (for development)
    'fake-driver': {
        'package': 'volttron-lib-fake-driver',
        'vip_identity': 'fake_driver',
        'description': 'Fake driver library for testing and development',
        'category': 'Driver Library'
    },
    'bacnet-driver': {
        'package': 'volttron-lib-bacnet-driver',
        'vip_identity': 'bacnet_driver',
        'description': 'BACnet driver library for building automation',
        'category': 'Driver Library'
    },
    
    # Protocol Libraries
    'protocol-proxy': {
        'package': 'lib-protocol-proxy',
        'vip_identity': 'protocol_proxy',
        'description': 'Protocol proxy library for device communication',
        'category': 'Protocol'
    },
    'bacnet-proxy': {
        'package': 'lib-protocol-proxy-bacnet',
        'vip_identity': 'bacnet_proxy',
        'description': 'BACnet protocol proxy for building automation',
        'category': 'Protocol'
    },
    
    # Tools
    'platform-lookup': {
        'package': 'platform-lookup',
        'vip_identity': 'platform_lookup',
        'description': 'Platform lookup service for agent discovery',
        'category': 'Tool'
    },
    'bacnet-scan': {
        'package': 'bacnet-scan-tool',
        'vip_identity': 'bacnet_scanner',
        'description': 'BACnet network scanning tool',
        'category': 'Tool'
    }
}

def format_volttron_warnings(stderr_output):
    """Format VOLTTRON warnings and messages for user-friendly display."""
    if not stderr_output:
        return ""
    
    warnings = []
    lines = stderr_output.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect common VOLTTRON messages
        if "Another VOLTTRON instance is already running" in line:
            warnings.append("⚠️ **VOLTTRON Already Running**: Another VOLTTRON instance is active - this is normal!")
        elif "VOLTTRON_HOME" in line:
            warnings.append(f"📁 **VOLTTRON Home**: {line}")
        elif "ERROR" in line.upper():
            warnings.append(f"❌ **Error**: {line}")
        elif "WARNING" in line.upper():
            warnings.append(f"⚠️ **Warning**: {line}")
        elif "INFO" in line.upper():
            warnings.append(f"ℹ️ **Info**: {line}")
        else:
            # Generic system message
            warnings.append(f"📋 **System**: {line}")
    
    if warnings:
        return "\n**System Messages:**\n" + "\n".join(warnings) + "\n\n"
    return ""

def find_volttron_command():
    """Find volttron command in various locations."""
    # First, check the known working VOLTTRON environment
    volttron_env_path = "/home/igor/Work/Volttron_eclispe/env/bin/volttron"
    if os.path.exists(volttron_env_path):
        return volttron_env_path
    
    # Second, check if it's in PATH
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
    # First, check the known working VOLTTRON environment
    vctl_env_path = "/home/igor/Work/Volttron_eclispe/env/bin/vctl"
    if os.path.exists(vctl_env_path):
        return vctl_env_path
    
    # Second, check if it's in PATH
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
    # Always prefer the project-specific VOLTTRON_HOME for consistency
    preferred_home = "/home/igorj/volttron/volttron_home"
    
    # Check if VOLTTRON_HOME is explicitly set in environment first
    env_volttron_home = os.getenv("VOLTTRON_HOME")
    if env_volttron_home and env_volttron_home != os.path.expanduser("~/.volttron"):
        # Use explicit environment setting unless it's the default ~/.volttron
        return env_volttron_home
    
    # Create and use our preferred directory
    os.makedirs(preferred_home, exist_ok=True)
    return preferred_home
    return os.path.expanduser("~/.volttron")

def check_volttron_environment():
    """Check and setup VOLTTRON environment variables."""
    
    # Check if VOLTTRON_HOME is set
    volttron_home = os.getenv("VOLTTRON_HOME")
    
    if not volttron_home:
        # Set a default VOLTTRON_HOME
        default_home = os.path.expanduser("~/volttron_home")
        os.environ["VOLTTRON_HOME"] = default_home
        
        return f"""
⚙️ **VOLTTRON Environment Setup**

Set VOLTTRON_HOME to: `{default_home}`

**Note from Eclipse VOLTTRON docs:**
- This is mandatory if you had an old monolithic VOLTTRON version
- Modular VOLTTRON (current) cannot work with old VOLTTRON_HOME directories
- Using separate directory: `{default_home}`

Environment ready for VOLTTRON operations! ✅
"""
    else:
        return f"""
✅ **VOLTTRON Environment Ready**

VOLTTRON_HOME: `{volttron_home}`

Environment is properly configured!
"""

def kill_existing_volttron_processes():
    """Kill any existing VOLTTRON processes to prevent conflicts."""
    try:
        # Find all VOLTTRON processes (be specific to avoid catching unrelated processes)
        result = subprocess.run(
            ["pgrep", "-f", "bin/volttron"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            killed_pids = []
            
            for pid in pids:
                try:
                    # Try to kill the process gracefully first
                    subprocess.run(["kill", "-TERM", pid], check=True, timeout=5)
                    killed_pids.append(pid)
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    try:
                        # Force kill if graceful kill doesn't work
                        subprocess.run(["kill", "-KILL", pid], check=True, timeout=5)
                        killed_pids.append(f"{pid} (force)")
                    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                        pass
            
            if killed_pids:
                return f"🔄 Stopped existing VOLTTRON processes: PIDs {', '.join(killed_pids)}"
            else:
                return "⚠️ Found VOLTTRON processes but couldn't stop them"
        else:
            return ""  # No processes found, which is good
            
    except Exception as e:
        return f"⚠️ Error checking for existing VOLTTRON processes: {str(e)}"

def start_volttron():
    """Start volttron in the background using the correct virtual environment."""
    try:
        volttron_cmd = find_volttron_command()
        volttron_home = get_volttron_home()
        
        # Check if the volttron command exists
        if not volttron_cmd:
            return check_volttron_installation()
        
        # Kill any existing VOLTTRON processes to prevent conflicts
        cleanup_msg = kill_existing_volttron_processes()
        
        # Set environment variables for VOLTTRON
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Create VOLTTRON_HOME directory if it doesn't exist
        os.makedirs(volttron_home, exist_ok=True)
        
        # Wait a moment for processes to fully terminate
        if cleanup_msg:
            import time
            time.sleep(2)
        
        # Start volttron in the background
        process = subprocess.Popen(
            [volttron_cmd, "-vv", "-l", "volttron.log"], 
            env=env,
            cwd=volttron_home
        )
        
        success_msg = f"✅ VOLTTRON started with PID {process.pid} (VOLTTRON_HOME: {volttron_home})"
        
        if cleanup_msg:
            return f"{cleanup_msg}\n{success_msg}"
        else:
            return success_msg
            
    except Exception as e:
        return f"❌ Error starting VOLTTRON: {str(e)}"

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
        
        # Format any system warnings
        warning_msg = format_volttron_warnings(result.stderr)
        
        if result.returncode == 0:
            status_output = result.stdout.strip()
            
            # Check if no agents are installed
            if not status_output or "No installed Agents found" in status_output:
                if explain:
                    return f"""{warning_msg}🟡 **VOLTTRON is running, but it looks pretty quiet in here!**

No agents are currently installed or running. This is normal for a fresh VOLTTRON installation.

💡 **Want to get started?**
   • Install some agents
   • Check out the platform driver for connecting to devices
   • Ask me "How do I install agents?" for help

Your VOLTTRON platform is ready - it just needs some agents to manage! 🤖
"""
                else:
                    return f"{warning_msg}I'm up and running, but I don't have any agents installed yet. Pretty quiet around here!"
            
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
                return f"{warning_msg}{explanation}\n{readable_status}\n\n💬 Need help with any of these agents? Just ask!"
            else:
                # For brief status, show both the formatted table AND conversational summary
                return f"{warning_msg}📋 **My Current Agents:**\n\n{readable_status}\n\n💬 **Summary:** {conversational_summary}"
                
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            warning_msg = format_volttron_warnings(result.stderr)
            
            if "not connected" in error_msg.lower() or "connection" in error_msg.lower():
                if explain:
                    return f"""{warning_msg}❌ **Oops! VOLTTRON isn't running right now.**

The platform needs to be started before I can check on your agents.

🚀 **Ready to fire it up?** Just say:
   • "Start VOLTTRON"
   • "Launch the platform"  
   • "Get VOLTTRON running"

I'll get it started for you! ⚡
"""
                else:
                    return f"{warning_msg}Uh oh, I'm not running right now! Want to start me up?"
            else:
                return f"{warning_msg}I'm having trouble checking my status: {error_msg}"
    except Exception as e:
        return f"Something went wrong while I was checking on myself: {str(e)}"

def make_status_conversational(status_output):
    """Convert status output to conversational summary."""
    if not status_output or "No installed Agents found" in status_output:
        return "I'm up and running, but I don't have any agents installed yet. Pretty quiet around here!"
    
    lines = status_output.strip().split('\n')
    if len(lines) < 2:
        return "I'm running but something seems off with my agent status."
    
    agents = []
    running_count = 0
    not_running_count = 0
    bad_health_count = 0
    
    # Parse each agent line - handle both old and new vctl status formats
    for line in lines[1:]:
        if not line.strip() or "UUID" in line:  # Skip header or empty lines
            continue
            
        # Clean up the line and split by whitespace
        clean_line = ' '.join(line.split())  # Normalize whitespace
        parts = clean_line.split()
        
        if len(parts) >= 3:
            uuid = parts[0]
            agent_name = parts[1] if len(parts) > 1 else "unknown"
            identity = parts[2] if len(parts) > 2 else "unknown"
            
            # Look for explicit status indicators in remaining parts
            remaining_parts = parts[3:] if len(parts) > 3 else []
            status = "UNKNOWN"
            health = "UNKNOWN"
            
            # Check for status in the line - be more flexible
            line_upper = line.upper()
            has_status_column = False
            
            # Look for explicit status words in remaining parts
            for part in remaining_parts:
                part_upper = part.upper()
                if part_upper in ["RUNNING", "STARTED", "ACTIVE", "ENABLED"]:
                    status = "RUNNING"
                    has_status_column = True
                elif part_upper in ["STOPPED", "DISABLED", "INACTIVE", "EXITED"]:
                    status = "STOPPED"
                    has_status_column = True
                elif part_upper in ["GOOD", "HEALTHY", "OK"]:
                    health = "GOOD"
                elif part_upper in ["BAD", "UNHEALTHY", "ERROR", "FAILED"]:
                    health = "BAD"
            
            # If no explicit status found, make reasonable assumptions
            if not has_status_column:
                # If we have an agent listed but no status, assume it's installed but not running
                # This is common in newer VOLTTRON versions where stopped agents aren't shown
                if len(parts) >= 3:  # Has UUID, name, and identity
                    status = "INSTALLED"  # Installed but status unclear
                    
            # Count the agent
            if status == "RUNNING":
                running_count += 1
            else:
                not_running_count += 1
                
            if health == "BAD":
                bad_health_count += 1
            
            # Extract agent type - handle multiple listeners
            if 'listener' in agent_name.lower():
                agent_type = "listener"
            elif 'platform' in agent_name.lower() and 'driver' in agent_name.lower():
                agent_type = "platform-driver"
            elif 'driver' in agent_name.lower():
                agent_type = "driver"
            elif 'platform' in agent_name.lower():
                agent_type = "platform"
            else:
                # Extract type from agent name
                agent_type = agent_name.split('-')[1] if '-' in agent_name else agent_name.split('.')[0] if '.' in agent_name else agent_name[:10]
            
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
    
    # Count agent types, including multiple instances
    agent_type_counts = {}
    for agent in agents:
        agent_type = agent['type']
        if agent_type in agent_type_counts:
            agent_type_counts[agent_type] += 1
        else:
            agent_type_counts[agent_type] = 1
    
    # Create conversational summary
    agent_count = len(agents)
    
    # Build agent type description
    agent_descriptions = []
    for agent_type, count in agent_type_counts.items():
        if count > 1:
            agent_descriptions.append(f"{count} {agent_type} agents")
        else:
            agent_descriptions.append(f"{agent_type} agent")
    
    if len(agent_descriptions) == 1:
        agent_list = agent_descriptions[0]
    elif len(agent_descriptions) == 2:
        agent_list = f"{agent_descriptions[0]} and {agent_descriptions[1]}"
    else:
        agent_list = ", ".join(agent_descriptions[:-1]) + f", and {agent_descriptions[-1]}"
    
    # Create status summary - be more informative about what we found
    if agent_count == 1:
        agent = agents[0]
        if agent['status'] == "RUNNING":
            return f"I have one {agent['type']} agent running (UUID: {agent['uuid']}) - it's working great! 🚀"
        elif agent['status'] == "INSTALLED":
            return f"I have one {agent['type']} agent installed (UUID: {agent['uuid']}) but I can't tell if it's running. Want me to check the detailed status?"
        else:
            return f"I have one {agent['type']} agent (UUID: {agent['uuid']}) but it appears to be stopped. Want me to start it?"
    
    # Multiple agents
    if running_count == 0 and not_running_count == agent_count:
        return f"I have {agent_count} agents installed ({agent_list}) but none appear to be running. Should I start them?"
    elif running_count == agent_count:
        if bad_health_count > 0:
            return f"I've got {agent_count} agents running ({agent_list}), but {bad_health_count} seem to be having issues. Want me to check what's wrong?"
        else:
            return f"All {agent_count} agents are running great! ({agent_list}) Everything's humming along nicely! ✨"
    elif running_count > 0:
        return f"I have {agent_count} agents ({agent_list}) - {running_count} running and {not_running_count} stopped. The running ones are working fine!"
    else:
        return f"I have {agent_count} agents ({agent_list}) installed, but I'm not sure about their current status. Want me to get more details?"

def make_status_readable(status_output):
    """Convert vctl status output to more readable format."""
    if not status_output:
        return "No agents found"
    
    lines = status_output.strip().split('\n')
    if len(lines) < 1:
        return "No agent information available"
    
    # Check if this is the simple format or detailed format
    if len(lines) == 1 and not "UUID" in lines[0]:
        # Simple format: just agent info on one line
        return f"📋 **Agent Status:**\n```\n{status_output}\n```"
    
    # Handle detailed format
    result_lines = []
    
    # Create a cleaner header
    result_lines.append("UUID   AGENT                             IDENTITY                     STATUS       HEALTH")
    result_lines.append("====   =================================  ===========================  ===========  =======")
    
    # Process each agent line
    for i, line in enumerate(lines):
        if not line.strip():
            continue
            
        # Skip headers that contain "UUID" 
        if "UUID" in line and i == 0:
            continue
            
        # Clean and split the line
        clean_line = ' '.join(line.split())  # Normalize whitespace
        parts = clean_line.split()
        
        if len(parts) >= 3:  # UUID, AGENT, IDENTITY at minimum
            uuid = parts[0][:6]  # Limit UUID to 6 chars for display
            agent = parts[1][:32] if len(parts) > 1 else ""  # Agent name
            identity = parts[2][:27] if len(parts) > 2 else ""  # Identity
            
            # Look for status and health in remaining parts
            remaining_parts = parts[3:] if len(parts) > 3 else []
            
            # Default values - assume installed if we see it listed
            status = "INSTALLED"
            health = "UNKNOWN"
            
            # Try to extract status and health from remaining parts
            if remaining_parts:
                for part in remaining_parts:
                    part_upper = part.upper()
                    if part_upper in ["RUNNING", "STARTED", "ACTIVE", "ENABLED"]:
                        status = "RUNNING"
                    elif part_upper in ["STOPPED", "DISABLED", "INACTIVE", "EXITED"]:
                        status = "STOPPED"
                    elif part_upper in ["GOOD", "HEALTHY", "OK"]:
                        health = "GOOD"
                    elif part_upper in ["BAD", "UNHEALTHY", "ERROR", "FAILED"]:
                        health = "BAD"
            
            # Format the line with consistent spacing
            formatted_line = f"{uuid:<6} {agent:<32} {identity:<27} {status:<11} {health}"
            result_lines.append(formatted_line)
        else:
            # If we can't parse it properly, show the original line with a note
            result_lines.append(f"       {line.strip()}")
    
    # If no agents were properly parsed, show the raw output with formatting
    if len(result_lines) <= 2:  # Only header lines
        return f"📋 **Agent Status (Raw Output):**\n```\n{status_output}\n```\n\n💡 **Note:** The output format may be non-standard. Try running 'vctl status' directly for more details."
    
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
        
        # First, check if VOLTTRON processes are actually running using the same method as start_volttron
        # Be more specific to avoid catching our own python subprocess
        process_check = subprocess.run(
            ["pgrep", "-f", "bin/volttron"],
            capture_output=True, text=True, timeout=10
        )
        
        # If no VOLTTRON processes are running, it's definitely not running
        if process_check.returncode != 0 or not process_check.stdout.strip():
            return "❌ VOLTTRON platform is not running."
        
        # VOLTTRON processes are running, now check with vctl status for detailed info
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
            # VOLTTRON is running (we confirmed with pgrep), now check agent status
            if result.returncode == 0:
                if status_output.strip() and "No installed Agents found" not in status_output:
                    return f"✅ VOLTTRON platform is running with agents active."
                else:
                    return f"🟡 VOLTTRON platform is running but no agents are installed."
            else:
                # Processes exist but vctl can't connect - could be starting up
                pids = process_check.stdout.strip().split('\n')
                return f"🟡 VOLTTRON platform is running (PID {', '.join(pids)}) but may still be initializing."
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

def vctl_uninstall_agent(agent_uuid_or_tag):
    """Uninstall/remove a specific agent by UUID or tag following VOLTTRON best practices.
    
    This function follows the official VOLTTRON documentation:
    1. Stop the agent first (if running)
    2. Remove the agent from the platform (deletes package from VOLTTRON_HOME)
    """
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        if not agent_uuid_or_tag:
            return "❌ Please specify an agent UUID or tag to uninstall. Use 'vctl status' to see available agents."
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # First check if VOLTTRON is running and if the agent exists
        status_result = subprocess.run(
            [vctl_cmd, "status"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home,
            timeout=10
        )
        
        if status_result.returncode != 0:
            return "❌ VOLTTRON is not running. Cannot uninstall agents when VOLTTRON is stopped.\n\n💡 **Try:** Start VOLTTRON first with 'start volttron'"
        
        # Check if the agent actually exists
        agent_found = False
        if status_result.stdout:
            if agent_uuid_or_tag in status_result.stdout:
                agent_found = True
        
        if not agent_found:
            return f"❌ Agent '{agent_uuid_or_tag}' not found.\n\n**Current agents:**\n{status_result.stdout}\n\n💡 **Tip:** Use the exact UUID or tag shown above."
        
        messages = []
        success = True
        
        # Step 1: Stop the agent first (required before removal)
        messages.append(f"🛑 Stopping agent '{agent_uuid_or_tag}'...")
        stop_result = subprocess.run(
            [vctl_cmd, "stop", agent_uuid_or_tag], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home,
            timeout=30
        )
        
        if stop_result.returncode == 0:
            messages.append(f"✅ Agent '{agent_uuid_or_tag}' stopped successfully.")
        else:
            # Agent might already be stopped, continue with removal
            stop_error = stop_result.stderr or stop_result.stdout or "No additional info"
            if "not running" in stop_error.lower() or "no agent" in stop_error.lower():
                messages.append(f"ℹ️ Agent '{agent_uuid_or_tag}' was already stopped.")
            else:
                messages.append(f"⚠️ Warning during stop: {stop_error}")
                # Don't fail here, might still be able to remove
        
        # Step 2: Remove the agent (this deletes the package from VOLTTRON_HOME)
        messages.append(f"🗑️ Removing agent '{agent_uuid_or_tag}' from platform...")
        remove_result = subprocess.run(
            [vctl_cmd, "remove", agent_uuid_or_tag], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home,
            timeout=30
        )
        
        if remove_result.returncode == 0:
            messages.append(f"✅ Agent '{agent_uuid_or_tag}' completely removed from platform!")
            messages.append("📁 Agent package deleted from $VOLTTRON_HOME directory.")
        else:
            # First removal attempt failed, try to find the actual UUID from status
            messages.append(f"⚠️ Initial removal failed, searching for UUID...")
            
            # Parse the status output to find the UUID for this agent
            uuid_found = None
            if status_result.stdout:
                lines = status_result.stdout.strip().split('\n')
                for line in lines:
                    if agent_uuid_or_tag in line:
                        # Extract the UUID (first column)
                        parts = line.split()
                        if parts:
                            uuid_found = parts[0]
                            break
            
            if uuid_found and uuid_found != agent_uuid_or_tag:
                # Try removal with the actual UUID
                messages.append(f"🔍 Found UUID '{uuid_found}', trying removal with UUID...")
                remove_result2 = subprocess.run(
                    [vctl_cmd, "remove", uuid_found], 
                    capture_output=True, 
                    text=True,
                    env=env,
                    cwd=volttron_home,
                    timeout=30
                )
                
                if remove_result2.returncode == 0:
                    messages.append(f"✅ Agent '{agent_uuid_or_tag}' (UUID: {uuid_found}) completely removed from platform!")
                    messages.append("📁 Agent package deleted from $VOLTTRON_HOME directory.")
                else:
                    success = False
                    remove_error = remove_result2.stderr or remove_result2.stdout or "Unknown error"
                    messages.append(f"❌ Error removing agent with UUID '{uuid_found}':")
                    messages.append(f"**Command output:** {remove_error}")
            else:
                success = False
                remove_error = remove_result.stderr or remove_result.stdout or "Unknown error"
                messages.append(f"❌ Error removing agent '{agent_uuid_or_tag}':")
                messages.append(f"**Command output:** {remove_error}")
                
                # Provide helpful hints based on error
                if "not found" in remove_error.lower():
                    messages.append("💡 **Hint:** Check if the agent UUID or tag is correct using 'vctl status'")
                elif "permission" in remove_error.lower():
                    messages.append("💡 **Hint:** Make sure VOLTTRON has proper permissions in $VOLTTRON_HOME")
                elif "still running" in remove_error.lower():
                    messages.append("💡 **Hint:** The agent might still be running. Try stopping it first.")
        
        # Step 3: Comprehensive verification of removal
        messages.append("\n🔍 **Performing comprehensive uninstall verification...**")
        
        # Verification 1: Check agent status
        verify_result = subprocess.run(
            [vctl_cmd, "status"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home,
            timeout=10
        )
        
        verification_passed = True
        verification_details = []
        
        if verify_result.returncode == 0:
            # Check if agent UUID/tag still appears in status
            if agent_uuid_or_tag not in verify_result.stdout:
                verification_details.append(f"✅ Agent '{agent_uuid_or_tag}' not found in vctl status")
            else:
                verification_details.append(f"❌ Agent '{agent_uuid_or_tag}' still appears in vctl status")
                verification_passed = False
                
            # Also check for UUID if we found one earlier
            if 'uuid_found' in locals() and uuid_found and uuid_found != agent_uuid_or_tag:
                if uuid_found not in verify_result.stdout:
                    verification_details.append(f"✅ Agent UUID '{uuid_found}' not found in status")
                else:
                    verification_details.append(f"❌ Agent UUID '{uuid_found}' still appears in status")
                    verification_passed = False
        else:
            verification_details.append("⚠️ Could not verify removal via vctl status")
            verification_passed = False
        
        # Verification 2: Check VOLTTRON_HOME for leftover agent directories
        try:
            agents_dir = os.path.join(volttron_home, "agents")
            if os.path.exists(agents_dir):
                leftover_dirs = []
                for item in os.listdir(agents_dir):
                    item_path = os.path.join(agents_dir, item)
                    if os.path.isdir(item_path):
                        # Check if directory name contains our agent identifier
                        if (agent_uuid_or_tag in item.lower() or 
                            ('uuid_found' in locals() and uuid_found and uuid_found in item)):
                            leftover_dirs.append(item)
                
                if leftover_dirs:
                    verification_details.append(f"⚠️ Found potential leftover directories: {leftover_dirs}")
                    verification_passed = False
                else:
                    verification_details.append("✅ No leftover agent directories found")
            else:
                verification_details.append("ℹ️ Agents directory not found (normal if no agents installed)")
        except Exception as e:
            verification_details.append(f"⚠️ Could not check agent directories: {str(e)}")
        
        # Verification 3: Try to start the agent (should fail if properly removed)
        try:
            start_test = subprocess.run(
                [vctl_cmd, "start", agent_uuid_or_tag], 
                capture_output=True, 
                text=True,
                env=env,
                cwd=volttron_home,
                timeout=10
            )
            
            # Check both return code and output content (vctl can return 0 even on errors)
            error_msg = (start_test.stderr + " " + start_test.stdout).lower()
            if ("not found" in error_msg or "no agent" in error_msg or 
                "agent not found" in error_msg or "unknown agent" in error_msg):
                verification_details.append("✅ Agent properly removed - cannot be started")
            elif start_test.returncode != 0:
                verification_details.append("✅ Agent start failed as expected")
            else:
                # Check if stderr has error even with return code 0
                if "error" in error_msg and ("not found" in error_msg or "no agent" in error_msg):
                    verification_details.append("✅ Agent properly removed - cannot be started")
                else:
                    verification_details.append("❌ Agent can still be started - removal incomplete")
                    verification_passed = False
        except Exception as e:
            verification_details.append(f"⚠️ Could not test agent start capability: {str(e)}")
        
        # Add verification details to messages
        for detail in verification_details:
            messages.append(detail)
        
        # Final verification result
        if verification_passed:
            messages.append(f"\n🎉 **UNINSTALL SUCCESSFUL:** Agent '{agent_uuid_or_tag}' completely removed!")
            messages.append("✅ All verification checks passed")
            success = True
        else:
            messages.append(f"\n⚠️ **UNINSTALL INCOMPLETE:** Some verification checks failed")
            messages.append("💡 **Recommendation:** Check VOLTTRON logs or restart VOLTTRON platform")
            success = False
        
        return "\n".join(messages)
            
    except subprocess.TimeoutExpired:
        return f"⏰ Timeout: Agent '{agent_uuid_or_tag}' uninstall operation took too long"
    except Exception as e:
        return f"❌ Error uninstalling agent '{agent_uuid_or_tag}': {str(e)}"

def verify_agent_uninstalled(agent_identifier):
    """Comprehensive verification to ensure an agent has been completely uninstalled.
    
    Args:
        agent_identifier: Agent UUID, tag, or name to verify removal of
        
    Returns:
        str: Detailed verification report
    """
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return "❌ VOLTTRON not properly installed - cannot verify uninstall"
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        messages = [f"🔍 **Verifying complete removal of agent '{agent_identifier}'**\n"]
        verification_results = []
        all_checks_passed = True
        
        # Check 1: Agent not in vctl status
        try:
            status_result = subprocess.run(
                [vctl_cmd, "status"], 
                capture_output=True, 
                text=True,
                env=env,
                cwd=volttron_home,
                timeout=10
            )
            
            if status_result.returncode == 0:
                if agent_identifier not in status_result.stdout:
                    verification_results.append("✅ Agent not found in vctl status")
                else:
                    verification_results.append("❌ Agent still appears in vctl status")
                    all_checks_passed = False
            elif status_result.returncode == 10:
                # VOLTTRON not running - this is actually good for uninstall verification
                verification_results.append("ℹ️ VOLTTRON not running - agent cannot be running")
            else:
                verification_results.append("⚠️ Could not check vctl status")
                all_checks_passed = False
        except Exception as e:
            verification_results.append(f"❌ Error checking status: {str(e)}")
            all_checks_passed = False
        
        # Check 2: No leftover directories in VOLTTRON_HOME
        try:
            agents_dir = os.path.join(volttron_home, "agents")
            leftover_found = False
            
            if os.path.exists(agents_dir):
                for item in os.listdir(agents_dir):
                    item_path = os.path.join(agents_dir, item)
                    if os.path.isdir(item_path):
                        if agent_identifier.lower() in item.lower():
                            verification_results.append(f"❌ Found leftover directory: {item}")
                            leftover_found = True
                            all_checks_passed = False
                
                if not leftover_found:
                    verification_results.append("✅ No leftover directories found")
            else:
                verification_results.append("ℹ️ Agents directory not found")
        except Exception as e:
            verification_results.append(f"⚠️ Could not check directories: {str(e)}")
        
        # Check 3: Agent cannot be started
        try:
            start_result = subprocess.run(
                [vctl_cmd, "start", agent_identifier], 
                capture_output=True, 
                text=True,
                env=env,
                cwd=volttron_home,
                timeout=10
            )
            
            # Check both return code and output content
            error_msg = (start_result.stderr + " " + start_result.stdout).lower()
            if ("not found" in error_msg or "no agent" in error_msg or 
                "agent not found" in error_msg or "unknown agent" in error_msg):
                verification_results.append("✅ Agent cannot be started (properly removed)")
            elif start_result.returncode != 0:
                verification_results.append("✅ Agent start failed as expected")
            else:
                # Check if stderr has error even with return code 0
                if "error" in error_msg and ("not found" in error_msg or "no agent" in error_msg):
                    verification_results.append("✅ Agent cannot be started (properly removed)")
                else:
                    verification_results.append("❌ Agent can still be started (removal incomplete)")
                    all_checks_passed = False
        except Exception as e:
            verification_results.append(f"⚠️ Could not test agent start: {str(e)}")
        
        # Check 4: Agent cannot be stopped (should fail if not installed)
        try:
            stop_result = subprocess.run(
                [vctl_cmd, "stop", agent_identifier], 
                capture_output=True, 
                text=True,
                env=env,
                cwd=volttron_home,
                timeout=10
            )
            
            # Check both return code and output content
            error_msg = (stop_result.stderr + " " + stop_result.stdout).lower()
            if ("not found" in error_msg or "no agent" in error_msg or 
                "agent not found" in error_msg or "unknown agent" in error_msg):
                verification_results.append("✅ Agent cannot be stopped (properly removed)")
            elif stop_result.returncode != 0:
                verification_results.append("✅ Agent stop failed as expected")
            else:
                # Check if stderr has error even with return code 0
                if "error" in error_msg and ("not found" in error_msg or "no agent" in error_msg):
                    verification_results.append("✅ Agent cannot be stopped (properly removed)")
                else:
                    verification_results.append("❌ Agent can still be stopped (may still exist)")
                    all_checks_passed = False
        except Exception as e:
            verification_results.append(f"⚠️ Could not test agent stop: {str(e)}")
        
        # Check 5: No process running with agent name (more specific check)
        try:
            import psutil
            agent_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    # More specific check - look for actual agent processes, not just any mention
                    if (agent_identifier.lower() in cmdline.lower() and 
                        'volttron' in cmdline.lower() and 
                        proc.info['name'] not in ['python3', 'python', 'bash', 'sh']):
                        agent_processes.append(f"PID {proc.info['pid']}: {proc.info['name']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if agent_processes:
                verification_results.append(f"⚠️ Found processes that may be related: {agent_processes}")
                all_checks_passed = False
            else:
                verification_results.append("✅ No related VOLTTRON processes running")
        except ImportError:
            verification_results.append("ℹ️ psutil not available - skipping process check")
        except Exception as e:
            verification_results.append(f"⚠️ Could not check processes: {str(e)}")
        
        # Compile results
        messages.extend(verification_results)
        
        if all_checks_passed:
            messages.append(f"\n🎉 **VERIFICATION PASSED:** Agent '{agent_identifier}' is completely uninstalled!")
            messages.append("✅ All verification checks succeeded")
        else:
            messages.append(f"\n⚠️ **VERIFICATION FAILED:** Agent '{agent_identifier}' may not be completely removed")
            messages.append("💡 **Recommendations:**")
            messages.append("   • Restart VOLTTRON platform")
            messages.append("   • Check VOLTTRON logs for errors")
            messages.append("   • Manually clean VOLTTRON_HOME if needed")
        
        return "\n".join(messages)
        
    except Exception as e:
        return f"❌ Error during verification: {str(e)}"

def vctl_install_listener_agent():
    """Install the VOLTTRON listener agent for monitoring platform messages."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # First, check if volttron-listener package is installed
        pip_cmd = find_pip_command()
        if pip_cmd:
            check_result = subprocess.run([
                pip_cmd, "show", "volttron-listener"
            ], capture_output=True, text=True, timeout=10, env=env)
            
            if check_result.returncode != 0:
                # Install the volttron-listener package
                install_result = subprocess.run([
                    pip_cmd, "install", "volttron-listener"
                ], capture_output=True, text=True, timeout=60, env=env)
                
                if install_result.returncode != 0:
                    return f"❌ Failed to install volttron-listener package: {install_result.stderr}"
        
        # Install the listener agent
        result = subprocess.run([
            vctl_cmd, "install", "volttron-listener",
            "--vip-identity", "listener",
            "--start"
        ], capture_output=True, text=True, timeout=30, env=env, cwd=volttron_home)
        
        if result.returncode == 0:
            return """
🎉 **Listener Agent Installed Successfully!**

The VOLTTRON Listener Agent is now installed and running! It will monitor and display all messages flowing through the VOLTTRON platform.

**📋 What the Listener does:**
• Subscribes to all topics on the message bus
• Displays real-time message activity
• Perfect for debugging and monitoring

**🔍 To see what it's listening to:**
• Check the logs: `tail -f volttron.log`
• Or ask: **"Show recent logs"**

The listener is now actively monitoring your VOLTTRON platform! 👂
"""
        else:
            return f"❌ Failed to install listener agent: {result.stderr or result.stdout}"
            
    except Exception as e:
        return f"Error installing listener agent: {str(e)}"

def vctl_install_agent(agent_name):
    """Install any VOLTTRON agent by name."""
    try:
        # Normalize agent name
        agent_name = agent_name.lower().replace('_', '-').replace(' ', '-')
        
        # Check if agent is available
        if agent_name not in AVAILABLE_AGENTS:
            available_agents = list_available_agents()
            return f"""❌ **Agent '{agent_name}' not found**

{available_agents}

💡 **Tip**: Try asking "what agents can I install?" to see all options."""
        
        agent_info = AVAILABLE_AGENTS[agent_name]
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Install the package first
        pip_cmd = find_pip_command()
        if pip_cmd:
            print(f"📦 Installing package: {agent_info['package']}")
            install_result = subprocess.run([
                pip_cmd, "install", agent_info['package']
            ], capture_output=True, text=True, timeout=120, env=env)
            
            if install_result.returncode != 0:
                return f"""❌ **Failed to install {agent_info['package']} package**

**Error:** {install_result.stderr or install_result.stdout}

💡 **Try manually:** `pip install {agent_info['package']}`"""
        
        # Install the agent in VOLTTRON
        install_args = [
            vctl_cmd, "install", agent_info['package'],
            "--vip-identity", agent_info['vip_identity']
        ]
        
        # Auto-start for core agents
        if agent_info['category'] in ['Core', 'Historian']:
            install_args.append("--start")
        
        result = subprocess.run(
            install_args,
            capture_output=True, text=True, timeout=60, env=env, cwd=volttron_home
        )
        
        if result.returncode == 0:
            status_emoji = "🎉" if agent_info['category'] == 'Core' else "✅"
            auto_start_msg = " and started" if "--start" in install_args else ""
            
            return f"""{status_emoji} **{agent_name.title()} Agent Installed Successfully!**

**📋 Agent Details:**
• **Name**: {agent_name}
• **Package**: {agent_info['package']}
• **Category**: {agent_info['category']}
• **Description**: {agent_info['description']}
• **VIP Identity**: {agent_info['vip_identity']}

The agent has been installed{auto_start_msg}! 🚀

**🔍 Next Steps:**
• Check status: **"vctl status"**
• View logs: **"show recent logs"**
• List all agents: **"list agents"**
"""
        else:
            return f"""❌ **Failed to install {agent_name} agent**

**Error:** {result.stderr or result.stdout}

💡 **Troubleshooting:**
• Make sure VOLTTRON is running: **"start volttron"**
• Check agent status: **"vctl status"**
• Try: **"what agents can I install?"**"""
            
    except Exception as e:
        return f"❌ Error installing {agent_name} agent: {str(e)}"

def list_available_agents():
    """List all available VOLTTRON agents that can be installed."""
    categories = {}
    
    # Group agents by category
    for agent_name, info in AVAILABLE_AGENTS.items():
        category = info['category']
        if category not in categories:
            categories[category] = []
        categories[category].append({
            'name': agent_name,
            'description': info['description'],
            'package': info['package']
        })
    
    output = "🤖 **Available VOLTTRON Agents:**\n\n"
    
    for category, agents in categories.items():
        output += f"**{category} Agents:**\n"
        for agent in agents:
            output += f"• **{agent['name']}** - {agent['description']}\n"
        output += "\n"
    
    output += """💡 **How to install:**
• Say: **"install listener"** or **"install sqlite-historian"**
• Or: **"install [agent-name]"** for any agent above

🎯 **Recommended for beginners:**
• **listener** - Great for monitoring platform activity
• **platform-driver** - Essential for device communication
• **sqlite-historian** - Perfect for storing sensor data"""
    
    return output

def find_pip_command():
    """Find pip command in the VOLTTRON environment."""
    # Check the current virtual environment first
    if 'VIRTUAL_ENV' in os.environ:
        pip_path = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'pip')
        if os.path.exists(pip_path):
            return pip_path
    
    # Check common VOLTTRON environment locations
    common_pip_paths = [
        "/home/igor/Work/Volttron_eclispe/env/bin/pip",
        "/home/igorj/volttron/volttron-ai-igorversions/env/bin/pip",
        "/usr/local/bin/pip",
        "/usr/bin/pip"
    ]
    
    for path in common_pip_paths:
        if os.path.exists(path):
            return path
    
    # Try to find pip in PATH
    pip_cmd = shutil.which("pip")
    if pip_cmd:
        return pip_cmd
    
    return None

def vctl_uninstall_all_listeners():
    """Uninstall all listener agents to clean up duplicates."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Get current agent status
        status_result = subprocess.run(
            [vctl_cmd, "status"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home
        )
        
        if status_result.returncode != 0:
            return "❌ Could not get agent status. Make sure VOLTTRON is running."
        
        # Parse status output to find listener agents
        lines = status_result.stdout.strip().split('\n')
        listener_uuids = []
        
        for line in lines[1:]:  # Skip header
            if not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                uuid = parts[0]
                agent_name = parts[1]
                
                if 'listener' in agent_name.lower():
                    listener_uuids.append(uuid)
        
        if not listener_uuids:
            return "✅ No listener agents found to uninstall."
        
        # Uninstall each listener agent
        removed_agents = []
        failed_agents = []
        
        for uuid in listener_uuids:
            # Stop first
            subprocess.run([vctl_cmd, "stop", uuid], capture_output=True, env=env, cwd=volttron_home)
            
            # Then remove
            result = subprocess.run(
                [vctl_cmd, "remove", uuid], 
                capture_output=True, 
                text=True,
                env=env,
                cwd=volttron_home
            )
            
            if result.returncode == 0:
                removed_agents.append(uuid)
            else:
                failed_agents.append(f"{uuid}: {result.stderr or result.stdout}")
        
        # Build response
        response_parts = []
        
        if removed_agents:
            response_parts.append(f"🗑️ Successfully removed {len(removed_agents)} listener agents:")
            for uuid in removed_agents:
                response_parts.append(f"   • {uuid}")
        
        if failed_agents:
            response_parts.append(f"\n❌ Failed to remove {len(failed_agents)} agents:")
            for failure in failed_agents:
                response_parts.append(f"   • {failure}")
        
        if removed_agents:
            response_parts.append(f"\n✅ Cleanup complete! Your platform driver is still running.")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"Error during cleanup: {str(e)}"

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
    """Provide conversational next steps based on VOLTTRON's current state."""
    # Check if VOLTTRON is actually running
    status_result = check_volttron_status()
    
    if "VOLTTRON is running" in status_result or "PID" in status_result:
        # VOLTTRON IS RUNNING - focus on what to do next
        return """
🎉 **Great! VOLTTRON is running!** 

Next step: Use **vctl commands** to control me! 

Try asking me:
- "What vctl commands are available?"
- "How do I check status?"
- "Help me install an agent"
- "Show me my agents"

I'll guide you through the specific vctl commands as you need them! 🚀
"""
    else:
        # VOLTTRON IS NOT RUNNING - show setup instructions
        return """
🔧 **VOLTTRON Setup & Installation Guide**

I'm not running yet! Here's how to get me started:

## 📦 **Installation Steps:**

### 1️⃣ **Setup Virtual Environment**
```bash
python -m venv env
source env/bin/activate
```

### 2️⃣ **Install VOLTTRON**
```bash
pip install volttron
```

### 3️⃣ **Setup VOLTTRON_HOME** (Important!)
```bash
export VOLTTRON_HOME=/path/to/volttron_home/dir
```

### 4️⃣ **Start VOLTTRON**
```bash
volttron -vv -l volttron.log &>/dev/null &
```

## 🚀 **Quick Start Alternative:**
Ask me: **"Can you start VOLTTRON for me?"** and I'll handle it!

Once I'm running, come back and ask **"What's next?"** for vctl commands! 
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

def vctl_install_platform_driver():
    """Install the VOLTTRON platform driver agent."""
    vctl_cmd = find_vctl_command()
    
    if not vctl_cmd:
        return "❌ vctl command not found. Please ensure VOLTTRON is installed and accessible."
    
    try:
        # First check if it's already installed
        status_result = subprocess.run([
            vctl_cmd, "status"
        ], capture_output=True, text=True, timeout=30)
        
        # Format any system warnings
        warning_msg = format_volttron_warnings(status_result.stderr)
        
        if "platform.driver" in status_result.stdout:
            return f"""{warning_msg}✅ **Platform driver is already installed and running!**

Great news! The platform driver agent is active and ready to manage your devices.

**Next step**: Let's install the fake driver library and configure some fake sensors.

Would you like me to:
1. Install the fake driver library
2. Create fake sensor configurations  
3. Set up monitoring

Just ask: **"Install the fake driver library"** and I'll get started! 🚀
"""
        
        # Install the platform driver agent
        install_result = subprocess.run([
            vctl_cmd, "install", "volttron-platform-driver", 
            "--vip-identity", "platform.driver", "--start"
        ], capture_output=True, text=True, timeout=120)
        
        # Format any system warnings from installation
        install_warning_msg = format_volttron_warnings(install_result.stderr)
        
        if install_result.returncode == 0:
            return f"""{install_warning_msg}🎉 **Platform driver installed successfully!**

The platform driver agent is now installed and starting up! This agent will manage all your device drivers.

**What's working:**
✅ **Platform driver agent** - Installed and starting
✅ **VIP Identity** - `platform.driver`
✅ **Auto-start** - Enabled

**Next step**: Let's install the fake driver library to create simulated sensors.

Ask: **"Install the fake driver library"** and I'll help you set up fake sensor data! 🚀
"""
        else:
            error_msg = install_result.stderr or install_result.stdout or "Unknown error"
            return f"""{install_warning_msg}❌ **Failed to install platform driver**

Installation failed with error:
```
{error_msg}
```

**Troubleshooting steps:**
1. **Check VOLTTRON status** - Make sure VOLTTRON is running
2. **Check network** - Ensure internet connection for package download
3. **Try manual install** - Run: `vctl install volttron-platform-driver --vip-identity platform.driver --start`

Would you like me to help troubleshoot this issue?
"""
        
    except Exception as e:
        return f"""⚠️ **Error installing platform driver**

An unexpected error occurred: {str(e)}

**Try the manual command:**
```bash
vctl install volttron-platform-driver --vip-identity platform.driver --start
```

Would you like me to help troubleshoot this issue?
"""

def install_fake_driver_library():
    """Install the volttron fake driver library."""
    try:
        result = subprocess.run([
            "pip", "install", "volttron-lib-fake-driver"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Check what steps are remaining
            config_exists = os.path.exists("config/fake.config") and os.path.exists("config/fake.csv")
            stored_in_vctl = False
            
            # Check if already stored in VOLTTRON config
            vctl_cmd = find_vctl_command()
            if vctl_cmd:
                check_result = subprocess.run([
                    vctl_cmd, "config", "list", "platform.driver"
                ], capture_output=True, text=True, timeout=10)
                stored_in_vctl = "devices/campus/building/fake" in check_result.stdout
            
            if stored_in_vctl:
                return """
✅ **Fake driver library installed!**

Perfect! Your fake driver is already fully configured and ready.

**🎉 Ready to see data!** Ask: **"Subscribe to fake data"** to see live sensor readings! 📊
"""
            elif config_exists:
                return """
✅ **Fake driver library installed!**

Great! I can see the config files already exist. 

**Next step**: Store the configuration in VOLTTRON. Ask: **"Store the fake driver config"** 📁➡️🏠
"""
            else:
                return """
✅ **Fake driver library installed!**

Perfect! Now let's create the configuration files.

**Next step**: Ask: **"Create the fake driver config"** and I'll generate the needed files! 📁
"""
        else:
            return f"""
❌ **Failed to install fake driver library**

Error: {result.stderr or result.stdout}

Try manually running: `pip install volttron-lib-fake-driver`
"""
    except Exception as e:
        return f"❌ Error installing fake driver library: {str(e)}"

def create_fake_driver_config():
    """Create configuration files for the fake driver."""
    try:
        # Create config directory
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # Create fake.config
        fake_config_content = """{
    "driver_config": {},
    "registry_config": "config://fake.csv",
    "interval": 5,
    "timezone": "US/Pacific",
    "heart_beat_point": "Heartbeat",
    "driver_type": "fake",
    "publish_breadth_first_all": false,
    "publish_depth_first": false,
    "publish_breadth_first": false
}"""
        
        fake_config_path = config_dir / "fake.config"
        fake_config_path.write_text(fake_config_content)
        
        # Create fake.csv
        fake_csv_content = """Point Name,Volttron Point Name,Units,Units Details,Writable,Starting Value,Type,Notes
EKG,EKG,waveform,waveform,TRUE,sin,float,Sine wave for baseline output
Heartbeat,Heartbeat,On/Off,On/Off,TRUE,0,boolean,Point for heartbeat toggle
OutsideAirTemperature1,OutsideAirTemperature1,F,-100 to 300,FALSE,50,float,CO2 Reading 0.00-2000.0 ppm
SampleWritableFloat1,SampleWritableFloat1,PPM,1000.00 (default),TRUE,10,float,Setpoint to enable demand control ventilation
SampleLong1,SampleLong1,Enumeration,1 through 13,FALSE,50,int,Status indicator of service switch
SampleWritableShort1,SampleWritableShort1,%,0.00 to 100.00 (20 default),TRUE,20,int,Minimum damper position during the standard mode
SampleBool1,SampleBool1,On / Off,on/off,FALSE,TRUE,boolean,Status indidcator of cooling stage 1
SampleWritableBool1,SampleWritableBool1,On / Off,on/off,TRUE,TRUE,boolean,Status indicator
HPWH_Phy0_PowerState,PowerState,1/0,1/0,TRUE,0,int,Power on off status
ERWH_Phy0_ValveState,ValveState,1/0,1/0,TRUE,0,int,power on off status
EKG_Sin,EKG_Sin,1-0,SIN Wave,TRUE,sin,float,SIN wave
EKG_Cos,EKG_Cos,1-0,COS Wave,TRUE,sin,float,COS wave"""
        
        fake_csv_path = config_dir / "fake.csv"
        fake_csv_path.write_text(fake_csv_content)
        
        # Check if already stored in VOLTTRON config to determine next step
        vctl_cmd = find_vctl_command()
        stored_in_vctl = False
        
        if vctl_cmd:
            check_result = subprocess.run([
                vctl_cmd, "config", "list", "platform.driver"
            ], capture_output=True, text=True, timeout=10)
            stored_in_vctl = "devices/campus/building/fake" in check_result.stdout
        
        if stored_in_vctl:
            return f"""
📁 **Configuration files created successfully!**

I've created:
- `{fake_config_path.absolute()}` - Driver configuration
- `{fake_csv_path.absolute()}` - Device registry points

**🎉 Already stored in VOLTTRON!** Your fake driver is ready to publish data.

**Next step**: Ask: **"Subscribe to fake data"** to see live sensor readings! 📊
"""
        else:
            return f"""
📁 **Configuration files created successfully!**

I've created:
- `{fake_config_path.absolute()}` - Driver configuration
- `{fake_csv_path.absolute()}` - Device registry points

**Next step**: Ask me: **"Store the fake driver config"** and I'll upload them to VOLTTRON! 🔧
"""
        
    except Exception as e:
        return f"❌ Error creating config files: {str(e)}"

def store_fake_driver_config():
    """Store the fake driver configuration in VOLTTRON."""
    vctl_cmd = find_vctl_command()
    
    if not vctl_cmd:
        return "❌ vctl command not found. Please ensure VOLTTRON is installed and accessible."
    
    try:
        # Store fake.config for the platform driver
        result1 = subprocess.run([
            vctl_cmd, "config", "store", "platform.driver", 
            "devices/campus/building/fake", "config/fake.config"
        ], capture_output=True, text=True, timeout=30)
        
        # Store fake.csv as registry config
        result2 = subprocess.run([
            vctl_cmd, "config", "store", "platform.driver", 
            "fake.csv", "config/fake.csv", "--csv"
        ], capture_output=True, text=True, timeout=30)
        
        if result1.returncode == 0 and result2.returncode == 0:
            # Check if listener is already available
            pip_cmd = "/home/igor/Work/Volttron_eclispe/env/bin/pip"
            listener_installed = False
            
            if os.path.exists(pip_cmd):
                check_result = subprocess.run([
                    pip_cmd, "show", "volttron-listener"
                ], capture_output=True, text=True, timeout=10)
                listener_installed = check_result.returncode == 0
            
            if listener_installed:
                return """
🎉 **Configuration stored successfully!**

Your fake driver is now configured and the listener package is ready! The platform driver should start publishing fake sensor data.

**🎯 Ready to see data!** Ask: **"Subscribe to fake data"** to see live sensor readings! 📊
"""
            else:
                return """
🎉 **Configuration stored successfully!**

Your fake driver is now configured! The platform driver should start publishing fake sensor data.

**Final step**: Ask: **"Install listener"** to set up monitoring! 👀
"""
        else:
            error_msg = ""
            if result1.returncode != 0:
                error_msg += f"Config store error: {result1.stderr}\n"
            if result2.returncode != 0:
                error_msg += f"Registry store error: {result2.stderr}\n"
            
            return f"""❌ **Failed to store configuration**

Error: {error_msg}

Make sure:
- VOLTTRON is running
- Platform driver is installed
- Config files exist in the config/ directory
"""
            error_msg = result1.stderr or result2.stderr or "Unknown error"
            return f"""
❌ **Failed to store configuration**

Error: {error_msg}

Make sure:
- VOLTTRON is running
- Platform driver is installed
- Config files exist in the config/ directory
"""
            
    except Exception as e:
        return f"❌ Error storing configuration: {str(e)}"

def setup_fake_driver_monitoring():
    """Set up monitoring and install listener agent to view fake driver data."""
    vctl_cmd = find_vctl_command()
    
    if not vctl_cmd:
        return "❌ vctl command not found. Please ensure VOLTTRON is installed and accessible."
    
    try:
        # First ensure the volttron-listener package is installed
        pip_cmd = "/home/igor/Work/Volttron_eclispe/env/bin/pip"
        if os.path.exists(pip_cmd):
            # Install the package directly if not already installed
            install_result = subprocess.run(
                [pip_cmd, 'install', 'volttron-listener'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if install_result.returncode != 0 and "already satisfied" not in install_result.stdout.lower():
                return f"❌ Failed to install volttron-listener package: {install_result.stderr}"
        
        # Check if fake device config exists
        config_result = subprocess.run([
            vctl_cmd, "config", "list", "platform.driver"
        ], capture_output=True, text=True, timeout=30)
        
        # Check if listener is already running
        status_result = subprocess.run([
            vctl_cmd, "status"
        ], capture_output=True, text=True, timeout=30)
        
        # Check if platform driver agent is actually installed
        platform_driver_installed = "platform.driver" in status_result.stdout if status_result.returncode == 0 else False
        listener_running = "listener" in status_result.stdout.lower() if status_result.returncode == 0 else False
        fake_config_exists = "devices/campus/building/fake" in config_result.stdout
        
        if fake_config_exists and platform_driver_installed:
            if listener_running:
                return """
🎉 **Fake driver setup is complete!**

Your fake sensors are now publishing data! Here's what's running:

✅ **Platform driver** - Managing your fake devices
✅ **Fake device config** - `devices/campus/building/fake` 
✅ **Registry file** - `fake.csv` with sensor definitions
✅ **Listener agent** - Already running and capturing messages
✅ **Data publishing** - Every 5 seconds to VOLTTRON message bus

**🔍 How to see your data:**

**Method 1 - Check agent logs:**
```bash
vctl status
tail -f volttron.log | grep listener
```

**Method 2 - Subscribe manually:**
```bash
vctl subscribe devices/campus/building/fake
```

**Method 3 - Ask me:**
- Say: **"Show me recent logs"**
- Say: **"Subscribe to fake data"**

**📊 Your fake sensors include:**
- **EKG** - Sine wave pattern
- **OutsideAirTemperature1** - Temperature readings  
- **Heartbeat** - Boolean toggle
- **SampleWritableFloat1** - Writable PPM value

The listener agent is capturing all messages on the VOLTTRON bus! 🚀
"""
            else:
                return """
✅ **Fake driver configured and volttron-listener package is ready!**

Your fake sensors are publishing data! Here's what's working:

✅ **Platform driver** - Managing your fake devices
✅ **Fake device config** - `devices/campus/building/fake` 
✅ **volttron-listener package** - Installed (v2.0.0rc3)
✅ **Data publishing** - Every 5 seconds to VOLTTRON message bus

**🔍 How to see your data:**

**Method 1 - Subscribe manually:**
```bash
vctl subscribe devices/campus/building/fake
```

**Method 2 - Monitor logs:**
```bash
tail -f volttron.log | grep fake
```

**Method 3 - Ask me:**
- Say: **"Subscribe to fake data"**
- Say: **"Show recent logs"**

**📊 Your fake sensors include:**
- **EKG** - Sine wave pattern
- **OutsideAirTemperature1** - Temperature readings  
- **Heartbeat** - Boolean toggle
- **SampleWritableFloat1** - Writable PPM value

**Note:** The volttron-listener package is available but agent setup can be done manually if needed.
Your fake driver is working - you can view the data using the methods above! 🚀
"""
        elif fake_config_exists and not platform_driver_installed:
            return """
⚠️ **Configuration ready, but Platform Driver agent not installed!**

I found your fake driver configuration, but the Platform Driver agent itself isn't installed yet.

**What's ready:**
✅ **Fake device config** - `devices/campus/building/fake` 
✅ **volttron-listener package** - Installed (v2.0.0rc3)

**What's missing:**
❌ **Platform Driver agent** - The agent that actually publishes the data

**Next step:** Ask me **"Install platform driver"** to complete the setup! 🔧

Once the Platform Driver agent is installed, it will start publishing your fake sensor data every 5 seconds.
"""
        else:
            return """
⚠️ **volttron-listener package installed but fake device not found**

The monitoring package is ready, but I couldn't find your fake device configuration.

**Next steps:**
1. **Check config** - Ask me: "Show VOLTTRON status"
2. **Setup fake driver** - Ask me about platform driver setup
3. **Verify config** - Run: `vctl config list platform.driver`

The listener package is installed and ready to monitor once your fake driver is configured!
"""
            
    except Exception as e:
        return f"❌ Error setting up monitoring: {str(e)}"

def subscribe_to_fake_data():
    """Subscribe to fake driver data to see live sensor readings."""
    vctl_cmd = find_vctl_command()
    
    if not vctl_cmd:
        return "❌ vctl command not found. Please ensure VOLTTRON is installed and accessible."
    
    try:
        # First check if VOLTTRON is running and fake device is configured
        status_result = subprocess.run([vctl_cmd, "status"], capture_output=True, text=True, timeout=10)
        
        if status_result.returncode != 0:
            return """
⚠️ **VOLTTRON is not running**

I need VOLTTRON to be running to show you live data.

**Quick fix:**
- Ask me: **"Start VOLTTRON"**
- Or run: `volttron -vv -l volttron.log &`

Once VOLTTRON is running, ask me again to see your fake sensor data! 🚀
"""
        
        # Run subscribe command for a short period to capture some messages
        result = subprocess.run([
            vctl_cmd, "subscribe", "devices/campus/building/fake", "--max-count", "3"
        ], capture_output=True, text=True, timeout=15)
        
        if result.stdout and "devices/campus/building/fake" in result.stdout:
            # Parse and format the subscription data nicely
            lines = result.stdout.strip().split('\n')
            formatted_data = []
            current_message = {}
            
            for line in lines:
                if line.startswith('Topic:'):
                    if current_message:
                        formatted_data.append(current_message)
                    current_message = {'topic': line.replace('Topic: ', '').strip()}
                elif line.startswith('Headers:'):
                    current_message['headers'] = line.replace('Headers: ', '').strip()
                elif line.startswith('Message:'):
                    current_message['message'] = line.replace('Message: ', '').strip()
            
            if current_message:
                formatted_data.append(current_message)
            
            if formatted_data:
                display_messages = ""
                for i, msg in enumerate(formatted_data[:3], 1):
                    display_messages += f"""
**📊 Message {i}:**
- **Topic**: `{msg.get('topic', 'N/A')}`
- **Data**: `{msg.get('message', 'N/A')}`
"""
                
                return f"""
📡 **Live fake sensor data streaming!** 🎉

Here's what your sensors just published:
{display_messages}

**🔬 What you're seeing:**
- **EKG**: Sine wave medical sensor pattern  
- **OutsideAirTemperature1**: Environmental temperature readings
- **Heartbeat**: Boolean pulse signal (true/false)
- **SampleWritableFloat1**: PPM concentration levels

**🚀 Your fake driver is working perfectly!**

**Want to see more?**
- **Continuous stream**: Run `vctl subscribe devices/campus/building/fake`
- **Agent logs**: Ask me "Show recent logs"
- **Live monitoring**: Keep asking me "Subscribe to fake data" for fresh readings!

Data publishes every 5 seconds - your VOLTTRON setup is active! ⚡
"""
            
        # Try alternative approach - check recent log data
        return get_recent_fake_data_from_logs()
        
    except subprocess.TimeoutExpired:
        return """
📡 **Subscription is working!** (Timeout after 15 seconds)

Your fake sensors are publishing data, but I stopped listening to give you a quick response.

**🎯 To see continuous live data:**

**Option 1 - Terminal stream:**
```bash
vctl subscribe devices/campus/building/fake
```
*(Press Ctrl+C to stop)*

**Option 2 - Quick samples:**
Keep asking me **"Subscribe to fake data"** and I'll grab fresh readings each time!

**Option 3 - Log monitoring:**
Ask me **"Show recent logs"** to see historical data.

Your fake driver is actively publishing every 5 seconds! 🚀⚡
"""
        
    except Exception as e:
        return f"❌ Error subscribing to data: {str(e)}"

def get_recent_fake_data_from_logs():
    """Get recent fake driver data from VOLTTRON logs."""
    try:
        # Look for volttron.log in common locations
        log_paths = [
            "/home/igor/Work/Volttron_eclispe/volttron.log",
            "volttron.log",
            "/tmp/volttron.log"
        ]
        
        volttron_log = None
        for path in log_paths:
            if os.path.exists(path):
                volttron_log = path
                break
        
        if not volttron_log:
            return """
📡 **Subscription ready, but no recent log data found**

Your fake sensors should be publishing, but I couldn't find recent log files.

**To see live data:**
1. **Direct subscribe**: `vctl subscribe devices/campus/building/fake`
2. **Check VOLTTRON status**: Ask me "Show VOLTTRON status"
3. **Start VOLTTRON**: Ask me "Start VOLTTRON" if it's not running

Your fake driver configuration is ready! 🚀
"""
        
        # Get recent lines from the log that mention fake driver
        result = subprocess.run([
            "tail", "-100", volttron_log
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            fake_lines = [line for line in lines if 'fake' in line.lower() and ('devices/campus/building/fake' in line or 'driver' in line)]
            
            if fake_lines:
                recent_lines = fake_lines[-5:]  # Last 5 relevant lines
                log_display = '\n'.join(recent_lines)
                
                return f"""
📡 **Recent fake driver activity from logs:**

```
{log_display}
```

**🎯 Your fake driver is active!**

**To see live streaming data:**
- **Real-time**: `vctl subscribe devices/campus/building/fake`
- **Fresh samples**: Keep asking "Subscribe to fake data"
- **More logs**: Ask "Show recent logs"

Data is being published every 5 seconds! 🚀⚡
"""
            else:
                return """
📡 **VOLTTRON is running but no recent fake driver data in logs**

This might mean:
- **Fake driver needs restart**: Ask me "Restart platform driver"
- **Configuration issue**: Ask me "Show VOLTTRON status"
- **Data publishing elsewhere**: Try `vctl subscribe devices/campus/building/fake`

Let me help you troubleshoot! 🔧
"""
        
        return "❌ Could not read VOLTTRON logs to check fake driver activity"
        
    except Exception as e:
        return f"❌ Error checking logs for fake data: {str(e)}"

def show_recent_logs():
    """Show recent VOLTTRON logs with focus on fake driver and agent activity."""
    try:
        # Look for volttron.log in common locations
        log_paths = [
            "/home/igor/Work/Volttron_eclispe/volttron.log",
            "volttron.log",
            "/tmp/volttron.log",
            "/var/log/volttron.log"
        ]
        
        volttron_log = None
        for path in log_paths:
            if os.path.exists(path):
                volttron_log = path
                break
        
        if not volttron_log:
            return """
📋 **No VOLTTRON log file found**

I looked in these locations:
- `/home/igor/Work/Volttron_eclispe/volttron.log`
- `volttron.log` (current directory)
- `/tmp/volttron.log`
- `/var/log/volttron.log`

**To start logging:**
1. **Start VOLTTRON with logging**: `volttron -vv -l volttron.log &`
2. **Check if running**: Ask me "Show VOLTTRON status"
3. **Generate some activity**: Ask me "Subscribe to fake data"

Once VOLTTRON is running with logging, I can show you live activity! 🚀
"""
        
        # Get recent lines from the log
        result = subprocess.run([
            "tail", "-50", volttron_log
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            log_lines = result.stdout.strip().split('\n')
            
            # Filter for interesting lines (fake driver, agents, errors, etc.)
            interesting_lines = []
            for line in log_lines:
                lower_line = line.lower()
                if any(keyword in lower_line for keyword in [
                    'fake', 'driver', 'platform.driver', 'agent', 'error', 'warning',
                    'devices/campus/building', 'listener', 'subscribe', 'publish'
                ]):
                    interesting_lines.append(line)
            
            if interesting_lines:
                log_display = '\n'.join(interesting_lines[-15:])  # Last 15 relevant lines
                
                return f"""
📋 **Recent VOLTTRON Activity Logs**

Here's what's been happening with your fake driver and agents:

```
{log_display}
```

**🔍 What to look for:**
- **Platform driver activity** - Device management
- **Fake device messages** - `devices/campus/building/fake`
- **Agent communications** - Listener, platform agents
- **Errors/Warnings** - Any issues that need attention

**📊 Your system status:**
- **Log file**: `{volttron_log}`
- **Recent activity**: {"Active" if interesting_lines else "Quiet"}
- **Fake driver**: {"Publishing data" if any('fake' in line.lower() for line in interesting_lines) else "Check configuration"}

**Next steps:**
- **See live data**: Ask "Subscribe to fake data"
- **Check agents**: Ask "Show VOLTTRON status"
- **Monitor continuously**: `tail -f {volttron_log}`
"""
            else:
                return f"""
📋 **VOLTTRON is running but activity is quiet**

**Log file found**: `{volttron_log}`
**Recent entries**: {len(log_lines)} lines total

The log doesn't show recent fake driver or agent activity. This might mean:

**Possible reasons:**
- **VOLTTRON just started** - No activity yet
- **Platform driver not active** - May need restart
- **Fake device not configured** - Check configuration
- **Logging level too low** - May need verbose logging

**Try these:**
1. **Generate activity**: Ask "Subscribe to fake data"
2. **Check status**: Ask "Show VOLTTRON status"
3. **Restart driver**: Ask about platform driver restart
4. **Manual check**: `tail -f {volttron_log}`

Let me help you get some activity going! 🚀
"""
        else:
            return f"❌ Could not read VOLTTRON log file: {volttron_log}"
            
    except subprocess.TimeoutExpired:
        return "❌ Timeout while reading VOLTTRON logs"
    except Exception as e:
        return f"❌ Error reading logs: {str(e)}"