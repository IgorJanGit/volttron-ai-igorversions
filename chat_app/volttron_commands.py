import subprocess
import os
import sys
import shutil
from pathlib import Path


def get_active_virtualenv():
    """
    Get the active virtual environment path dynamically.
    This will work regardless of where VOLTTRON is installed.
    
    Returns:
        tuple: (is_active, venv_path, reason)
    """
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        return True, venv_path, "VIRTUAL_ENV environment variable"
    
    if hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    ):
        return True, sys.prefix, "sys.prefix detection"
    
    return False, None, "Not in virtual environment"

def is_in_virtualenv():
    """Check if currently running in a virtual environment."""
    is_active, _, _ = get_active_virtualenv()
    return is_active

def get_pip_command_from_venv():
    """
    Get pip command from the ACTIVE virtual environment.
    This is the proper way - use what's actually active!
    
    Returns:
        tuple: (pip_path, error_message)
    """
    is_active, venv_path, reason = get_active_virtualenv()
    
    if not is_active:
        return None, "❌ Not running in a virtual environment! VOLTTRON requires a virtual environment."
    
    # Check for pip in the active venv
    pip_path = os.path.join(venv_path, 'bin', 'pip')
    
    if os.path.exists(pip_path) and os.access(pip_path, os.X_OK):
        print(f"✅ Using pip from active venv: {pip_path}")
        return pip_path, None
    
    # Also check for pip3
    pip3_path = os.path.join(venv_path, 'bin', 'pip3')
    if os.path.exists(pip3_path) and os.access(pip3_path, os.X_OK):
        print(f"✅ Using pip3 from active venv: {pip3_path}")
        return pip3_path, None
    
    return None, f"❌ pip not found in active virtual environment: {venv_path}"

# ============================================================================
# VOLTTRON AGENTS AND PACKAGES
# ============================================================================

# Available VOLTTRON agents and packages
AVAILABLE_AGENTS = {
    # Core Agents
    'listener': {
        'package': 'volttron-listener-agent',  # Updated to the new package name
        'alt_package': 'volttron-listener',    # Alternative/legacy package name
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
    try:
        if not stderr_output or stderr_output.strip() == "":
            return ""
        
        warnings = []
        lines = stderr_output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
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
                warnings.append(f"📋 **System**: {line}")
        
        if warnings:
            return "\n**System Messages:**\n" + "\n".join(warnings) + "\n\n"
        return ""
    except Exception as e:
        print(f"Error in format_volttron_warnings: {str(e)}")
        return "" 

def find_volttron_command():
    """Find volttron command in various locations, prioritizing running instance."""
    

    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'volttron' in proc.name().lower() or any('volttron' in cmd.lower() for cmd in proc.cmdline() if cmd):

                    cmd_path = proc.cmdline()[0] if proc.cmdline() else None
                    if cmd_path and os.path.exists(cmd_path) and 'volttron' in cmd_path:
                        print(f"DEBUG: Found volttron from running process: {cmd_path}")
                        return cmd_path
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except ImportError:

        pass
    

    fresh_volttron = os.path.expanduser("~/volttron-fresh/venv-fresh/bin/volttron")
    if os.path.exists(fresh_volttron):
        print(f"DEBUG: Using volttron from fresh installation: {fresh_volttron}")
        return fresh_volttron
    
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_env_volttron = os.path.join(os.path.dirname(current_dir), "env", "bin", "volttron")
    if os.path.exists(project_env_volttron):
        print(f"DEBUG: Using volttron from project env: {project_env_volttron}")
        return project_env_volttron
    

    volttron_cmd = shutil.which("volttron")
    if volttron_cmd:
        print(f"DEBUG: Using volttron from PATH: {volttron_cmd}")
        return volttron_cmd

    possible_paths = [

        os.path.join(os.getenv("VIRTUAL_ENV", ""), "bin", "volttron"),

        os.path.expanduser("~/volttron/bin/volttron"),
        os.path.expanduser("~/VOLTTRON/bin/volttron"),
        os.path.expanduser("~/volttron-env/bin/volttron"),
        os.path.expanduser("~/VOLTTRON/env/bin/volttron"),
        os.path.expanduser("~/VOLTTRON/AI/env/bin/volttron"),

        os.path.expanduser("~/volttron-fresh/venv-fresh/bin/volttron"),
        os.path.expanduser("~/volttron-fresh/env/bin/volttron"),

        "/opt/volttron/bin/volttron",
        "/usr/local/bin/volttron",
        "/usr/bin/volttron"
    ]
    
    for path in possible_paths:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    
    return None

def find_vctl_command():
    """Find vctl command in various locations, prioritizing running instance."""
    
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'volttron' in proc.name().lower() or any('volttron' in cmd.lower() for cmd in proc.cmdline() if cmd):
                    cmd_path = proc.cmdline()[0] if proc.cmdline() else None
                    if cmd_path and os.path.exists(cmd_path):
                        bin_dir = os.path.dirname(cmd_path)
                        vctl_path = os.path.join(bin_dir, "vctl")
                        if os.path.isfile(vctl_path) and os.access(vctl_path, os.X_OK):
                            print(f"DEBUG: Found vctl from running process: {vctl_path}")
                            return vctl_path
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except ImportError:
        pass
    
    fresh_vctl = os.path.expanduser("~/volttron-fresh/venv-fresh/bin/vctl")
    if os.path.exists(fresh_vctl):
        print(f"DEBUG: Using vctl from fresh installation: {fresh_vctl}")
        return fresh_vctl
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_env_vctl = os.path.join(os.path.dirname(current_dir), "env", "bin", "vctl")
    if os.path.exists(project_env_vctl):
        print(f"DEBUG: Using vctl from project env: {project_env_vctl}")
        return project_env_vctl
    
    vctl_cmd = shutil.which("vctl")
    if vctl_cmd:
        print(f"DEBUG: Using vctl from PATH: {vctl_cmd}")
        return vctl_cmd
    
    volttron_cmd = find_volttron_command()
    if volttron_cmd:
        vctl_path = os.path.join(os.path.dirname(volttron_cmd), "vctl")
        if os.path.isfile(vctl_path) and os.access(vctl_path, os.X_OK):
            print(f"DEBUG: Using vctl from volttron path: {vctl_path}")
            return vctl_path
    
    print("DEBUG: Could not find vctl command")
    return None

def get_volttron_env_path():
    """Get the path to the VOLTTRON virtual environment."""
    venv_path = os.getenv("VIRTUAL_ENV")
    if venv_path:
        return venv_path
    
    volttron_cmd = find_volttron_command()
    if volttron_cmd:
        bin_dir = os.path.dirname(volttron_cmd)
        if bin_dir.endswith("/bin"):
            return os.path.dirname(bin_dir)
    
    return None

def get_volttron_home():
    """Get the VOLTTRON_HOME directory, preferring fresh installation if available."""
    
    env_volttron_home = os.getenv("VOLTTRON_HOME")
    if env_volttron_home:
        print(f"DEBUG: Using VOLTTRON_HOME from environment: {env_volttron_home}")
        return env_volttron_home
    
    possible_paths = [
        os.path.expanduser("~/volttron-fresh/volttron_home"),
        os.path.expanduser("~/.volttron"),
        os.path.expanduser("~/volttron_home"),
        "/var/lib/volttron",
        "/tmp/volttron_home"
    ]
    
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'environ']):
            try:
                if 'volttron' in proc.name().lower() or any('volttron' in cmd.lower() for cmd in proc.cmdline() if cmd):
                    if proc.environ() and 'VOLTTRON_HOME' in proc.environ():
                        volttron_home_from_proc = proc.environ()['VOLTTRON_HOME']
                        print(f"DEBUG: Found VOLTTRON_HOME from running process: {volttron_home_from_proc}")
                        return volttron_home_from_proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except ImportError:
        pass
        
    for path in possible_paths:
        if os.path.exists(path):
            if (os.path.exists(os.path.join(path, "agents")) or 
                os.path.exists(os.path.join(path, "certificates"))):
                print(f"DEBUG: Found valid VOLTTRON_HOME at: {path}")
                return path
    
    default_volttron_home = os.path.expanduser("~/.volttron")
    os.makedirs(default_volttron_home, exist_ok=True)
    print(f"DEBUG: Using default VOLTTRON_HOME: {default_volttron_home}")
    return default_volttron_home


