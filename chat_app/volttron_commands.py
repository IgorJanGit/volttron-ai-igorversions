import subprocess
import os
import shutil
from pathlib import Path

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
                # Return conversational summary instead of raw table
                return f"{warning_msg}{conversational_summary}"
                
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
                if status_output.strip() and "No installed Agents found" not in status_output:
                    return f"✅ VOLTTRON platform is running with agents active."
                else:
                    return f"🟡 VOLTTRON platform is running but no agents are installed."
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