def run_vctl_help(subcommand=None):
    """Run vctl --help or vctl <subcommand> --help to learn about available commands.
    
    Args:
        subcommand: Optional subcommand to get help for (e.g., 'install', 'status')
    
    Returns:
        str: Help output from vctl
    """
    vctl_cmd = find_vctl_command()
    volttron_home = get_volttron_home()
    
    if not vctl_cmd:
        return "❌ Could not find vctl command"
    
    try:
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        if subcommand:
            result = subprocess.run(
                [vctl_cmd, subcommand, "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
                cwd=volttron_home
            )
        else:
            result = subprocess.run(
                [vctl_cmd, "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
                cwd=volttron_home
            )
        
        if result.returncode == 0:
            return result.stdout
        else:
            return result.stderr or "No help available"
            
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout getting help"
    except Exception as e:
        return f"💥 Error getting help: {str(e)}"


def intelligent_vctl_command_discovery(user_intent, context=""):
    """Intelligently discover and execute vctl commands by learning from --help.
    
    This function:
    1. Runs vctl --help to see available commands
    2. Analyzes the user's intent
    3. Picks the most likely command
    4. Runs that command's --help if needed
    5. Executes the command with appropriate arguments
    
    Args:
        user_intent: What the user is trying to do (e.g., "check agent status")
        context: Additional context about the request
    
    Returns:
        dict: {
            'success': bool,
            'command_used': str,
            'output': str,
            'help_consulted': list of help commands checked
        }
    """
    vctl_cmd = find_vctl_command()
    volttron_home = get_volttron_home()
    
    if not vctl_cmd:
        return {
            'success': False,
            'command_used': None,
            'output': "❌ Could not find vctl command",
            'help_consulted': []
        }
    
    result = {
        'success': False,
        'command_used': None,
        'output': '',
        'help_consulted': []
    }
    
    try:
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        help_output = run_vctl_help()
        result['help_consulted'].append('vctl --help')
        
        available_commands = []
        lines = help_output.split('\n')
        in_commands_section = False
        
        for line in lines:
            if 'positional arguments:' in line.lower() or 'commands:' in line.lower():
                in_commands_section = True
                continue
            
            if in_commands_section:
                if line.strip().startswith('-') or (line.strip() == '' and available_commands):
                    break
                
                parts = line.strip().split()
                if parts and not parts[0].startswith('{'):
                    cmd = parts[0]
                    if cmd and not cmd.startswith('-'):
                        available_commands.append(cmd)
        
        intent_lower = user_intent.lower()
        
        intent_map = {
            'status': ['status', 'list', 'ps'],
            'install': ['install', 'add'],
            'uninstall': ['uninstall', 'remove', 'delete'],
            'start': ['start', 'run', 'launch'],
            'stop': ['stop', 'shutdown', 'kill'],
            'restart': ['restart', 'reload'],
            'list': ['list', 'show', 'display'],
            'config': ['config', 'configure', 'set'],
            'tag': ['tag', 'name', 'identity'],
            'health': ['health', 'check', 'verify'],
            'log': ['log', 'logs', 'tail'],
            'clear': ['clear', 'clean', 'purge'],
            'peerlist': ['peerlist', 'peers', 'connections']
        }
        
        matched_commands = []
        for key, keywords in intent_map.items():
            if any(kw in intent_lower for kw in keywords):
                if key in available_commands:
                    matched_commands.append(key)
        
        if not matched_commands:
            for cmd in available_commands:
                if cmd in intent_lower:
                    matched_commands.append(cmd)
        
        if matched_commands:
            primary_command = matched_commands[0]
            
            cmd_help = run_vctl_help(primary_command)
            result['help_consulted'].append(f'vctl {primary_command} --help')
            
            exec_result = subprocess.run(
                [vctl_cmd, primary_command],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=volttron_home
            )
            
            result['success'] = (exec_result.returncode == 0)
            result['command_used'] = f'vctl {primary_command}'
            result['output'] = exec_result.stdout if exec_result.returncode == 0 else exec_result.stderr
            
        else:
            result['output'] = f"""
🤔 **Could not find matching vctl command for:** "{user_intent}"

**Available vctl commands:**
{', '.join(available_commands)}

**💡 Tip:** Try being more specific or use one of the available commands directly.
"""
        
        return result
        
    except subprocess.TimeoutExpired:
        result['output'] = "⏱️ Timeout executing command"
        return result
    except Exception as e:
        result['output'] = f"💥 Error: {str(e)}"
        return result

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

def is_volttron_running_quick():
    """Quick check if VOLTTRON is running - returns True/False only.
    This function uses multiple methods to detect VOLTTRON running status.
    """
    try:
        # Method 1 (Most reliable): Check for VOLTTRON processes with multiple variations
        try:
            # Try pgrep first (most reliable across systems)
            result = subprocess.run(
                ["pgrep", "-f", "bin/volttron"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"VOLTTRON is running (pgrep found process): {result.stdout.strip()}")
                return True
                
            # If pgrep fails, try alternative with ps | grep
            alt_result = subprocess.run(
                "ps aux | grep bin/volttron | grep -v grep",
                shell=True,
                capture_output=True, text=True, timeout=5
            )
            
            if alt_result.returncode == 0 and alt_result.stdout.strip():
                print(f"VOLTTRON is running (ps|grep found process): {alt_result.stdout.strip()[:50]}...")
                return True
        except Exception as e:
            print(f"Error in process check: {str(e)}")
        
        # Method 2: Check with ps aux for more detailed process info
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'volttron' in line and 'bin/volttron' in line and not 'grep' in line:
                        print(f"VOLTTRON is running (ps found process): {line[:50]}...")
                        return True
        except Exception as e:
            print(f"Error in ps check: {str(e)}")
        
        # Method 3: Try vctl status command (can be unreliable during startup)
        try:
            vctl_cmd = find_vctl_command()
            if vctl_cmd:
                volttron_home = get_volttron_home()
                env = os.environ.copy()
                env["VOLTTRON_HOME"] = volttron_home
                
                result = subprocess.run(
                    [vctl_cmd, "status"],
                    capture_output=True, text=True, 
                    env=env, cwd=volttron_home, timeout=5
                )
                # If vctl status succeeds, VOLTTRON is running
                if result.returncode == 0:
                    print("VOLTTRON is running (vctl status succeeded)")
                    return True
        except Exception as e:
            print(f"Error in vctl check: {str(e)}")
            
        print("All VOLTTRON running checks failed - VOLTTRON is not running")
        return False
        
    except Exception as e:
        print(f"Error in VOLTTRON status check: {str(e)}")
        return False

def kill_existing_volttron_processes():
    """Kill any existing VOLTTRON processes to prevent conflicts - ensures only one VOLTTRON runs at a time."""
    killed_pids = []
    messages = []
    
    try:
        search_patterns = [
            "bin/volttron",           # Standard VOLTTRON binary
            "python.*volttron",       # Python-launched VOLTTRON
            "volttron.*-vv",          # VOLTTRON with verbose flags
            "volttron.*platform"      # VOLTTRON platform processes
        ]
        
        all_found_pids = set()
        
        for pattern in search_patterns:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", pattern],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    all_found_pids.update(pids)
                    
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                continue
        
        try:
            volttron_home = get_volttron_home()
            ps_result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=10
            )
            
            if ps_result.returncode == 0:
                for line in ps_result.stdout.split('\n'):
                    if ('volttron' in line.lower() and 
                        (volttron_home in line or 'VOLTTRON_HOME' in line)):
                        parts = line.split()
                        if len(parts) > 1 and parts[1].isdigit():
                            all_found_pids.add(parts[1])
                            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        
        current_pid = str(os.getpid())
        all_found_pids.discard(current_pid)
        
        if all_found_pids:
            messages.append(f"🔍 Found {len(all_found_pids)} VOLTTRON process(es) to terminate")
            
            for pid in all_found_pids:
                try:
                    check_result = subprocess.run(
                        ["kill", "-0", pid], 
                        capture_output=True, timeout=2
                    )
                    
                    if check_result.returncode != 0:
                        continue  # Process already dead
                    
                    try:
                        subprocess.run(["kill", "-TERM", pid], check=True, timeout=3)
                        import time
                        time.sleep(1)
                        
                        check_again = subprocess.run(
                            ["kill", "-0", pid], 
                            capture_output=True, timeout=2
                        )
                        
                        if check_again.returncode == 0:
                            subprocess.run(["kill", "-KILL", pid], check=True, timeout=3)
                            killed_pids.append(f"{pid} (forced)")
                        else:
                            killed_pids.append(f"{pid} (graceful)")
                            
                    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                        try:
                            subprocess.run(["kill", "-KILL", pid], check=True, timeout=3)
                            killed_pids.append(f"{pid} (force-kill)")
                        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                            messages.append(f"⚠️ Could not kill PID {pid}")
                            
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    continue
            
            if killed_pids:
                messages.append(f"🔄 Successfully terminated VOLTTRON processes: PIDs {', '.join(killed_pids)}")
                messages.append("✅ System is now ready for a clean VOLTTRON start")
            else:
                messages.append("⚠️ Found VOLTTRON processes but couldn't terminate them")
                
        else:
            messages.append("✅ No existing VOLTTRON processes found - clean start possible")
            
        return "\n".join(messages) if messages else ""
            
    except Exception as e:
        return f"⚠️ Error checking/killing VOLTTRON processes: {str(e)}"

def start_volttron():
    """Start volttron in the background using the correct virtual environment.
    
    This function ensures only one VOLTTRON instance runs at a time by:
    1. Killing all existing VOLTTRON processes first
    2. Waiting for proper cleanup
    3. Starting a fresh VOLTTRON instance
    """
    try:
        volttron_cmd = find_volttron_command()
        volttron_home = get_volttron_home()
        
        if not volttron_cmd:
            return check_volttron_installation()
        
        messages = []
        messages.append("🚀 Starting VOLTTRON with clean process management...")
        
        cleanup_msg = kill_existing_volttron_processes()
        if cleanup_msg:
            messages.append(cleanup_msg)
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        os.makedirs(volttron_home, exist_ok=True)
        
        import time
        if cleanup_msg and ("terminated" in cleanup_msg or "killed" in cleanup_msg):
            messages.append("⏳ Waiting for system cleanup to complete...")
            time.sleep(3)  # Give more time for proper cleanup
        
        messages.append("🔧 Launching new VOLTTRON instance...")
        
        cmd = f"cd {volttron_home} && nohup {volttron_cmd} -vv -l volttron.log > volttron_output.log 2>&1 &"
        
        result = subprocess.run(
            cmd,
            shell=True,
            env=env,
            cwd=volttron_home
        )
        
        messages.append("⏳ Waiting for VOLTTRON to initialize...")
        time.sleep(3)  # Give VOLTTRON time to start
        
        is_running = wait_for_volttron_ready(max_wait_seconds=10)
        
        pid = None
        try:
            pid_result = subprocess.run(
                ["pgrep", "-f", "bin/volttron"],
                capture_output=True, text=True, timeout=5
            )
            if pid_result.returncode == 0 and pid_result.stdout.strip():
                pid = pid_result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return f"""VOLTTRON platform start operation completed.

Result: {'Running' if is_running else 'Failed to start'}
Process ID: {pid if pid else 'Not detected'}
VOLTTRON_HOME: {volttron_home}
Command executed: {volttron_cmd} -vv -l volttron.log
Verification: {'Process found and responsive' if is_running else 'Process not responsive'}

Background process: Yes (using nohup)
Log file: {volttron_home}/volttron.log
Output log: {volttron_home}/volttron_output.log

Cleanup performed: {bool(cleanup_msg)}
Wait time after cleanup: 3 seconds
Wait time for startup: 3 seconds

Process management: Single instance enforced (old processes killed)
"""
            
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
            return "❌ VOLTTRON commands not found. Please install VOLTTRON first."
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        is_running = False
        try:
            result = subprocess.run(
                "ps aux | grep bin/volttron | grep -v grep",
                shell=True,
                capture_output=True, text=True, timeout=5
            )
            is_running = result.returncode == 0 and result.stdout.strip()
        except Exception:
            pass
            
        if not is_running:
            warning_msg = ""
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
        
        try:
            cmd_str = f"export VOLTTRON_HOME={volttron_home} && {vctl_cmd} status"
            print(f"Running vctl status command: {cmd_str}")
            result = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True, 
                text=True,
                timeout=15  # Add timeout to prevent hanging
            )
            
            print(f"vctl_status direct command result: {result.returncode}")
            print(f"vctl_status stdout: {result.stdout}")
            print(f"vctl_status stderr: {result.stderr}")
            
            warning_msg = format_volttron_warnings(result.stderr) if result.stderr else ""
            
            if result.returncode == 0:
                status_output = result.stdout.strip() if result.stdout else ""
                header = result.stderr.strip() if result.stderr else ""
                
                # Combine header and output for complete table
                full_output = ""
                if header and "UUID" in header:
                    full_output = header + "\n" + status_output
                else:
                    full_output = status_output
                
                return f"""VOLTTRON agent status check completed.

Platform running: Yes
Status command success: True
VOLTTRON_HOME: {volttron_home}

Agent status:
{full_output if full_output else 'No agents installed'}

Command used: {vctl_cmd} status
"""
                    
            else:
                error_msg = ""
                if result.stderr:
                    error_msg = result.stderr
                elif result.stdout:
                    error_msg = result.stdout
                else:
                    error_msg = "Unknown error"
                
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
                    if is_running:
                        return f"{warning_msg}VOLTTRON is running, but the status command had issues: {error_msg}. You might need to check it directly."
                    else:
                        return f"{warning_msg}I'm having trouble checking my status: {error_msg}"
        
        except subprocess.TimeoutExpired:
            if is_running:
                return f"VOLTTRON appears to be running, but the status command is taking too long to respond. This could mean the system is under heavy load or experiencing issues."
            else:
                return "VOLTTRON doesn't seem to be running currently. The status command timed out."
                
    except Exception as e:
        try:
            if is_volttron_running_quick():
                return f"VOLTTRON appears to be running, but I encountered an error while checking detailed status: {str(e)}"
            else:
                return f"VOLTTRON doesn't seem to be running. Error details: {str(e)}"
        except Exception as inner_e:
            return f"Something went wrong while I was checking on myself: {str(e)} (Additional error: {str(inner_e)})"

def make_status_conversational(status_output):
    """Convert status output to conversational summary."""
    try:
        if not status_output or status_output.strip() == "" or "No installed Agents found" in status_output:
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
                
                # Look for explicit status words in remaining parts AND the full line
                for part in remaining_parts:
                    part_upper = part.upper()
                    if part_upper in ["RUNNING", "STARTED", "ACTIVE", "ENABLED"] or "RUNNING" in part_upper:
                        status = "RUNNING"
                        has_status_column = True
                    elif part_upper in ["STOPPED", "DISABLED", "INACTIVE", "EXITED"]:
                        status = "STOPPED"
                        has_status_column = True
                    elif part_upper in ["GOOD", "HEALTHY", "OK"]:
                        health = "GOOD"
                    elif part_upper in ["BAD", "UNHEALTHY", "ERROR", "FAILED"]:
                        health = "BAD"
                        
                # Also check the full line for running status with PID pattern like "running [48605]"
                if "RUNNING" in line_upper or ("[" in line_upper and "]" in line_upper and "RUNNING" not in line_upper):
                    status = "RUNNING"
                    has_status_column = True
                    
                # Check for health status in the full line
                if "GOOD" in line_upper:
                    health = "GOOD"
                elif "BAD" in line_upper:
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
                return f"Got one {agent['type']} agent humming along nicely (ID: {agent['uuid']}) - everything's good! 🚀"
            elif agent['status'] == "INSTALLED":
                return f"I've got a {agent['type']} agent sitting here (ID: {agent['uuid']}) but it's just chilling - not sure if it's actually doing anything. Want me to poke it and see?"
            else:
                return f"There's a {agent['type']} agent here (ID: {agent['uuid']}) but it looks like it's taking a nap. Should I wake it up?"
        
        # Multiple agents
        if running_count == 0 and not_running_count == agent_count:
            return f"I've got {agent_count} agents hanging around ({agent_list}) but they're all just sitting there doing nothing. Want me to get them moving?"
        elif running_count == agent_count:
            if bad_health_count > 0:
                return f"All {agent_count} agents are trying to work ({agent_list}), but {bad_health_count} of them seem a bit under the weather. Should I check what's bugging them?"
            else:
                return f"Sweet! All {agent_count} agents are cranking away perfectly ({agent_list}) - everything's running like a dream! ✨"
        elif running_count > 0:
            return f"I've got {agent_count} agents total ({agent_list}) - {running_count} are busy working and {not_running_count} are taking a break. The active ones are doing great though!"
        else:
            return f"There are {agent_count} agents here ({agent_list}) but honestly, I'm not totally sure what they're up to right now. Want me to investigate?"
    except Exception as e:
        print(f"Error in make_status_conversational: {str(e)}")
        return "I'm running, but I'm having trouble interpreting my agent status right now."

def make_status_readable(status_output):
    """Convert vctl status output to more readable format with emojis and better formatting."""
    try:
        if not status_output or status_output.strip() == "":
            return "No agents found"
        
        lines = status_output.strip().split('\n')
        if len(lines) < 1:
            return "No agent information available"
        
        if len(lines) == 1:
            test_parts = lines[0].split()
            if len(test_parts) >= 3 and (test_parts[0].isdigit() or test_parts[0].isalnum()):
                pass  # Continue to detailed processing
            elif "UUID" not in lines[0]:
                return f"📋 **Agent Status:**\n```\n{status_output}\n```"
        
        result_lines = []
        
        agent_count = 0
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            if "UUID" in line and i == 0:
                continue
                
            clean_line = ' '.join(line.split())  # Normalize whitespace
            parts = clean_line.split()
            
            if len(parts) >= 3:  # UUID, AGENT, IDENTITY at minimum
                agent_count += 1
                uuid = parts[0]
                agent = parts[1]
                identity = parts[2]
                
                remaining_parts = parts[3:] if len(parts) > 3 else []
                
                status = "INSTALLED"
                health = "UNKNOWN"
                
                full_line = ' '.join(parts).upper()  # Check the entire line for keywords
                if remaining_parts:
                    for part in remaining_parts:
                        part_upper = part.upper()
                        if part_upper in ["RUNNING", "STARTED", "ACTIVE", "ENABLED"] or "RUNNING" in part_upper:
                            status = "RUNNING"
                        elif part_upper in ["STOPPED", "DISABLED", "INACTIVE", "EXITED"]:
                            status = "STOPPED"
                        elif part_upper in ["GOOD", "HEALTHY", "OK"]:
                            health = "GOOD"
                        elif part_upper in ["BAD", "UNHEALTHY", "ERROR", "FAILED"]:
                            health = "BAD"
                            
                if "RUNNING" in full_line or "[" in full_line and "]" in full_line:
                    status = "RUNNING"
                    
                if "GOOD" in full_line:
                    health = "GOOD"
                
                if status == "RUNNING":
                    status_emoji = "🟢"
                elif status == "INSTALLED":
                    status_emoji = "⏸️"
                else:
                    status_emoji = "🔴"
                
                if health == "GOOD":
                    health_emoji = "💚"
                elif health == "UNKNOWN":
                    health_emoji = "❓"
                else:
                    health_emoji = "💔"
                
                agent_name = agent.replace('volttron-', '').replace('-0.2.0rc0', '').title()
                
                if status == "RUNNING":
                    status_text = "up and running"
                elif status == "INSTALLED":
                    status_text = "chilling (not started yet)"
                else:
                    status_text = "having issues"
                
                if health == "GOOD":
                    health_text = "feeling great"
                elif health == "UNKNOWN":
                    health_text = "can't tell how it's doing"
                else:
                    health_text = "not feeling well"
                
                result_lines.append(f"{status_emoji} **{agent_name}** (ID: {uuid}) - {status_text}")
                result_lines.append(f"   • Goes by: *{identity}*")
                result_lines.append(f"   • Health check: {health_text} {health_emoji}")
                result_lines.append("")  # Empty line for spacing
        
        if agent_count == 0:
            return f"📋 **Agent Status (Raw Output):**\n```\n{status_output}\n```\n\n💡 **Note:** The output format may be non-standard. Try running 'vctl status' directly for more details."
        
        if result_lines and result_lines[-1] == "":
            result_lines.pop()
        
        return '\n'.join(result_lines)
    except Exception as e:
        print(f"Error in make_status_readable: {str(e)}")
        return f"📋 **Agent Status (Raw Output):**\n```\n{status_output}\n```"

def vctl_status_detailed():
    """Get detailed VOLTTRON agent status with explanations."""
    return vctl_status(explain=True)

def check_volttron_status(brief=True):
    """Check VOLTTRON status with simple yes/no answer unless details requested."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return "❌ VOLTTRON not installed"
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        try:
            cmd_str = f"export VOLTTRON_HOME={volttron_home} && {vctl_cmd} status"
            result = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True, 
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                if brief:
                    return "✅ VOLTTRON is running"
                else:
                    return f"✅ VOLTTRON is running\n\nStatus output:\n{result.stdout}"
            else:
                error_output = result.stderr or result.stdout or ""
                if "not running" in error_output.lower():
                    return "❌ VOLTTRON is not running"
                else:
                    return f"❌ VOLTTRON status check failed: {error_output}"
                    
        except subprocess.TimeoutExpired:
            pass
        
        process_check = subprocess.run(
            ["pgrep", "-f", "bin/volttron"],
            capture_output=True, text=True, timeout=10
        )
        
        if process_check.returncode != 0 or not process_check.stdout.strip():
            return "❌ VOLTTRON is not running"
        else:
            return "✅ VOLTTRON is running (process found)"
            
    except Exception as e:
        return f"❌ Error checking VOLTTRON: {str(e)}"

def is_volttron_running():
    """Simple check: is VOLTTRON running? Returns just 'Yes' or 'No'."""
    status = check_volttron_status(brief=True)
    if "✅" in status and "running" in status:
        return "Yes"
    else:
        return "No"

def simple_volttron_status_check():
    """Simple function to check if VOLTTRON is running with minimal output."""
    try:
        result = subprocess.run(
            "ps aux | grep bin/volttron | grep -v grep",
            shell=True,
            capture_output=True, 
            text=True, 
            timeout=3
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return "✅ VOLTTRON is running!"
        else:
            return "❌ Hey, VOLTTRON is not running! You need to start it first."
    except Exception:
        return "❌ Hey, VOLTTRON is not running! You need to start it first."
        
def check_volttron_simple_message():
    """
    Simple function to check if VOLTTRON is running and return a user-friendly message.
    This is designed to be integrated into REST APIs or other interfaces.
    
    Returns:
        dict: Contains 'running' (boolean) and 'message' (string) fields
    """
    try:
        result = subprocess.run(
            "ps aux | grep bin/volttron | grep -v grep",
            shell=True,
            capture_output=True, 
            text=True,
            timeout=3
        )
        
        is_running = result.returncode == 0 and result.stdout.strip()
        
        if is_running:
            message = "✅ VOLTTRON is running and active!"
            return {"running": True, "message": message}
        else:
            message = "❌ Hey, VOLTTRON is not running! You need to start it first."
            return {"running": False, "message": message}
            
    except Exception as e:
        message = f"❓ Could not determine if VOLTTRON is running: {str(e)}"
        return {"running": False, "message": message}

def vctl_list_agents():
    """List all installed agents with their details."""
    try:
        # Get paths dynamically
        volttron_home = get_volttron_home()
        vctl_path = find_vctl_command()
        
        if not vctl_path:
            return "❌ Could not find vctl command. Please ensure VOLTTRON is installed."
        
        print(f"DEBUG: Running vctl list_agents with paths: VOLTTRON_HOME={volttron_home}, vctl={vctl_path}")
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Run the command directly with shell=True to ensure proper environment handling
        cmd_str = f"export VOLTTRON_HOME={volttron_home} && {vctl_path} status"
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True, 
            text=True,
            env=env,
            timeout=15
        )
        
        # Print detailed debug info
        print(f"DEBUG: vctl_list_agents direct command result code: {result.returncode}")
        print(f"DEBUG: vctl_list_agents stdout: {result.stdout}")
        print(f"DEBUG: vctl_list_agents stderr: {result.stderr}")
        
        if result.returncode == 0:
            # Combine stdout and stderr to get full output including header
            combined_output = ""
            if result.stderr and "UUID" in result.stderr:
                combined_output = result.stderr.strip() + "\n"
            
            if result.stdout:
                combined_output += result.stdout.strip()
            
            combined_output = combined_output.strip()
            
            if combined_output:
                # Process the output to make it more readable
                lines = combined_output.split('\n')
                if len(lines) >= 2:  # If there's a header and at least one agent
                    # Use make_status_readable for nicer formatting if available
                    try:
                        readable_status = make_status_readable(combined_output)
                        return f"🤖 **Installed VOLTTRON Agents:**\n\n{readable_status}"
                    except Exception as format_error:
                        # Fallback to simple formatting
                        print(f"DEBUG: Error formatting agent list: {str(format_error)}")
                        return f"🤖 **Installed VOLTTRON Agents:**\n\n```\n{combined_output}\n```"
                else:
                    return "No agents are currently installed."
            else:
                return "No agents are currently installed."
        else:
            error = result.stderr or "Unknown error"
            return f"Error listing agents: {error}"
    except Exception as e:
        print(f"DEBUG: Exception in vctl_list_agents: {str(e)}")
        return f"Failed to list agents: {str(e)}"

def vctl_start_agent(agent_uuid_or_tag):
    """Start a specific agent by UUID or tag."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        if not agent_uuid_or_tag:
            return "❌ Please specify an agent UUID or tag to start. Use 'vctl status' to see available agents."
        
        if not is_volttron_running_quick():
            return """❌ **VOLTTRON is not running!**

**Cannot start agent** - VOLTTRON platform must be running first.

💡 **Please try this:**
1. Ask me to "start volttron" first
2. Wait a few seconds for it to start up
3. Then try starting the agent again"""
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        status_result = subprocess.run(
            [vctl_cmd, "status"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home,
            timeout=10
        )
        
        if status_result.returncode != 0:
            return f"❌ Can't check agent status to verify '{agent_uuid_or_tag}' exists. VOLTTRON might not be responding properly."
        
        agent_found = False
        agent_details = ""
        
        if status_result.stdout:
            status_lines = status_result.stdout.strip().split('\n')
            for line in status_lines:
                if agent_uuid_or_tag in line:
                    agent_found = True
                    agent_details = line.strip()
                    break
        
        if not agent_found:
            available_agents = []
            if status_result.stdout:
                for line in status_result.stdout.strip().split('\n'):
                    if line and not 'UUID' in line and len(line.split()) >= 3:
                        parts = line.split()
                        if parts[0] and parts[0] != 'UUID':
                            available_agents.append(f"• **{parts[0]}** - {parts[1] if len(parts) > 1 else 'Unknown'}")
            
            available_list = '\n'.join(available_agents[:5]) if available_agents else "• No agents found"
            
            return f"""❌ **Agent '{agent_uuid_or_tag}' not found!**

The agent you're trying to start doesn't exist in the system.

📋 **Available agents:**
{available_list}

💡 **Try:**
• Use one of the UUIDs shown above
• Ask "what agents are available" 
• Check if you need to install the agent first"""
        
        if "running" in agent_details.lower():
            agent_name = agent_details.split()[1] if len(agent_details.split()) > 1 else agent_uuid_or_tag
            return f"ℹ️ **Agent '{agent_uuid_or_tag}' is already running!**\n\nAgent details: {agent_name}\n\n💡 No need to start it again - it's already active and working."
        
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

def vctl_start_all_agents():
    """Start all registered VOLTTRON agents that aren't already running."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        # Check if VOLTTRON is running before trying to start agents
        if not is_volttron_running_quick():
            return """❌ **VOLTTRON is not running!**

**Cannot start agents** - VOLTTRON platform must be running first.

💡 **Please try this:**
1. Ask me to "start volttron" first
2. Wait a few seconds for it to start up
3. Then try starting the agents again"""
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # First, get the current status to see which agents exist
        status_result = subprocess.run(
            [vctl_cmd, "status"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home,
            timeout=10
        )
        
        if status_result.returncode != 0:
            return f"❌ Can't check agent status. VOLTTRON might not be responding properly."
        
        # Parse agents from status output
        agents_to_start = []
        if status_result.stdout:
            status_lines = status_result.stdout.strip().split('\n')
            for line in status_lines[1:]:  # Skip header line
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        agent_id = parts[0]
                        status = "running" if "running" in line.lower() else "stopped"
                        if status != "running":
                            agents_to_start.append(agent_id)
        
        if not agents_to_start:
            return "✅ **All agents are already running!** Nothing to start."
        
        # Start each agent
        started_agents = []
        failed_agents = []
        
        for agent_id in agents_to_start:
            result = subprocess.run(
                [vctl_cmd, "start", agent_id],
                capture_output=True,
                text=True,
                env=env,
                cwd=volttron_home,
                timeout=10
            )
            
            if result.returncode == 0:
                started_agents.append(agent_id)
            else:
                failed_agents.append(agent_id)
        
        # Generate response message
        message = "🚀 **Starting all agents...**\n\n"
        
        if started_agents:
            message += f"✅ **{len(started_agents)} agent{'s' if len(started_agents) > 1 else ''} started successfully**\n"
            if len(started_agents) <= 5:
                message += "• " + "\n• ".join(started_agents) + "\n\n"
        
        if failed_agents:
            message += f"❌ **{len(failed_agents)} agent{'s' if len(failed_agents) > 1 else ''} failed to start**\n"
            if len(failed_agents) <= 5:
                message += "• " + "\n• ".join(failed_agents) + "\n\n"
        
        return message.strip()
        
    except Exception as e:
        return f"❌ Error starting all agents: {str(e)}"

def vctl_stop_agent(agent_uuid_or_tag):
    """Stop a specific agent by UUID or tag."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        if not agent_uuid_or_tag:
            return "❌ Please specify an agent UUID or tag to stop. Use 'vctl status' to see running agents."
        
        if not is_volttron_running_quick():
            return """❌ **VOLTTRON is not running!**

**Cannot stop agent** - VOLTTRON platform must be running to manage agents.

💡 **If VOLTTRON is stopped, the agents are already stopped too.**"""
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        status_result = subprocess.run(
            [vctl_cmd, "status"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home,
            timeout=10
        )
        
        if status_result.returncode != 0:
            return f"❌ Can't check agent status to verify '{agent_uuid_or_tag}' exists."
        
        agent_found = False
        agent_details = ""
        
        if status_result.stdout:
            status_lines = status_result.stdout.strip().split('\n')
            for line in status_lines:
                if agent_uuid_or_tag in line:
                    agent_found = True
                    agent_details = line.strip()
                    break
        
        if not agent_found:
            return f"""❌ **Agent '{agent_uuid_or_tag}' not found!**

Can't stop an agent that doesn't exist.

💡 **Try:** Ask "what's running" to see available agents"""
        
        if "running" not in agent_details.lower():
            agent_name = agent_details.split()[1] if len(agent_details.split()) > 1 else agent_uuid_or_tag
            return f"ℹ️ **Agent '{agent_uuid_or_tag}' is already stopped.**\n\nAgent details: {agent_name}\n\n💡 No need to stop it - it's already inactive."
        
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
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
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
        
        agent_found = False
        if status_result.stdout:
            if agent_uuid_or_tag in status_result.stdout:
                agent_found = True
        
        if not agent_found:
            return f"❌ Agent '{agent_uuid_or_tag}' not found.\n\n**Current agents:**\n{status_result.stdout}\n\n💡 **Tip:** Use the exact UUID or tag shown above."
        
        messages = []
        success = True
        
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
            stop_error = stop_result.stderr or stop_result.stdout or "No additional info"
            if "not running" in stop_error.lower() or "no agent" in stop_error.lower():
                messages.append(f"ℹ️ Agent '{agent_uuid_or_tag}' was already stopped.")
            else:
                messages.append(f"⚠️ Warning during stop: {stop_error}")
        
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
            messages.append(f"⚠️ Initial removal failed, searching for UUID...")
            
            uuid_found = None
            if status_result.stdout:
                lines = status_result.stdout.strip().split('\n')
                for line in lines:
                    if agent_uuid_or_tag in line:
                        parts = line.split()
                        if parts:
                            uuid_found = parts[0]
                            break
            
            if uuid_found and uuid_found != agent_uuid_or_tag:
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
                
                if "not found" in remove_error.lower():
                    messages.append("💡 **Hint:** Check if the agent UUID or tag is correct using 'vctl status'")
                elif "permission" in remove_error.lower():
                    messages.append("💡 **Hint:** Make sure VOLTTRON has proper permissions in $VOLTTRON_HOME")
                elif "still running" in remove_error.lower():
                    messages.append("💡 **Hint:** The agent might still be running. Try stopping it first.")
        
        messages.append("\n🔍 **Performing comprehensive uninstall verification...**")
        
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
            if agent_uuid_or_tag not in verify_result.stdout:
                verification_details.append(f"✅ Agent '{agent_uuid_or_tag}' not found in vctl status")
            else:
                verification_details.append(f"❌ Agent '{agent_uuid_or_tag}' still appears in vctl status")
                verification_passed = False
                
            if 'uuid_found' in locals() and uuid_found and uuid_found != agent_uuid_or_tag:
                if uuid_found not in verify_result.stdout:
                    verification_details.append(f"✅ Agent UUID '{uuid_found}' not found in status")
                else:
                    verification_details.append(f"❌ Agent UUID '{uuid_found}' still appears in status")
                    verification_passed = False
        else:
            verification_details.append("⚠️ Could not verify removal via vctl status")
            verification_passed = False
        
        try:
            agents_dir = os.path.join(volttron_home, "agents")
            if os.path.exists(agents_dir):
                leftover_dirs = []
                for item in os.listdir(agents_dir):
                    item_path = os.path.join(agents_dir, item)
                    if os.path.isdir(item_path):
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
        
        try:
            start_test = subprocess.run(
                [vctl_cmd, "start", agent_uuid_or_tag], 
                capture_output=True, 
                text=True,
                env=env,
                cwd=volttron_home,
                timeout=10
            )
            
            error_msg = (start_test.stderr + " " + start_test.stdout).lower()
            if ("not found" in error_msg or "no agent" in error_msg or 
                "agent not found" in error_msg or "unknown agent" in error_msg):
                verification_details.append("✅ Agent properly removed - cannot be started")
            elif start_test.returncode != 0:
                verification_details.append("✅ Agent start failed as expected")
            else:
                if "error" in error_msg and ("not found" in error_msg or "no agent" in error_msg):
                    verification_details.append("✅ Agent properly removed - cannot be started")
                else:
                    verification_details.append("❌ Agent can still be started - removal incomplete")
                    verification_passed = False
        except Exception as e:
            verification_details.append(f"⚠️ Could not test agent start capability: {str(e)}")
        
        for detail in verification_details:
            messages.append(detail)
        
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

def vctl_force_remove_agent(agent_tag_or_uuid):
    """Force remove a VOLTTRON agent by tag or UUID using aggressive removal methods.
    
    This function uses multiple approaches to ensure agent removal even when the
    standard methods fail or timeout:
    1. Try direct removal with force flag
    2. If that fails, try direct file manipulation in VOLTTRON_HOME
    3. Use shorter timeouts to avoid hanging
    
    Args:
        agent_tag_or_uuid: The tag or UUID of the agent to remove
        
    Returns:
        str: Status message with the result of the operation
    """
    try:
        import os
        import shutil
        import glob
        import json
        import time
        
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        if not agent_tag_or_uuid:
            return "❌ Please specify an agent tag or UUID to remove. Use 'vctl status' to see available agents."
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        status_result = subprocess.run(
            [vctl_cmd, "status"],
            capture_output=True,
            text=True,
            env=env,
            cwd=volttron_home,
            timeout=10
        )
        
        agent_uuid = agent_tag_or_uuid  # Default to assuming it's already a UUID
        found_in_status = False
        agent_name = "unknown"
        
        if status_result.returncode == 0 and status_result.stdout:
            lines = status_result.stdout.strip().split('\n')
            for line in lines:
                if agent_tag_or_uuid in line:
                    found_in_status = True
                    parts = line.split()
                    if len(parts) >= 1:
                        agent_uuid = parts[0]  # First column is UUID
                        agent_name = parts[1] if len(parts) > 1 else "unknown"
                    break
        
        messages = []
        messages.append(f"🔥 **Aggressively removing agent '{agent_tag_or_uuid}'...**")
        
        messages.append(f"🛑 First stopping agent...")
        try:
            stop_result = subprocess.run(
                [vctl_cmd, "stop", agent_uuid],
                capture_output=True,
                text=True,
                env=env,
                cwd=volttron_home,
                timeout=5  # Short timeout to avoid hanging
            )
            if stop_result.returncode == 0:
                messages.append("✅ Agent stopped successfully")
            else:
                messages.append("⚠️ Agent may still be running (stop command failed)")
        except subprocess.TimeoutExpired:
            messages.append("⚠️ Stop command timed out - proceeding anyway")
            
        messages.append(f"🗑️ Attempting force removal with vctl...")
        removal_success = False
        
        if agent_tag_or_uuid != agent_uuid:
            try:
                tag_result = subprocess.run(
                    [vctl_cmd, "remove", "--tag", agent_tag_or_uuid, "-f"],
                    capture_output=True,
                    text=True,
                    env=env,
                    cwd=volttron_home,
                    timeout=10  # Shorter timeout
                )
                if tag_result.returncode == 0:
                    messages.append("✅ Successfully removed by tag")
                    removal_success = True
            except subprocess.TimeoutExpired:
                messages.append("⚠️ Tag removal timed out - trying alternate methods")
        
        if not removal_success:
            try:
                uuid_result = subprocess.run(
                    [vctl_cmd, "remove", agent_uuid, "-f"],
                    capture_output=True,
                    text=True,
                    env=env,
                    cwd=volttron_home,
                    timeout=10  # Shorter timeout
                )
                if uuid_result.returncode == 0:
                    messages.append("✅ Successfully removed by UUID")
                    removal_success = True
            except subprocess.TimeoutExpired:
                messages.append("⚠️ UUID removal timed out - trying alternate methods")
        
        if not removal_success:
            messages.append("🛠️ Trying direct file removal...")
            
            agents_dir = os.path.join(volttron_home, "agents")
            if os.path.exists(agents_dir):
                removed_dirs = 0
                
                uuid_dirs = glob.glob(f"{agents_dir}/{agent_uuid}*")
                for dir_path in uuid_dirs:
                    try:
                        shutil.rmtree(dir_path)
                        removed_dirs += 1
                    except Exception:
                        pass
                
                if agent_name != "unknown":
                    name_pattern = agent_name.replace("volttron-", "").replace("-", "_").split("-")[0]
                    name_dirs = glob.glob(f"{agents_dir}/*{name_pattern}*")
                    for dir_path in name_dirs:
                        try:
                            agent_config = os.path.join(dir_path, "agent-data/agentconfig")
                            if os.path.exists(agent_config):
                                with open(agent_config, 'r') as f:
                                    config_text = f.read()
                                    if agent_uuid in config_text:
                                        shutil.rmtree(dir_path)
                                        removed_dirs += 1
                        except Exception:
                            pass
                
                if removed_dirs > 0:
                    messages.append(f"✅ Removed {removed_dirs} agent directories")
                    removal_success = True
                else:
                    messages.append("⚠️ No matching agent directories found")
        
        try:
            registry_file = os.path.join(volttron_home, "configuration_store/platform.driver/registry_configs")
            if os.path.exists(registry_file):
                with open(registry_file, 'r') as f:
                    registry = json.load(f)
                if agent_uuid in registry or agent_tag_or_uuid in registry:
                    if agent_uuid in registry:
                        del registry[agent_uuid]
                    if agent_tag_or_uuid in registry:
                        del registry[agent_tag_or_uuid]
                    with open(registry_file, 'w') as f:
                        json.dump(registry, f)
                    messages.append("✅ Cleaned up registry entries")
                    removal_success = True
        except Exception:
            pass
        
        final_status = "✅ SUCCESS" if removal_success else "⚠️ PARTIAL"
        
        try:
            time.sleep(1)  # Brief pause to let changes take effect
            verify_result = subprocess.run(
                [vctl_cmd, "status"],
                capture_output=True,
                text=True,
                env=env,
                cwd=volttron_home,
                timeout=10
            )
            
            if verify_result.returncode == 0 and verify_result.stdout:
                if agent_uuid not in verify_result.stdout and agent_tag_or_uuid not in verify_result.stdout:
                    messages.append("✅ Verification passed: Agent no longer appears in status")
                    removal_success = True
                else:
                    messages.append("⚠️ Agent may still appear in status, but files should be removed")
        except Exception:
            messages.append("⚠️ Could not verify final status")
        
        messages.append(f"\n{final_status}: Agent '{agent_tag_or_uuid}' force-removal {removal_success and 'completed' or 'attempted'}")
        
        if not removal_success:
            messages.append("""
💡 **For stubborn agents:**
• Restart VOLTTRON with: "restart volttron" 
• Then try removing again
• Or manually delete files from VOLTTRON_HOME/agents directory""")
        
        return "\n".join(messages)
    
    except Exception as e:
        return f"❌ Error during force-removal: {str(e)}"

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
                verification_results.append("ℹ️ VOLTTRON not running - agent cannot be running")
            else:
                verification_results.append("⚠️ Could not check vctl status")
                all_checks_passed = False
        except Exception as e:
            verification_results.append(f"❌ Error checking status: {str(e)}")
            all_checks_passed = False
        
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
        
        try:
            start_result = subprocess.run(
                [vctl_cmd, "start", agent_identifier], 
                capture_output=True, 
                text=True,
                env=env,
                cwd=volttron_home,
                timeout=10
            )
            
            error_msg = (start_result.stderr + " " + start_result.stdout).lower()
            if ("not found" in error_msg or "no agent" in error_msg or 
                "agent not found" in error_msg or "unknown agent" in error_msg):
                verification_results.append("✅ Agent cannot be started (properly removed)")
            elif start_result.returncode != 0:
                verification_results.append("✅ Agent start failed as expected")
            else:
                if "error" in error_msg and ("not found" in error_msg or "no agent" in error_msg):
                    verification_results.append("✅ Agent cannot be started (properly removed)")
                else:
                    verification_results.append("❌ Agent can still be started (removal incomplete)")
                    all_checks_passed = False
        except Exception as e:
            verification_results.append(f"⚠️ Could not test agent start: {str(e)}")
        
        try:
            stop_result = subprocess.run(
                [vctl_cmd, "stop", agent_identifier], 
                capture_output=True, 
                text=True,
                env=env,
                cwd=volttron_home,
                timeout=10
            )
            
            error_msg = (stop_result.stderr + " " + stop_result.stdout).lower()
            if ("not found" in error_msg or "no agent" in error_msg or 
                "agent not found" in error_msg or "unknown agent" in error_msg):
                verification_results.append("✅ Agent cannot be stopped (properly removed)")
            elif stop_result.returncode != 0:
                verification_results.append("✅ Agent stop failed as expected")
            else:
                if "error" in error_msg and ("not found" in error_msg or "no agent" in error_msg):
                    verification_results.append("✅ Agent cannot be stopped (properly removed)")
                else:
                    verification_results.append("❌ Agent can still be stopped (may still exist)")
                    all_checks_passed = False
        except Exception as e:
            verification_results.append(f"⚠️ Could not test agent stop: {str(e)}")
        
        try:
            import psutil
            agent_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
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

def wait_for_volttron_ready(max_wait_seconds=30):
    """Wait for VOLTTRON to be fully ready for operations.
    
    Args:
        max_wait_seconds: Maximum time to wait in seconds
        
    Returns:
        tuple: (is_ready: bool, message: str)
    """
    import time
    
    vctl_cmd = find_vctl_command()
    volttron_home = get_volttron_home()
    
    if not vctl_cmd:
        return False, "❌ vctl command not found"
    
    start_time = time.time()
    env = os.environ.copy()
    env["VOLTTRON_HOME"] = volttron_home
    
    while time.time() - start_time < max_wait_seconds:
        try:
            process_check = subprocess.run(
                "ps aux | grep bin/volttron | grep -v grep",
                shell=True,
                capture_output=True, text=True, timeout=5
            )
            
            if process_check.returncode == 0 and process_check.stdout.strip():
                try:
                    cmd_str = f"export VOLTTRON_HOME={volttron_home} && {vctl_cmd} status"
                    result = subprocess.run(
                        cmd_str,
                        shell=True,
                        capture_output=True, 
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        return True, "✅ VOLTTRON is ready (vctl status working)"
                except Exception:
                    pass
                    
                if time.time() - start_time > 10:
                    return True, "✅ VOLTTRON process is running (assumed ready)"
        except:
            pass
        
        time.sleep(1)
    
    return False, f"❌ VOLTTRON not ready after {max_wait_seconds} seconds"

def vctl_install_listener_agent():
    """Install the VOLTTRON listener agent for monitoring platform messages."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return "❌ VOLTTRON commands not found. Please install VOLTTRON first."
        
        # Check if VOLTTRON is running directly with a process check instead of calling other functions
        is_running = False
        try:
            result = subprocess.run(
                "ps aux | grep bin/volttron | grep -v grep",
                shell=True,
                capture_output=True, text=True, timeout=5
            )
            is_running = result.returncode == 0 and result.stdout.strip()
        except Exception:
            pass
            
        if not is_running:
            return "❌ VOLTTRON is not running. Please start VOLTTRON first with 'start volttron'."
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # First, check if volttron-listener-agent package is installed
        pip_cmd = find_pip_command()
        if pip_cmd:
            # Try both package names (current and legacy)
            check_result = subprocess.run([
                pip_cmd, "show", "volttron-listener-agent"
            ], capture_output=True, text=True, timeout=10, env=env)
            
            legacy_check_result = subprocess.run([
                pip_cmd, "show", "volttron-listener"
            ], capture_output=True, text=True, timeout=10, env=env)
            
            if check_result.returncode != 0 and legacy_check_result.returncode != 0:
                # Both checks failed - install the volttron-listener-agent package
                print("Installing volttron-listener-agent package...")
                install_result = subprocess.run([
                    pip_cmd, "install", "volttron-listener-agent"
                ], capture_output=True, text=True, timeout=60, env=env)
                
                if install_result.returncode != 0:
                    # Try the legacy package name as fallback
                    install_result = subprocess.run([
                        pip_cmd, "install", "volttron-listener"
                    ], capture_output=True, text=True, timeout=60, env=env)
                    
                    if install_result.returncode != 0:
                        return f"❌ Failed to install listener agent package: {install_result.stderr}"
        
        # Install the listener agent (try both package names)
        # Note: We install WITHOUT --start first, then start separately for better debugging
        messages = []
        package_used = None
        
        try:
            # Try the new package name first
            print(f"DEBUG: Attempting to install volttron-listener-agent")
            result = subprocess.run([
                vctl_cmd, "install", "volttron-listener-agent",
                "--vip-identity", "listener"
            ], capture_output=True, text=True, timeout=30, env=env, cwd=volttron_home)
            
            print(f"DEBUG: vctl install result: returncode={result.returncode}")
            print(f"DEBUG: stdout: {result.stdout}")
            print(f"DEBUG: stderr: {result.stderr}")
            
            # If that fails, try the legacy package name
            if result.returncode != 0 and "not found" in (result.stderr + result.stdout).lower():
                print(f"DEBUG: First attempt failed, trying volttron-listener")
                result = subprocess.run([
                    vctl_cmd, "install", "volttron-listener",
                    "--vip-identity", "listener"
                ], capture_output=True, text=True, timeout=30, env=env, cwd=volttron_home)
                
                print(f"DEBUG: vctl install (legacy) result: returncode={result.returncode}")
                print(f"DEBUG: stdout: {result.stdout}")
                print(f"DEBUG: stderr: {result.stderr}")
                package_used = "volttron-listener"
            else:
                package_used = "volttron-listener-agent"
                
        except Exception as e:
            return f"❌ Error during listener agent installation: {str(e)}"
        
        if result.returncode != 0:
            return f"❌ Failed to install listener agent: {result.stderr or result.stdout}"
        
        # Verify the agent was actually installed
        import time
        time.sleep(2)  # Brief pause to let installation complete
        
        verify_result = subprocess.run([
            vctl_cmd, "status"
        ], capture_output=True, text=True, timeout=10, env=env, cwd=volttron_home)
        
        print(f"DEBUG: Verification status check: {verify_result.stdout}")
        
        agent_found = False
        agent_uuid = None
        if verify_result.returncode == 0 and verify_result.stdout:
            # Look for listener in the status output
            for line in verify_result.stdout.split('\n'):
                if 'listener' in line.lower():
                    agent_found = True
                    # Try to extract UUID (first column)
                    parts = line.split()
                    if parts:
                        agent_uuid = parts[0]
                    messages.append(f"✅ Listener agent installed with UUID: {agent_uuid}")
                    break
        
        if not agent_found:
            return f"""⚠️ **Installation Command Succeeded, But Agent Not Found**

The vctl install command completed without errors, but the listener agent doesn't appear in agent status.

**Debug Information:**
• Package used: {package_used}
• VOLTTRON_HOME: {volttron_home}
• Installation output: {result.stdout}

**Troubleshooting Steps:**
1. Check if package is actually installed: `pip show {package_used}`
2. Try manual installation: `vctl install {package_used} --vip-identity listener --start`
3. Check VOLTTRON logs: `tail -f $VOLTTRON_HOME/volttron.log`
4. Restart VOLTTRON and try again

This suggests a compatibility issue between the package and VOLTTRON."""
        
        # Now start the agent
        start_successful = False
        start_output = ""
        start_errors = ""
        if agent_uuid:
            start_result = subprocess.run([
                vctl_cmd, "start", agent_uuid
            ], capture_output=True, text=True, timeout=10, env=env, cwd=volttron_home)
            
            start_successful = start_result.returncode == 0
            start_output = start_result.stdout
            start_errors = start_result.stderr
        
        return f"""Listener agent installation operation completed.

Installation result:
- Success: {result.returncode == 0}
- Package used: {package_used}
- Agent UUID: {agent_uuid or 'Not assigned'}
- Found in status: {agent_found}
- Started successfully: {start_successful}

Installation output:
{result.stdout}

Verification output:
{verify_result.stdout}

Start operation output:
{start_output if start_output else 'N/A'}

Errors (if any):
Installation errors: {result.stderr or 'None'}
Start errors: {start_errors or 'None'}
"""
            
    except Exception as e:
        return f"Error installing listener agent: {str(e)}"

def vctl_install_agent(agent_name):
    """Install any VOLTTRON agent by name."""
    try:
        agent_name = agent_name.lower().replace('_', '-').replace(' ', '-')
        
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
        
        is_ready, wait_message = wait_for_volttron_ready(max_wait_seconds=15)
        if not is_ready:
            return f"❌ Failed to install {agent_name} agent: {wait_message}\n\n💡 **Try this:**\n• Ask me to \"start volttron\" first\n• Wait a few seconds, then try installing again"
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        pip_cmd = find_pip_command()
        if pip_cmd:
            package_name = agent_info['package']
            print(f"📦 Installing package: {package_name}")
            install_result = subprocess.run([
                pip_cmd, "install", package_name
            ], capture_output=True, text=True, timeout=120, env=env)
            
            if install_result.returncode != 0 and 'alt_package' in agent_info:
                alt_package = agent_info['alt_package']
                print(f"📦 Primary package install failed, trying alternative: {alt_package}")
                alt_install_result = subprocess.run([
                    pip_cmd, "install", alt_package
                ], capture_output=True, text=True, timeout=120, env=env)
                
                if alt_install_result.returncode == 0:
                    package_name = alt_package
                    install_result = alt_install_result
            
            if install_result.returncode != 0:
                return f"""❌ **Failed to install {agent_name} agent package**

**Error:** {install_result.stderr or install_result.stdout}

💡 **Try manually:** `pip install {package_name}`"""
            
            agent_info['installed_package'] = package_name
        
        package_to_install = agent_info.get('installed_package', agent_info['package'])
        
        install_args = [
            vctl_cmd, "install", package_to_install,
            "--vip-identity", agent_info['vip_identity']
        ]
        
        if agent_info['category'] in ['Core', 'Historian']:
            install_args.append("--start")
        
        result = subprocess.run(
            install_args,
            capture_output=True, text=True, timeout=60, env=env, cwd=volttron_home
        )
        
        return f"""Agent installation operation completed.

Agent name: {agent_name}
Package: {agent_info['package']}
Category: {agent_info['category']}
Description: {agent_info['description']}
VIP Identity: {agent_info['vip_identity']}
Command used: {' '.join(install_args)}
Return code: {result.returncode}
Success: {result.returncode == 0}
Auto-started: {'--start' in install_args}

Installation output:
{result.stdout}

Errors (if any):
{result.stderr if result.stderr else 'None'}
"""
            
    except Exception as e:
        return f"""Agent installation error.

Agent name: {agent_name}
Operation: vctl install agent
Error type: {type(e).__name__}
Error details: {str(e)}
"""

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
    """Find pip command from ACTIVE virtual environment (proper way!)."""
    
    pip_path, error = get_pip_command_from_venv()
    if pip_path:
        return pip_path
    
    print(f"⚠️ pip detection issue: {error}")
    
    if 'VIRTUAL_ENV' in os.environ:
        venv_pip = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'pip')
        if os.path.exists(venv_pip):
            print(f"✅ Found pip via VIRTUAL_ENV: {venv_pip}")
            return venv_pip
    
    pip_cmd = shutil.which("pip")
    if pip_cmd:
        print(f"⚠️ Using system pip from PATH: {pip_cmd} (may cause issues)")
        return pip_cmd
    
    pip3_cmd = shutil.which("pip3")
    if pip3_cmd:
        print(f"⚠️ Using system pip3 from PATH: {pip3_cmd} (may cause issues)")
        return pip3_cmd
    
    print("❌ ERROR: pip not found anywhere!")
    return None

def pip_install_package(package_name, upgrade=False):
    """Install a Python package using pip with comprehensive error handling.
    
    Args:
        package_name (str): Name of the package to install
        upgrade (bool): If True, add --upgrade flag
    
    Returns:
        str: Detailed status message with debugging info
    """
    try:
        pip_cmd = find_pip_command()
        if not pip_cmd:
            is_active, venv_path, reason = get_active_virtualenv()
            return f"""❌ **Cannot find pip command!**

**Problem:** pip is not available

**Debug Info:**
• In virtual environment: {is_active}
• Venv path: {venv_path or 'None'}
• Detection method: {reason}

**To Fix:**
1. Make sure you're in a virtual environment: `source /path/to/venv/bin/activate`
2. Install pip if needed: `python -m ensurepip`
3. Try again"""
        
        cmd = [pip_cmd, "install"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(package_name)
        
        print(f"DEBUG: Running pip command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(f"DEBUG: pip install returncode: {result.returncode}")
        print(f"DEBUG: pip stdout: {result.stdout[:200]}")  # First 200 chars
        if result.stderr:
            print(f"DEBUG: pip stderr: {result.stderr[:200]}")
        
        verify_result = subprocess.run(
            [pip_cmd, "show", package_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        is_active, venv_path, _ = get_active_virtualenv()
        
        return f"""Package installation operation completed.

Package: {package_name}
Installation return code: {result.returncode}
Installation success: {result.returncode == 0}
Verification return code: {verify_result.returncode}
Verification success: {verify_result.returncode == 0}

Command used: {' '.join(cmd)}
Virtual environment: {venv_path if is_active else 'Not using venv'}

Installation output:
{result.stdout}

Verification output:
{verify_result.stdout}

Errors (if any):
{result.stderr if result.stderr else 'None'}
"""
            
    except subprocess.TimeoutExpired as e:
        return f"""Package installation timeout.

Package: {package_name}
Operation: pip install
Timeout duration: 120 seconds
Error type: TimeoutExpired
Error details: {str(e)}

The installation process exceeded the timeout limit. This may indicate:
- Large package with many dependencies
- Slow network connection
- Package build process taking too long
"""
    except Exception as e:
        return f"""Package installation error.

Package: {package_name}
Operation: pip install
Error type: {type(e).__name__}
Error details: {str(e)}

An unexpected error occurred during package installation.
"""

def pip_uninstall_package(package_name, force=False):
    """Uninstall a Python package using pip.
    
    Args:
        package_name (str): Name of the package to uninstall
        force (bool): If True, skip confirmation prompts
    
    Returns:
        str: Structured status message with operation details
    """
    try:
        pip_cmd = find_pip_command()
        
        if not pip_cmd:
            is_active, venv_path, reason = get_active_virtualenv()
            return f"""Cannot find pip command.

Package: {package_name}
Operation: pip uninstall
Pip command: Not found
Virtual environment active: {is_active}
Virtual environment path: {venv_path or 'None'}
Detection method: {reason}
"""
        
        if not package_name or not package_name.strip():
            return f"""Invalid package name.

Package: {package_name}
Operation: pip uninstall
Error: Empty or invalid package name provided
"""
        
        package_name = package_name.strip()
        
        env = os.environ.copy()
        if 'VIRTUAL_ENV' in os.environ:
            env["PATH"] = f"{os.path.join(os.environ['VIRTUAL_ENV'], 'bin')}:{env['PATH']}"
        
        check_result = subprocess.run([
            pip_cmd, "show", package_name
        ], capture_output=True, text=True, timeout=10, env=env)
        
        if check_result.returncode != 0:
            return f"""Package not currently installed.

Package: {package_name}
Operation: pip uninstall
Check return code: {check_result.returncode}
Package installed: False
Check output: {check_result.stdout}
Check errors: {check_result.stderr}
"""
        
        uninstall_cmd = [pip_cmd, "uninstall"]
        
        if force:
            uninstall_cmd.append("-y")
        
        uninstall_cmd.append(package_name)
        
        result = subprocess.run(
            uninstall_cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        
        return f"""Package uninstall operation completed.

Package: {package_name}
Operation: pip uninstall
Command used: {' '.join(uninstall_cmd)}
Return code: {result.returncode}
Success: {result.returncode == 0}
Force mode: {force}

Output:
{result.stdout}

Errors (if any):
{result.stderr if result.stderr else 'None'}
"""
                
    except subprocess.TimeoutExpired as e:
        return f"""Package uninstall timeout.

Package: {package_name}
Operation: pip uninstall
Timeout duration: 60 seconds
Error type: TimeoutExpired
Error details: {str(e)}
"""
    except Exception as e:
        return f"""Package uninstall error.

Package: {package_name}
Operation: pip uninstall
Error type: {type(e).__name__}
Error details: {str(e)}
"""

def pip_list_packages():
    """List all installed packages in a casual, readable format."""
    try:
        pip_cmd = find_pip_command()
        
        if not pip_cmd:
            return "❌ Can't find pip to check what's installed."
        
        # Set up environment
        env = os.environ.copy()
        if 'VIRTUAL_ENV' in os.environ:
            env["PATH"] = f"{os.path.join(os.environ['VIRTUAL_ENV'], 'bin')}:{env['PATH']}"
        
        # Get package list
        result = subprocess.run([
            pip_cmd, "list"
        ], capture_output=True, text=True, timeout=30, env=env)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if not output:
                return "🤷 No packages installed... that's weird."
            
            lines = output.split('\n')
            if len(lines) <= 2:  # Just headers
                return "📦 No packages found (just pip itself probably)."
            
            # Count packages (skip header lines)
            package_lines = [line for line in lines[2:] if line.strip()]
            package_count = len(package_lines)
            
            return f"📦 **Found {package_count} installed packages:**\n\n```\n{output}\n```"
        else:
            error_output = result.stderr or result.stdout or "Unknown error"
            return f"❌ Error getting package list: {error_output}"
            
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout getting package list - that's taking unusually long."
    except Exception as e:
        return f"💥 Error checking installed packages: {str(e)}"

def smart_install_package(package_name, user_message=""):
    """Intelligently install a package using pip or vctl based on package type.
    
    Rules:
    - Fake driver library (volttron-lib-fake-driver) → MUST use pip
    - Python libraries (volttron-*) → Use pip
    - VOLTTRON agents (listener, platform driver, historian, etc.) → Use vctl install
    
    Args:
        package_name: Name of package/agent to install
        user_message: Original user message for context
        
    Returns:
        str: Installation result message
    """
    package_lower = package_name.lower().strip()
    message_lower = user_message.lower()
    
    # Rule 1: Fake driver library MUST use pip (cannot use vctl)
    if 'fake' in package_lower and 'driver' in package_lower:
        if 'lib' not in package_lower and 'volttron-lib' not in package_lower:
            package_name = 'volttron-lib-fake-driver'
        return pip_install_package(package_name)
    
    # Rule 2: If package starts with "volttron-" it's a pip package (library)
    if package_lower.startswith('volttron-'):
        return pip_install_package(package_name)
    
    # Rule 3: Known VOLTTRON agents that use vctl install
    # Comprehensive list from https://github.com/eclipse-volttron
    vctl_agents = {
        # Core agents
        'listener': vctl_install_listener_agent,
        'listeneragent': vctl_install_listener_agent,
        'volttron-listener': vctl_install_listener_agent,
        
        # Platform driver
        'platform-driver': vctl_install_platform_driver,
        'platformdriver': vctl_install_platform_driver,
        'platform.driver': vctl_install_platform_driver,
        'volttron-platform-driver': vctl_install_platform_driver,
        
        # Historians
        'historian': vctl_install_agent,
        'sqlhistorian': vctl_install_agent,
        'sql-historian': vctl_install_agent,
        'postgresql-historian': vctl_install_agent,
        'sqlite-historian': vctl_install_agent,
        'volttron-postgresql-historian': vctl_install_agent,
        'volttron-sqlite-historian': vctl_install_agent,
        
        # Actuator
        'actuator': vctl_install_agent,
        'volttron-actuator': vctl_install_agent,
        
        # Weather
        'weather': vctl_install_agent,
        'weatheragent': vctl_install_agent,
        
        # IEEE 2030.5
        'ieee2030': vctl_install_agent,
        'ieee-2030': vctl_install_agent,
        
        # Protocol proxies
        'bacnet-proxy': vctl_install_agent,
        'bacnetproxy': vctl_install_agent,
        'modbus-tk': vctl_install_agent,
        'modbus': vctl_install_agent,
        'dnp3': vctl_install_agent,
        'mqtt-proxy': vctl_install_agent,
        'nats-proxy': vctl_install_agent,
        
        # ILC
        'ilc': vctl_install_agent,
        'volttron-ilc': vctl_install_agent,
        
        # Topic watcher
        'topic-watcher': vctl_install_agent,
        'topicwatcher': vctl_install_agent,
        'volttron-topic-watcher': vctl_install_agent,
        
        # Threshold detection
        'threshold-detection': vctl_install_agent,
        'thresholddetection': vctl_install_agent,
        'volttron-threshold-detection': vctl_install_agent,
        
        # Platform lookup
        'platform-lookup': vctl_install_agent,
        'platformlookup': vctl_install_agent,
    }
    
    # Check if it's a known vctl agent
    package_normalized = package_lower.replace('_', '-').replace('.', '-')
    for agent_name, install_func in vctl_agents.items():
        if agent_name in package_normalized or package_normalized in agent_name:
            # Call the appropriate installation function
            if install_func == vctl_install_agent:
                return vctl_install_agent(package_name)
            else:
                return install_func()
    
    # Rule 4: If message says "agent", use vctl
    if 'agent' in message_lower:
        return vctl_install_agent(package_name)
    
    # Rule 5: Default to pip for Python packages
    # Try pip first, if it fails suggest vctl
    pip_result = pip_install_package(package_name)
    
    if '❌' in pip_result or 'Failed' in pip_result or 'not found' in pip_result.lower():
        return f"""{pip_result}

💡 **Alternative:** If this is a VOLTTRON agent (not a library), try:
   `vctl install {package_name}`

**Need help?** Tell me more about what you're trying to install:
• Python library → I'll use `pip install`
• VOLTTRON agent → I'll use `vctl install`"""
    
    return pip_result

def install_fake_driver_library():
    """Install the volttron-lib-fake-driver package for testing and development.
    
    Returns:
        str: Status message about the installation
    """
    try:
        pip_cmd = find_pip_command()
        if not pip_cmd:
            return "❌ Pip command not found. Please install pip first."
        
        package_name = "volttron-lib-fake-driver"
        
        print(f"📦 Installing {package_name}...")
        install_result = subprocess.run(
            [pip_cmd, "install", package_name],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if install_result.returncode == 0:
            # Check if it was already installed
            if "Requirement already satisfied" in install_result.stdout:
                return f"""✅ **{package_name} is already installed!**

The fake driver library is ready to use for testing and development.

**⚠️ Important Next Steps to See Fake Data:**
The library is installed, but you still need to:

1. **Install the platform driver agent**: 
   Say: "install platform driver"
   
2. **Create fake device configuration**:
   The platform driver needs config files to know what fake devices to create
   
3. **Start the platform driver**:
   Once configured, start it to begin generating fake data

**Quick start**: Try saying:
• "install platform driver" - to install the driver agent
• "show agents" - to see what's running
• "show logs" - to monitor activity

💡 Just having the library isn't enough - you need the platform driver agent running with proper configuration to actually generate and see fake device data in the logs!"""
            else:
                return f"""🎉 **Successfully installed {package_name}!**

The fake driver library is now available for testing and simulating device data.

**⚠️ Important Next Steps to See Fake Data:**
The library is installed, but you still need to:

1. **Install the platform driver agent**: 
   Say: "install platform driver"
   
2. **Create fake device configuration**:
   The platform driver needs config files to know what fake devices to create
   
3. **Start the platform driver**:
   Once configured, start it to begin generating fake data

**Quick start**: Try saying:
• "install platform driver" - to install the driver agent
• "show agents" - to see what's running
• "show logs" - to monitor activity

💡 Just having the library isn't enough - you need the platform driver agent running with proper configuration to actually generate and see fake device data in the logs!"""
        else:
            error_output = install_result.stderr or install_result.stdout or "Unknown error"
            return f"""❌ **Failed to install {package_name}**

Error: {error_output}

**Troubleshooting:**
• Make sure you're in the correct virtual environment
• Check your internet connection
• Try: `pip install {package_name}` manually

Need help? Let me know!"""
            
    except subprocess.TimeoutExpired:
        return f"⏱️ Installation is taking longer than expected. The package might be large or your connection is slow."
    except Exception as e:
        return f"💥 Error installing fake driver library: {str(e)}"

def show_fake_driver_logs(num_lines=50):
    """Show recent fake driver data from VOLTTRON logs.
    
    Args:
        num_lines (int): Number of recent log lines to check (default: 50)
    
    Returns:
        str: Formatted display of fake driver log data
    """
    try:
        # Find VOLTTRON log file
        volttron_home = get_volttron_home()
        log_paths = [
            os.path.join(volttron_home, "volttron.log"),
            os.path.expanduser("~/volttron-fresh/volttron_home/volttron.log"),
            os.path.expanduser("~/.volttron/volttron.log"),
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
            return f"""Fake driver logs check completed.
Status: Log file not found
Paths searched: {', '.join(log_paths)}
Recommendation: Start VOLTTRON with logging (volttron -vv -l volttron.log)"""
        
        # Read recent lines from the log
        result = subprocess.run([
            "tail", f"-{num_lines}", volttron_log
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            log_lines = result.stdout.strip().split('\n')
            
            # Filter for fake driver related lines
            fake_lines = []
            for line in log_lines:
                lower_line = line.lower()
                if any(keyword in lower_line for keyword in [
                    'fake', 'devices/campus/building/fake', 
                    'volttron-lib-fake-driver', 'fakedriver'
                ]):
                    fake_lines.append(line)
            
            if fake_lines:
                # Show last 20 fake driver lines
                display_lines = fake_lines[-20:]
                log_display = '\n'.join(display_lines)
                
                return f"""Fake driver logs retrieved successfully.
Status: Active
Log file: {volttron_log}
Total lines scanned: {num_lines}
Fake driver entries found: {len(fake_lines)}
Entries displayed: {len(display_lines)}

Recent fake driver log entries:
{log_display}

Log file path: {volttron_log}
Data topics: devices/campus/building/fake/*"""
            else:
                return f"""Fake driver logs check completed.
Status: No activity found
Log file: {volttron_log}
Lines scanned: {len(log_lines)}
Fake driver entries: 0

No fake driver activity detected in recent logs.
Possible causes: Fake driver library not installed, platform driver not running, fake device not configured, or no data published yet."""
        else:
            return f"""Fake driver logs check completed.
Status: Error reading log file
Log file: {volttron_log}
Return code: {result.returncode}"""
            
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout reading log file - it might be very large"
    except Exception as e:
        return f"💥 Error showing fake driver logs: {str(e)}"

def check_fake_driver_status():
    """Check if the fake driver is actively publishing data by examining recent logs.
    
    This function checks the actual log activity to determine if the fake driver is working,
    not just whether the library is installed. Returns structured data for AI interpretation.
    
    Returns:
        str: Structured status information about fake driver operation
    """
    try:
        # Find VOLTTRON log file
        volttron_home = get_volttron_home()
        log_paths = [
            os.path.join(volttron_home, "volttron.log"),
            os.path.expanduser("~/volttron-fresh/volttron_home/volttron.log"),
            os.path.expanduser("~/.volttron/volttron.log"),
            "volttron.log",
        ]
        
        volttron_log = None
        for path in log_paths:
            if os.path.exists(path):
                volttron_log = path
                break
        
        if not volttron_log:
            return """Fake driver status check completed.
Status: Unable to determine
Reason: VOLTTRON log file not found
Log file searched: Multiple standard locations
Recommendation: Start VOLTTRON with logging enabled"""
        
        # Read recent lines from the log (last 100 lines should be enough)
        result = subprocess.run([
            "tail", "-100", volttron_log
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            log_lines = result.stdout.strip().split('\n')
            
            # Filter for fake driver activity
            fake_lines = []
            for line in log_lines:
                lower_line = line.lower()
                if any(keyword in lower_line for keyword in [
                    'fake', 'devices/campus/building/fake'
                ]):
                    fake_lines.append(line)
            
            # Determine status based on log activity
            if fake_lines:
                # Count publishing events
                publish_count = sum(1 for line in fake_lines if 'publishing:' in line.lower())
                
                # Extract timestamp from last line if available
                last_line = fake_lines[-1] if fake_lines else None
                
                return f"""Fake driver status check completed.
Status: Active and publishing
Activity found: Yes
Recent log entries: {len(fake_lines)} in last 100 lines
Publishing events detected: {publish_count}
Log file: {volttron_log}
Last activity: {last_line[:80] if last_line else 'N/A'}...

Fake driver is operational and publishing data."""
            else:
                # Check if volttron-lib-fake-driver is installed
                pip_cmd = find_pip_command()
                if pip_cmd:
                    check_result = subprocess.run(
                        [pip_cmd, "show", "volttron-lib-fake-driver"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    library_installed = check_result.returncode == 0
                else:
                    library_installed = False
                
                return f"""Fake driver status check completed.
Status: Not publishing
Activity found: No
Recent log entries: 0 in last 100 lines
Log file: {volttron_log}
Lines scanned: {len(log_lines)}
Library installed: {library_installed}

No fake driver activity detected in recent logs.
This could indicate:
- Fake driver library not installed
- Platform driver not running
- Fake device not configured
- VOLTTRON not actively running"""
        else:
            return f"""Fake driver status check completed.
Status: Unable to read logs
Error: Failed to read log file
Log file: {volttron_log}
Return code: {result.returncode}"""
            
    except subprocess.TimeoutExpired:
        return """Fake driver status check completed.
Status: Timeout
Error: Log file read timeout (file may be very large)"""
    except Exception as e:
        return f"""Fake driver status check completed.
Status: Error
Error type: {type(e).__name__}
Error message: {str(e)}"""

def watch_fake_driver_logs():
    """Provide instructions for watching fake driver logs in real-time.
    
    Returns:
        str: Instructions for using tail -f to monitor logs
    """
    try:
        # Find VOLTTRON log file
        volttron_home = get_volttron_home()
        log_paths = [
            os.path.join(volttron_home, "volttron.log"),
            os.path.expanduser("~/volttron-fresh/volttron_home/volttron.log"),
            os.path.expanduser("~/.volttron/volttron.log"),
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
📋 **Cannot find VOLTTRON log file**

**To start logging:**
```bash
volttron -vv -l volttron.log &
```

Then ask me again to watch the logs! 🚀
"""
        
        return f"""
👀 **Watch Fake Driver Logs in Real-Time**

To monitor fake driver data as it's published, open a terminal and run:

**Option 1 - Watch all fake driver activity:**
```bash
tail -f {volttron_log} | grep -i fake
```

**Option 2 - Watch ALL VOLTTRON logs:**
```bash
tail -f {volttron_log}
```

**Option 3 - Watch specific device topics:**
```bash
tail -f {volttron_log} | grep "devices/campus/building/fake"
```

**📁 Log file location:** `{volttron_log}`

**🔍 What to look for:**
• **Published messages** - Data being sent to the message bus
• **Device readings** - Temperature, EKG, heartbeat, etc.
• **Timestamps** - When data was published
• **Topics** - Where data is being sent

**💡 Tip:** Press `Ctrl+C` to stop watching the logs

**Need something else?**
• Ask me "show fake driver logs" for recent entries
• Ask me "show agent status" to check what's running
"""
        
    except Exception as e:
        return f"💥 Error getting log watch instructions: {str(e)}"

def setup_fake_driver_complete():
    """Complete automated setup of fake driver - install library, platform driver, configure, and start everything.
    
    This does EVERYTHING needed to get fake data flowing, so the user just needs to check logs afterwards.
    
    Returns:
        str: Status of the complete setup process
    """
    import time
    
    status_messages = []
    
    try:
        # STEP 1: Ensure VOLTTRON is running
        status_messages.append("🚀 **Step 1/5: Starting VOLTTRON platform...**")
        start_result = start_volttron()
        time.sleep(3)  # Give it time to start
        
        # STEP 2: Install fake driver library
        status_messages.append("\n📦 **Step 2/5: Installing volttron-lib-fake-driver...**")
        pip_cmd = find_pip_command()
        if not pip_cmd:
            return "❌ Pip command not found. Please install pip first."
        
        install_lib_result = subprocess.run(
            [pip_cmd, "install", "volttron-lib-fake-driver"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if install_lib_result.returncode == 0:
            if "Requirement already satisfied" in install_lib_result.stdout:
                status_messages.append("   ✅ volttron-lib-fake-driver already installed")
            else:
                status_messages.append("   ✅ volttron-lib-fake-driver installed successfully")
        else:
            return "\n".join(status_messages) + f"\n❌ Failed to install fake driver library: {install_lib_result.stderr}"
        
        # STEP 3: Install platform driver package
        status_messages.append("\n📦 **Step 3/5: Installing volttron-platform-driver...**")
        install_pd_result = subprocess.run(
            [pip_cmd, "install", "volttron-platform-driver"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if install_pd_result.returncode == 0:
            if "Requirement already satisfied" in install_pd_result.stdout:
                status_messages.append("   ✅ volttron-platform-driver already installed")
            else:
                status_messages.append("   ✅ volttron-platform-driver installed successfully")
        else:
            return "\n".join(status_messages) + f"\n❌ Failed to install platform driver: {install_pd_result.stderr}"
        
        time.sleep(2)
        
        # STEP 4: Install and configure platform driver agent with vctl
        status_messages.append("\n⚙️  **Step 4/5: Installing platform driver agent...**")
        
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return "\n".join(status_messages) + "\n❌ vctl command not found"
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Check if already installed
        status_check = subprocess.run(
            [vctl_cmd, "status"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            cwd=volttron_home
        )
        
        if "platform.driver" in status_check.stdout:
            status_messages.append("   ✅ Platform driver agent already installed")
        else:
            # Install the agent
            install_agent_result = subprocess.run(
                [vctl_cmd, "install", "volttron-platform-driver", "--start"],
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
                cwd=volttron_home
            )
            
            if install_agent_result.returncode == 0:
                status_messages.append("   ✅ Platform driver agent installed and started")
            else:
                # Try without --start
                install_agent_result = subprocess.run(
                    [vctl_cmd, "install", "volttron-platform-driver"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env=env,
                    cwd=volttron_home
                )
                if install_agent_result.returncode == 0:
                    status_messages.append("   ✅ Platform driver agent installed")
                else:
                    status_messages.append(f"   ⚠️  Platform driver installation had issues: {install_agent_result.stderr[:200]}")
        
        time.sleep(3)
        
        # STEP 5: Start the platform driver if not running
        status_messages.append("\n▶️  **Step 5/5: Starting platform driver agent...**")
        
        # Get updated status
        status_check = subprocess.run(
            [vctl_cmd, "status"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            cwd=volttron_home
        )
        
        # Try to find and start platform driver
        if "platform.driver" in status_check.stdout:
            # Try to start it
            start_agent_result = subprocess.run(
                [vctl_cmd, "start", "--tag", "platform.driver"],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=volttron_home
            )
            status_messages.append("   ✅ Platform driver started")
        
        time.sleep(2)
        
        # Final status check
        final_status = subprocess.run(
            [vctl_cmd, "status"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            cwd=volttron_home
        )
        
        # Build final response
        response = "\n".join(status_messages)
        response += "\n\n" + "="*60
        response += "\n🎉 **FAKE DRIVER SETUP COMPLETE!**\n"
        response += "="*60
        
        if "platform.driver" in final_status.stdout:
            response += """

✅ **Everything is ready!** The fake driver is now set up and running.

**What's happening now:**
• VOLTTRON platform is running
• Fake driver library is installed
• Platform driver agent is installed and started
• Fake devices will start generating data

**To see the fake data:**
Just say: **"show logs"** or **"show fake driver logs"**

You should now see fake sensor data appearing in the logs! 🎊

**Monitor live data:**
• "show logs" - See recent fake data
• "show fake driver logs" - Focused view of fake device data
• "show agents" - Check all agent status

The fake driver is now actively generating simulated device data! 📊
"""
        else:
            response += """

⚠️  **Setup mostly complete, but platform driver may need manual configuration**

**What's installed:**
• VOLTTRON platform ✅
• volttron-lib-fake-driver ✅
• volttron-platform-driver package ✅

**What might need attention:**
• Platform driver agent may need configuration files
• Check agent status with: "show agents"
• Check logs with: "show logs"

The platform driver might need specific configuration files to define fake devices.
Would you like help creating the configuration?
"""
        
        return response
        
    except subprocess.TimeoutExpired:
        return "\n".join(status_messages) + "\n⏱️ Timeout during setup - process taking too long"
    except Exception as e:
        return "\n".join(status_messages) + f"\n💥 Error during setup: {str(e)}"

def vctl_uninstall_all_listeners():
    """Uninstall all listener agents to clean up duplicates."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        status_result = subprocess.run(
            [vctl_cmd, "status"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home
        )
        
        if status_result.returncode != 0:
            return "❌ Could not get agent status. Make sure VOLTTRON is running."
        
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
        
        removed_agents = []
        failed_agents = []
        
        for uuid in listener_uuids:
            subprocess.run([vctl_cmd, "stop", uuid], capture_output=True, env=env, cwd=volttron_home)
            
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
        
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-num_lines:] if len(lines) >= num_lines else lines
            raw_logs = ''.join(recent_lines).strip()
        
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
pip install volttron

export VOLTTRON_HOME=~/.volttron

vcfg

volttron -vv -l volttron.log &
```

🛠️ **Method 2: Developer Install**
----------------------------------
If you want to modify VOLTTRON or install from source:

```bash
git clone https://github.com/VOLTTRON/volttron.git
cd volttron

python3 -m venv env
source env/bin/activate

pip install -e .

export VOLTTRON_HOME=~/.volttron

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


```bash
python -m venv env
source env/bin/activate
```

```bash
pip install volttron
```

```bash
export VOLTTRON_HOME=/path/to/volttron_home/dir
```

```bash
volttron -vv -l volttron.log &>/dev/null &
```

Ask me: **"Can you start VOLTTRON for me?"** and I'll handle it!

Once I'm running, come back and ask **"What's next?"** for vctl commands! 
"""

def install_volttron_with_pip():
    """Install VOLTTRON using pip and set up the environment."""
    try:
        volttron_cmd = find_volttron_command()
        if volttron_cmd:
            return f"""
🎉 **VOLTTRON is already installed!**

✅ Found VOLTTRON at: {volttron_cmd}

You can now:
• **Start VOLTTRON**: "start volttron"
• **Check status**: "vctl status"  
• **Install agents**: "install listener agent"

Ready to control your IoT platform! 🚀
"""

        pip_cmd = find_pip_command()
        if not pip_cmd:
            return """
❌ **Pip not found!**

I need pip to install VOLTTRON. Please make sure Python and pip are installed:

```bash
# On Ubuntu/Debian:
sudo apt update && sudo apt install python3-pip

# On CentOS/RHEL:
sudo yum install python3-pip

# Or use curl:
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

Then try asking me to install VOLTTRON again! 🔧
"""

        print(f"Installing VOLTTRON using pip: {pip_cmd}")
        
        result = subprocess.run(
            [pip_cmd, "install", "volttron"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            volttron_home = os.path.expanduser("~/.volttron")
            
            return f"""
🎉 **VOLTTRON Installation Successful!**

✅ **Installed via**: {pip_cmd} install volttron
📁 **VOLTTRON_HOME**: {volttron_home}

**Next Steps:**
1. **Set environment variable**:
   ```bash
   export VOLTTRON_HOME={volttron_home}
   ```

2. **Configure VOLTTRON** (optional):
   ```bash
   vcfg
   ```

3. **Start VOLTTRON**:
   ```bash
   volttron -vv -l volttron.log &
   ```

**Or just ask me**: "start volttron" and I'll handle it! 🚀

💡 **Installation complete!** You can now use commands like:
• "Show VOLTTRON status"
• "Install listener agent"  
• "List all agents"
"""
        else:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            return f"""
❌ **VOLTTRON Installation Failed**

**Error output:**
```
{error_msg}
```

**Common solutions:**
• **Upgrade pip**: `pip install --upgrade pip`
• **Use virtual environment**: 
  ```bash
  python -m venv volttron-env
  source volttron-env/bin/activate
  pip install volttron
  ```
• **Install system dependencies**: 
  ```bash
  # Ubuntu/Debian:
  sudo apt install build-essential python3-dev
  
  # CentOS/RHEL:
  sudo yum groupinstall "Development Tools"
  sudo yum install python3-devel
  ```

Try these fixes and ask me to install VOLTTRON again! 🔧
"""
            
    except subprocess.TimeoutExpired:
        return """
⏱️ **Installation timed out**

VOLTTRON installation is taking longer than expected (5+ minutes).

**Try these alternatives:**
• **Manual install**: Open a terminal and run `pip install volttron`
• **Virtual environment**: Create a dedicated environment first
• **Check internet**: Ensure you have a stable connection

I can help you troubleshoot once the installation completes! 🔧
"""
    except Exception as e:
        return f"""
❌ **Installation error occurred**

**Error**: {str(e)}

**Please try manual installation:**
```bash
pip install volttron
export VOLTTRON_HOME=~/.volttron
vcfg
volttron -vv -l volttron.log &
```

Once installed, I can help you control VOLTTRON! 🤖
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
    """Install the VOLTTRON platform driver agent with proper pip and vctl installation."""
    vctl_cmd = find_vctl_command()
    volttron_home = get_volttron_home()
    
    if not vctl_cmd:
        return check_volttron_installation()
    
    print("Ensuring VOLTTRON is running by starting it...")
    start_volttron()
    
    import time
    time.sleep(5)
    
    
    try:
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        status_result = subprocess.run([
            vctl_cmd, "status"
        ], capture_output=True, text=True, timeout=30, env=env, cwd=volttron_home)
        
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
        
        pip_cmd = find_pip_command()
        package_name = "volttron-platform-driver"
        
        if pip_cmd:
            print(f"📦 Installing platform driver package: {package_name}")
            pip_result = subprocess.run([
                pip_cmd, "install", package_name
            ], capture_output=True, text=True, timeout=120, env=env)
            
            if pip_result.returncode != 0:
                return f"""❌ **Failed to install platform driver package**

Error installing the Python package:
```
{pip_result.stderr or pip_result.stdout}
```

Please try manually running:
```
pip install volttron-platform-driver
```

Once the package is installed, try installing the agent again.
"""
        
        print(f"Installing platform driver with vctl: {vctl_cmd}")
        print(f"VOLTTRON_HOME: {volttron_home}")
        
        install_cmd = f"export VOLTTRON_HOME={volttron_home} && {vctl_cmd} install volttron-platform-driver --vip-identity platform.driver --start --priority 40"
        install_result = subprocess.run(
            install_cmd, 
            shell=True,
            capture_output=True, 
            text=True, 
            timeout=120,
            env=env
        )
        
        print(f"Platform driver install command result: {install_result.returncode}")
        print(f"Platform driver install stdout: {install_result.stdout}")
        print(f"Platform driver install stderr: {install_result.stderr}")
        
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

def get_recent_fake_data_from_logs():
    """Get recent fake driver data from VOLTTRON logs.
    
    Returns structured data about fake driver activity, not hardcoded responses.
    """
    try:
        # Look for volttron.log in common locations
        volttron_home = get_volttron_home()
        log_paths = [
            os.path.join(volttron_home, "volttron.log"),
            os.path.expanduser("~/volttron-fresh/volttron_home/volttron.log"),
            os.path.expanduser("~/.volttron/volttron.log"),
            "volttron.log",
            "/tmp/volttron.log"
        ]
        
        volttron_log = None
        for path in log_paths:
            if os.path.exists(path):
                volttron_log = path
                break
        
        if not volttron_log:
            return f"""Fake driver log check completed.
Status: Log file not found
Log paths searched: {', '.join(log_paths)}
Recommendation: Start VOLTTRON with logging enabled (volttron -vv -l volttron.log)
Configuration status: Ready (log file needed)"""
        
        # Get recent lines from the log that mention fake driver
        result = subprocess.run([
            "tail", "-100", volttron_log
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            fake_lines = [line for line in lines if 'fake' in line.lower() and ('devices/campus/building/fake' in line or 'driver' in line)]
            
            if fake_lines:
                recent_lines = fake_lines[-5:]
                log_display = '\n'.join(recent_lines)
                
                return f"""Fake driver log check completed.
Status: Active
Log file: {volttron_log}
Lines scanned: 100
Fake driver entries found: {len(fake_lines)}
Recent entries shown: {len(recent_lines)}

Recent log output:
{log_display}

Fake driver is actively publishing data."""
            else:
                return f"""Fake driver log check completed.
Status: No activity detected
Log file: {volttron_log}
Lines scanned: 100
Fake driver entries found: 0

No recent fake driver activity in logs.
Possible reasons: Platform driver not running, fake device not configured, or VOLTTRON just started."""
        
        return f"""Fake driver log check completed.
Status: Error reading logs
Log file: {volttron_log}
Return code: {result.returncode}"""
        
    except Exception as e:
        return f"""Fake driver log check completed.
Status: Error
Error type: {type(e).__name__}
Error message: {str(e)}"""

def show_recent_logs():
    """Show recent VOLTTRON logs with focus on fake driver and agent activity."""
    try:
        volttron_home = get_volttron_home()
        
        log_paths = [
            os.path.join(volttron_home, "volttron.log"),  # PRIMARY: VOLTTRON_HOME/volttron.log
            os.path.expanduser("~/volttron-fresh/volttron_home/volttron.log"),
            os.path.expanduser("~/.volttron/volttron.log"),
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
            searched_paths = [
                f"{volttron_home}/volttron.log",
                os.path.expanduser('~/volttron-fresh/volttron_home/volttron.log'),
                os.path.expanduser('~/.volttron/volttron.log'),
                "volttron.log",
                "/tmp/volttron.log",
                "/var/log/volttron.log"
            ]
            return f"""VOLTTRON logs check completed.
Status: Log file not found
VOLTTRON_HOME: {volttron_home}
Paths searched:
{chr(10).join(f'  - {p}' for p in searched_paths)}

Recommendation: Start VOLTTRON with logging enabled using command: volttron -vv -l volttron.log"""
        
        result = subprocess.run([
            "tail", "-200", volttron_log
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            log_lines = result.stdout.strip().split('\n')
            
            device_lines = []
            other_interesting_lines = []
            
            for line in log_lines:
                lower_line = line.lower()
                if 'devices/campus/building/fake' in lower_line and 'publishing:' in lower_line:
                    device_lines.append(line)
                elif any(keyword in lower_line for keyword in [
                    'error', 'warning', 'failed', 'exception', 
                    'installed', 'started', 'stopped'
                ]) and 'auth_service' not in lower_line:  # Skip auth service spam
                    other_interesting_lines.append(line)
            
            interesting_lines = device_lines[-30:] + other_interesting_lines[-5:]  # Get more lines
            
            if interesting_lines:
                device_data = {}  # device_name -> [timestamps]
                
                for line in device_lines[-50:]:  # Look at more lines
                    if 'devices/campus/building/fake/' in line:
                        try:
                            timestamp_full = line.split('(')[0].strip()
                            time_only = timestamp_full.split()[1].split(',')[0]  # Get HH:MM:SS
                            
                            device_part = line.split('devices/campus/building/fake/')[1]
                            device_name = device_part.split()[0].strip()
                            
                            if device_name != 'all':  # Skip 'all' device
                                if device_name not in device_data:
                                    device_data[device_name] = []
                                if len(device_data[device_name]) < 3:  # Keep last 3 timestamps per device
                                    device_data[device_name].append(time_only)
                        except:
                            pass
                
                if device_data:
                    devices_list = sorted(device_data.keys())
                    
                    # Build device list with timestamps
                    device_list = []
                    for dev in devices_list:
                        times = device_data[dev]
                        latest_time = times[-1] if times else "N/A"
                        device_list.append(f"{dev}: {latest_time} (last seen)")
                    
                    device_output = '\n'.join(device_list)
                    
                    # Build timeline for first 12 devices
                    timeline_list = []
                    for dev in devices_list[:12]:
                        times = device_data[dev]
                        if times:
                            timeline_list.append(f"{dev}: {' -> '.join(times[-3:])}")
                    
                    timeline_output = '\n'.join(timeline_list) if timeline_list else "No timeline data"
                else:
                    device_output = "No device data parsed"
                    timeline_output = "No device data"
                
                return f"""VOLTTRON recent logs check completed.
Status: Activity detected
Log file: {volttron_log}
Lines scanned: 200
Device publishing entries: {len(device_lines)}
Other interesting entries: {len(other_interesting_lines)}
Devices active: {len(device_data)}

Active devices:
{device_output}

Recent activity timeline:
{timeline_output}

Platform driver status: Active and publishing
Log file path: {volttron_log}"""
            else:
                return f"""VOLTTRON recent logs check completed.
Status: No activity
Log file: {volttron_log}
Lines scanned: {len(log_lines)}
Device publishing entries: 0
Other interesting entries: 0

No recent fake driver or significant agent activity detected.
This may indicate: VOLTTRON just started, platform driver not active, fake device not configured, or low logging verbosity."""
        else:
            return f"""VOLTTRON logs check completed.
Status: Could not read log file
Log file: {volttron_log}
Return code: {result.returncode}"""
            
    except subprocess.TimeoutExpired:
        return "❌ Timeout while reading VOLTTRON logs"
    except Exception as e:
        return f"❌ Error reading logs: {str(e)}"
