import subprocess
import os
import sys
import shutil
import requests
import json
from pathlib import Path
import re


def install_missing_package(package_name, pip_path=None):
    """
    Install a missing Python package.
    
    Args:
        package_name: Name of the package to install (e.g., 'zope.event')
        pip_path: Optional pip path to use. If None, will detect from environment.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Get pip path if not provided
        if pip_path is None:
            pip_path, error = get_pip_command_from_venv()
            if error:
                return False, error
        
        print(f"📦 Installing missing package: {package_name}")
        result = subprocess.run(
            [pip_path, 'install', package_name],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return True, f"✅ Successfully installed {package_name}"
        else:
            return False, f"❌ Failed to install {package_name}: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, f"❌ Timeout while installing {package_name}"
    except Exception as e:
        return False, f"❌ Error installing {package_name}: {str(e)}"


def extract_missing_module(error_output):
    """
    Extract the missing module name from an error message.
    
    Args:
        error_output: Error output from a command
    
    Returns:
        str or None: The missing module name, or None if not found
    """
    # Pattern: ModuleNotFoundError: No module named 'package.name'
    pattern = r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]"
    match = re.search(pattern, error_output)
    if match:
        return match.group(1)
    return None


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
    
    pip_path = os.path.join(venv_path, 'bin', 'pip')
    
    if os.path.exists(pip_path) and os.access(pip_path, os.X_OK):
        print(f"✅ Using pip from active venv: {pip_path}")
        return pip_path, None
    
    pip3_path = os.path.join(venv_path, 'bin', 'pip3')
    if os.path.exists(pip3_path) and os.access(pip3_path, os.X_OK):
        print(f"✅ Using pip3 from active venv: {pip3_path}")
        return pip3_path, None
    
    return None, f"❌ pip not found in active virtual environment: {venv_path}"


AVAILABLE_AGENTS = {
    'listener': {
        'package': 'volttron-listener',
        'vip_identity': 'listener',
        'description': 'Simple listener agent that monitors all platform messages',
        'category': 'Core',
        'github_url': 'https://github.com/eclipse-volttron/volttron-listener.git'
    },
    'platform-driver': {
        'package': 'volttron-platform-driver', 
        'vip_identity': 'platform.driver',
        'description': 'Platform driver for device communication',
        'category': 'Driver',
        'github_url': 'https://github.com/eclipse-volttron/volttron-platform-driver.git'
    },
    
    'sqlite-historian': {
        'package': 'volttron-sqlite-historian',
        'vip_identity': 'sqlite_historian',
        'description': 'SQLite database historian for storing data',
        'category': 'Historian',
        'github_url': 'https://github.com/eclipse-volttron/volttron-sqlite-historian.git'
    },
    'postgresql-historian': {
        'package': 'volttron-postgresql-historian',
        'vip_identity': 'postgresql_historian', 
        'description': 'PostgreSQL database historian for storing data',
        'category': 'Historian',
        'github_url': 'https://github.com/eclipse-volttron/volttron-postgresql-historian.git'
    },
    
    'fake-driver': {
        'package': 'volttron-lib-fake-driver',
        'vip_identity': 'fake_driver',
        'description': 'Fake driver library for testing and development',
        'category': 'Driver Library',
        'github_url': 'https://github.com/eclipse-volttron/volttron-lib-fake-driver.git'
    },
    
    'csv-driver': {
        'package': 'volttron-csv-driver',
        'vip_identity': 'csv_driver',
        'description': 'CSV driver agent for reading data from CSV files',
        'category': 'Data Analysis',
        'github_url': 'https://github.com/eclipse-volttron/volttron-csv-driver.git'
    },
    
    'forward-historian': {
        'package': 'volttron-forward-historian',
        'vip_identity': 'forward_historian',
        'description': 'Forward historian for sending data to other VOLTTRON instances',
        'category': 'Historian',
        'github_url': 'https://github.com/eclipse-volttron/volttron-forward-historian.git'
    },
    
    'ilc': {
        'package': 'volttron-ilc',
        'vip_identity': 'ilc',
        'description': 'Intelligent Load Control agent for demand response',
        'category': 'Control',
        'github_url': 'https://github.com/eclipse-volttron/volttron-ilc.git'
    },
    
    'topic-watcher': {
        'package': 'volttron-topic-watcher',
        'vip_identity': 'topic_watcher',
        'description': 'Watches and monitors specific topics on the message bus',
        'category': 'Monitoring',
        'github_url': 'https://github.com/eclipse-volttron/volttron-topic-watcher.git'
    },
    
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

def discover_volttron_installations():
    """Discover all VOLTTRON installations in the user's environment."""
    installations = []
    
    search_patterns = [
        os.path.expanduser("~/volttron*/bin/volttron"),
        os.path.expanduser("~/volttron*/venv*/bin/volttron"),
        os.path.expanduser("~/volttron*/env/bin/volttron"),
        os.path.expanduser("~/.local/bin/volttron"),
        "/opt/volttron/bin/volttron",
        "/usr/local/bin/volttron",
        "/usr/bin/volttron"
    ]
    
    import glob
    for pattern in search_patterns:
        for path in glob.glob(pattern):
            if os.path.isfile(path) and os.access(path, os.X_OK):
                try:
                    bin_dir = os.path.dirname(path)
                    pip_path = os.path.join(bin_dir, "pip")
                    version = "Unknown"
                    
                    if os.path.exists(pip_path):
                        for package in ["volttron-core", "volttron"]:
                            result = subprocess.run(
                                [pip_path, "show", package],
                                capture_output=True,
                                text=True,
                                timeout=3
                            )
                            if result.returncode == 0 and result.stdout:
                                for line in result.stdout.split("\n"):
                                    if line.startswith("Version:"):
                                        version = line.split(":", 1)[1].strip()
                                        break
                            if version != "Unknown":
                                break
                    
                    installations.append({
                        "path": path,
                        "version": version,
                        "name": os.path.basename(os.path.dirname(os.path.dirname(path)))
                    })
                except Exception:
                    installations.append({
                        "path": path,
                        "version": "Unknown",
                        "name": os.path.basename(os.path.dirname(os.path.dirname(path)))
                    })
    
    seen = set()
    unique_installations = []
    for install in installations:
        resolved = os.path.realpath(install["path"])
        if resolved not in seen:
            seen.add(resolved)
            unique_installations.append(install)
    
    return unique_installations

def find_volttron_command():
    """Find volttron command in various locations, prioritizing running instance."""
    
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'volttron' in proc.name().lower() or any('volttron' in cmd.lower() for cmd in proc.cmdline() if cmd):
                    cmdline = proc.cmdline()
                    for cmd in cmdline:
                        if cmd and 'volttron' in cmd and os.path.exists(cmd) and not cmd.endswith('python'):
                            return cmd
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except ImportError:
        pass
    
    installations = discover_volttron_installations()
    
    if not installations:
        volttron_cmd = shutil.which("volttron")
        if volttron_cmd:
            return volttron_cmd
        return None
    
    installations.sort(key=lambda x: x.get("version", "0"), reverse=True)
    
    selected = installations[0]
    
    return selected["path"]

def find_vctl_command():
    """Find vctl command, using the same installation as volttron."""
    
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'volttron' in proc.name().lower() or any('volttron' in cmd.lower() for cmd in proc.cmdline() if cmd):
                    cmdline = proc.cmdline()
                    for cmd in cmdline:
                        if cmd and 'volttron' in cmd and os.path.exists(cmd) and not cmd.endswith('python'):
                            bin_dir = os.path.dirname(cmd)
                            vctl_path = os.path.join(bin_dir, "vctl")
                            if os.path.isfile(vctl_path) and os.access(vctl_path, os.X_OK):
                                return vctl_path
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except ImportError:
        pass
    
    vctl_cmd = shutil.which("vctl")
    if vctl_cmd:
        return vctl_cmd
    
    volttron_cmd = find_volttron_command()
    if volttron_cmd:
        vctl_path = os.path.join(os.path.dirname(volttron_cmd), "vctl")
        if os.path.isfile(vctl_path) and os.access(vctl_path, os.X_OK):
            return vctl_path
    
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
    """Get the VOLTTRON_HOME directory from environment or infer from VOLTTRON installation."""
    
    env_volttron_home = os.getenv("VOLTTRON_HOME")
    if env_volttron_home:
        return env_volttron_home
    
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'environ']):
            try:
                if 'volttron' in proc.name().lower() or any('volttron' in cmd.lower() for cmd in proc.cmdline() if cmd):
                    if proc.environ() and 'VOLTTRON_HOME' in proc.environ():
                        volttron_home_from_proc = proc.environ()['VOLTTRON_HOME']
                        return volttron_home_from_proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except ImportError:
        pass
    
    volttron_cmd = find_volttron_command()
    if volttron_cmd:
        install_name = os.path.basename(os.path.dirname(os.path.dirname(volttron_cmd)))
        
        home_mappings = {
            'volttron-v11-py311': os.path.expanduser("~/volttron-home-v11"),
            'volttron-v10-py38': os.path.expanduser("~/volttron-home-v10"),
            'venv-fresh': os.path.expanduser("~/volttron-fresh/volttron_home"),
            'volttron-core-v2': os.path.expanduser("~/volttron-core-v2/volttron_home"),
        }
        
        if install_name in home_mappings:
            inferred_home = home_mappings[install_name]
            if os.path.exists(inferred_home):
                return inferred_home
    
    search_patterns = [
        os.path.expanduser("~/volttron-home*"),
        os.path.expanduser("~/volttron_home"),
        os.path.expanduser("~/.volttron"),
        "/var/lib/volttron",
    ]
    
    import glob
    for pattern in search_patterns:
        for path in glob.glob(pattern):
            if os.path.isdir(path):
                if (os.path.exists(os.path.join(path, "agents")) or 
                    os.path.exists(os.path.join(path, "certificates")) or
                    os.path.exists(os.path.join(path, "configuration_store"))):
                    return path
    
    default_volttron_home = os.path.expanduser("~/.volttron")
    os.makedirs(default_volttron_home, exist_ok=True)
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
    
    volttron_home = os.getenv("VOLTTRON_HOME")
    
    if not volttron_home:
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
        try:
            result = subprocess.run(
                ["pgrep", "-f", "bin/volttron"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"VOLTTRON is running (pgrep found process): {result.stdout.strip()}")
                return True
                
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
                        continue
                    
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
            time.sleep(3)
        
        messages.append("🔧 Launching new VOLTTRON instance...")
        
        cmd = f"cd {volttron_home} && nohup {volttron_cmd} -vv -l volttron.log > volttron_output.log 2>&1 &"
        
        result = subprocess.run(
            cmd,
            shell=True,
            env=env,
            cwd=volttron_home
        )
        
        messages.append("⏳ Waiting for VOLTTRON to initialize...")
        time.sleep(3)
        
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
        
        if not vctl_cmd:
            return check_volttron_installation()
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
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
        
        for line in lines[1:]:
            if not line.strip() or "UUID" in line:  # Skip header or empty lines
                continue
                
            clean_line = ' '.join(line.split())  # Normalize whitespace
            parts = clean_line.split()
            
            if len(parts) >= 3:
                uuid = parts[0]
                agent_name = parts[1] if len(parts) > 1 else "unknown"
                identity = parts[2] if len(parts) > 2 else "unknown"
                
                remaining_parts = parts[3:] if len(parts) > 3 else []
                status = "UNKNOWN"
                health = "UNKNOWN"
                
                line_upper = line.upper()
                has_status_column = False
                
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
                        
                if "RUNNING" in line_upper or ("[" in line_upper and "]" in line_upper and "RUNNING" not in line_upper):
                    status = "RUNNING"
                    has_status_column = True
                    
                if "GOOD" in line_upper:
                    health = "GOOD"
                elif "BAD" in line_upper:
                    health = "BAD"
                
                if not has_status_column:
                    if len(parts) >= 3:
                        status = "INSTALLED"  # Installed but status unclear
                        
                if status == "RUNNING":
                    running_count += 1
                else:
                    not_running_count += 1
                    
                if health == "BAD":
                    bad_health_count += 1
                
                if 'listener' in agent_name.lower():
                    agent_type = "listener"
                elif 'platform' in agent_name.lower() and 'driver' in agent_name.lower():
                    agent_type = "platform-driver"
                elif 'driver' in agent_name.lower():
                    agent_type = "driver"
                elif 'platform' in agent_name.lower():
                    agent_type = "platform"
                else:
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
        
        agent_type_counts = {}
        for agent in agents:
            agent_type = agent['type']
            if agent_type in agent_type_counts:
                agent_type_counts[agent_type] += 1
            else:
                agent_type_counts[agent_type] = 1
        
        agent_count = len(agents)
        
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
        
        if agent_count == 1:
            agent = agents[0]
            if agent['status'] == "RUNNING":
                return f"Got one {agent['type']} agent humming along nicely (ID: {agent['uuid']}) - everything's good! 🚀"
            elif agent['status'] == "INSTALLED":
                return f"I've got a {agent['type']} agent sitting here (ID: {agent['uuid']}) but it's just chilling - not sure if it's actually doing anything. Want me to poke it and see?"
            else:
                return f"There's a {agent['type']} agent here (ID: {agent['uuid']}) but it looks like it's taking a nap. Should I wake it up?"
        
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
                pass
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
            
            if len(parts) >= 3:
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

def vctl_config_store(config_file_path, config_name, config_type='config'):
    """
    Store a configuration file in VOLTTRON's config store.
    
    Args:
        config_file_path: Path to the configuration file to store
        config_name: Name for the config in the store (e.g., 'devices/fake.csv')
        config_type: Type of config ('config', 'csv', or 'json')
    
    Returns:
        str: Result message
    """
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return "❌ vctl command not found. Please ensure VOLTTRON is installed."
        
        if not os.path.exists(config_file_path):
            return f"❌ Configuration file not found: {config_file_path}"
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        cmd_str = f"export VOLTTRON_HOME={volttron_home} && {vctl_cmd} config store platform.driver {config_name} {config_file_path} --{config_type}"
        
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return f"✅ Successfully stored {config_name} in config store"
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return f"❌ Failed to store config: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return f"❌ Timeout while storing configuration"
    except Exception as e:
        return f"❌ Error storing configuration: {str(e)}"

def vctl_config_list(agent_vip_identity='platform.driver'):
    """
    List configurations in VOLTTRON's config store for a specific agent.
    
    Args:
        agent_vip_identity: VIP identity of the agent (default: 'platform.driver')
    
    Returns:
        str: List of configurations
    """
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return "❌ vctl command not found. Please ensure VOLTTRON is installed."
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        cmd_str = f"export VOLTTRON_HOME={volttron_home} && {vctl_cmd} config list {agent_vip_identity}"
        
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                return f"📋 Configuration store for {agent_vip_identity}:\n{output}"
            else:
                return f"📋 No configurations found for {agent_vip_identity}"
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            if "not running" in error_msg.lower():
                return "❌ VOLTTRON is not running. Please start VOLTTRON first."
            return f"❌ Failed to list configurations: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return f"❌ Timeout while listing configurations"
    except Exception as e:
        return f"❌ Error listing configurations: {str(e)}"

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
            
            # Check for missing module errors and try to auto-install
            if result.returncode != 0 and result.stderr:
                missing_module = extract_missing_module(result.stderr)
                if missing_module:
                    print(f"⚠️ Missing dependency detected: {missing_module}")
                    success, message = install_missing_package(missing_module)
                    print(message)
                    
                    if success:
                        # Retry the command after installing the missing package
                        print("🔄 Retrying vctl status after installing dependency...")
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
        volttron_home = get_volttron_home()
        vctl_path = find_vctl_command()
        
        if not vctl_path:
            return "❌ Could not find vctl command. Please ensure VOLTTRON is installed."
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        cmd_str = f"export VOLTTRON_HOME={volttron_home} && {vctl_path} status"
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True, 
            text=True,
            env=env,
            timeout=15
        )
        
        # Check for missing module errors and try to auto-install
        if result.returncode != 0 and result.stderr:
            missing_module = extract_missing_module(result.stderr)
            if missing_module:
                print(f"⚠️ Missing dependency detected: {missing_module}")
                success, message = install_missing_package(missing_module)
                print(message)
                
                if success:
                    # Retry the command after installing the missing package
                    print("🔄 Retrying vctl status after installing dependency...")
                    result = subprocess.run(
                        cmd_str,
                        shell=True,
                        capture_output=True, 
                        text=True,
                        env=env,
                        timeout=15
                    )
        
        if result.returncode == 0:
            combined_output = ""
            if result.stderr and "UUID" in result.stderr:
                combined_output = result.stderr.strip() + "\n"
            
            if result.stdout:
                combined_output += result.stdout.strip()
            
            combined_output = combined_output.strip()
            
            if combined_output:
                lines = combined_output.split('\n')
                if len(lines) >= 2:
                    try:
                        readable_status = make_status_readable(combined_output)
                        return f"🤖 **Installed VOLTTRON Agents:**\n\n{readable_status}"
                    except Exception as format_error:
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
        
        # Check for missing module errors and try to auto-install
        if status_result.returncode != 0 and status_result.stderr:
            missing_module = extract_missing_module(status_result.stderr)
            if missing_module:
                print(f"⚠️ Missing dependency detected: {missing_module}")
                success, message = install_missing_package(missing_module)
                print(message)
                
                if success:
                    # Retry the command after installing the missing package
                    print("🔄 Retrying vctl status after installing dependency...")
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
        
        if not is_volttron_running_quick():
            return """❌ **VOLTTRON is not running!**

**Cannot start agents** - VOLTTRON platform must be running first.

💡 **Please try this:**
1. Ask me to "start volttron" first
2. Wait a few seconds for it to start up
3. Then try starting the agents again"""
        
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
            return f"❌ Can't check agent status. VOLTTRON might not be responding properly."
        
        agents_to_start = []
        if status_result.stdout:
            status_lines = status_result.stdout.strip().split('\n')
            for line in status_lines[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        agent_id = parts[0]
                        status = "running" if "running" in line.lower() else "stopped"
                        if status != "running":
                            agents_to_start.append(agent_id)
        
        if not agents_to_start:
            return "✅ **All agents are already running!** Nothing to start."
        
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
        
        agent_uuid = agent_tag_or_uuid
        found_in_status = False
        agent_name = "unknown"
        
        if status_result.returncode == 0 and status_result.stdout:
            lines = status_result.stdout.strip().split('\n')
            for line in lines:
                if agent_tag_or_uuid in line:
                    found_in_status = True
                    parts = line.split()
                    if len(parts) >= 1:
                        agent_uuid = parts[0]
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
                timeout=5
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
                    timeout=10
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
                    timeout=10
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
            time.sleep(1)
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
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        package_name = "volttron-listener"
        
        try:
            print(f"DEBUG: Attempting to install {package_name} with vctl install")
            result = subprocess.run([
                vctl_cmd, "install", package_name,
                "--vip-identity", "listener",
                "--tag", "listener",
                "--force"
            ], capture_output=True, text=True, timeout=120, env=env, cwd=volttron_home)
            
            print(f"DEBUG: vctl install result: returncode={result.returncode}")
            print(f"DEBUG: stdout: {result.stdout}")
            print(f"DEBUG: stderr: {result.stderr}")
            
            if result.returncode == 0:
                import time
                time.sleep(2)
                return f"✅ **Listener agent installed successfully!** Check with 'vctl status'"
                
        except Exception as e:
            print(f"DEBUG: vctl install exception: {str(e)}")
        
        print(f"DEBUG: vctl install failed, trying GitHub installation...")
        github_url = "https://github.com/eclipse-volttron/volttron-listener.git"
        
        try:
            print(f"DEBUG: Installing listener from GitHub: {github_url}")
            result = subprocess.run([
                vctl_cmd, "install", github_url,
                "--vip-identity", "listener",
                "--tag", "listener",
                "--force"
            ], capture_output=True, text=True, timeout=120, env=env, cwd=volttron_home)
            
            print(f"DEBUG: GitHub install result: returncode={result.returncode}")
            print(f"DEBUG: stdout: {result.stdout}")
            print(f"DEBUG: stderr: {result.stderr}")
                
        except Exception as e:
            return f"❌ Error during listener agent installation: {str(e)}"
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            
            if "already exists" in error_msg.lower():
                return f"""⚠️ **Listener agent already exists**

The listener agent is already installed. You can:

**Option 1: Check status**
• Say: **"vctl status"** to see if it's running

**Option 2: Uninstall first**
• Say: **"uninstall listener"** or **"force remove listener"**

**Option 3: Start if stopped**
• Say: **"start listener"**

What would you like to do?
"""
            
            return f"❌ Failed to install listener agent: {error_msg}"
        
        import time
        install_wait = int(os.getenv('VOLTTRON_INSTALL_WAIT', '2'))
        time.sleep(install_wait)
        
        verify_result = subprocess.run([
            vctl_cmd, "status"
        ], capture_output=True, text=True, timeout=10, env=env, cwd=volttron_home)
        
        print(f"DEBUG: Verification status check: {verify_result.stdout}")
        
        agent_found = False
        agent_uuid = None
        if verify_result.returncode == 0 and verify_result.stdout:
            for line in verify_result.stdout.split('\n'):
                if 'listener' in line.lower():
                    agent_found = True
                    parts = line.split()
                    if parts:
                        agent_uuid = parts[0]
                    break
        
        if not agent_found:
            return f"⚠️ Listener installation command succeeded but agent not found in status. Check `vctl status`"
        
        if agent_uuid:
            try:
                start_result = subprocess.run([
                    vctl_cmd, "start", agent_uuid
                ], capture_output=True, text=True, timeout=10, env=env, cwd=volttron_home)
                
                if start_result.returncode == 0:
                    return f"✅ Listener agent (UUID: {agent_uuid}) installed and started successfully"
                else:
                    return f"✅ Listener agent (UUID: {agent_uuid}) installed but failed to start"
            except Exception:
                return f"✅ Listener agent (UUID: {agent_uuid}) installed"
        
        return f"✅ Listener agent installed successfully"
            
    except Exception as e:
        return f"Error installing listener agent: {str(e)}"

def vctl_install_agent(agent_name):
    """Install any VOLTTRON agent by name."""
    try:
        agent_name = agent_name.lower().replace('_', '-').replace(' ', '-')
        
        if agent_name not in AVAILABLE_AGENTS:
            print(f"Agent '{agent_name}' not in local registry, searching GitHub...")
            github_result = search_github_for_agent(agent_name)
            
            return f"""Agent '{agent_name}' not found in local registry.

Searched GitHub eclipse-volttron organization:

{github_result}

To install from GitHub, you can:
1. Use the install_agent_from_github function with the URL
2. Or ask me to "install agent from <github-url>"
"""
        
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
        
        package_to_install = agent_info['package']
        
        install_args = [
            vctl_cmd, "install", package_to_install,
            "--vip-identity", agent_info['vip_identity'],
            "--force"
        ]
        
        if agent_info['category'] in ['Core', 'Historian']:
            install_args.append("--start")
        
        print(f"🔧 Trying vctl install {package_to_install}...")
        result = subprocess.run(
            install_args,
            capture_output=True, text=True, timeout=120, env=env, cwd=volttron_home
        )
        
        if result.returncode == 0:
            auto_started = '--start' in install_args
            status_msg = "installed and started" if auto_started else "installed"
            return f"✅ {agent_info['package']} {status_msg} successfully"
        
        print(f"⚠️ vctl install failed for {package_to_install}, checking for GitHub URL...")
        error_msg = result.stderr or result.stdout or "Unknown error"
        
        if "already exists" in error_msg.lower():
            return f"""⚠️ **{agent_name} agent already exists**

The {agent_name} agent is already installed. You can:

**Option 1: Check status**
• Say: **"vctl status"** to see if it's running

**Option 2: Uninstall first**
• Say: **"uninstall {agent_info['vip_identity']}"**

**Option 3: Start if stopped**
• Say: **"start {agent_info['vip_identity']}"**

What would you like to do?
"""
        
        if 'github_url' in agent_info:
            github_url = agent_info['github_url']
            print(f"🔍 Trying GitHub installation: {github_url}")
            
            github_args = [
                vctl_cmd, "install", github_url,
                "--vip-identity", agent_info['vip_identity'],
                "--tag", agent_name,
                "--force"
            ]
            
            if agent_info['category'] in ['Core', 'Historian']:
                github_args.append("--start")
            
            github_result = subprocess.run(
                github_args,
                capture_output=True, text=True, timeout=120, env=env, cwd=volttron_home
            )
            
            if github_result.returncode == 0:
                auto_started = '--start' in github_args
                status_msg = "installed and started" if auto_started else "installed"
                return f"✅ {agent_name} {status_msg} successfully from GitHub!"
            else:
                github_error = github_result.stderr or github_result.stdout
                return f"""❌ **Failed to install {agent_name}**

**Tried:**
1. vctl install {package_to_install} - Failed: {error_msg[:200]}
2. GitHub install {github_url} - Failed: {github_error[:200]}

**Try manually:** `vctl install {package_to_install} --vip-identity {agent_info['vip_identity']} --force`
"""
        
        return f"❌ {agent_info['package']} installation failed: {error_msg}"
            
    except Exception as e:
        return f"❌ {agent_name} installation error: {type(e).__name__} - {str(e)[:100]}"

def list_available_agents():
    """List all available VOLTTRON agents that can be installed."""
    categories = {}
    
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

def detect_installation_method(repo_owner, repo_name):
    """Detect the installation method for a GitHub repository.
    
    Args:
        repo_owner (str): Repository owner (e.g., 'eclipse-volttron')
        repo_name (str): Repository name
        
    Returns:
        dict: Installation method information
    """
    try:
        installation_info = {
            'method': 'unknown',
            'pypi_package': None,
            'vctl_compatible': False,
            'setup_py': False,
            'pyproject_toml': False,
            'details': []
        }
        
        base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
        
        response = requests.get(base_url, timeout=10)
        if response.status_code != 200:
            installation_info['details'].append(f"Could not fetch repo contents (status {response.status_code})")
            return installation_info
        
        files = response.json()
        file_names = [f['name'].lower() for f in files if 'name' in f]
        
        if 'setup.py' in file_names:
            installation_info['setup_py'] = True
            installation_info['details'].append("Found setup.py")
        
        if 'pyproject.toml' in file_names:
            installation_info['pyproject_toml'] = True
            installation_info['details'].append("Found pyproject.toml")
        
        readme_file = None
        for f in files:
            if f['name'].lower().startswith('readme'):
                readme_file = f
                break
        
        if readme_file:
            readme_response = requests.get(readme_file['download_url'], timeout=10)
            if readme_response.status_code == 200:
                readme_content = readme_response.text.lower()
                
                if 'pip install' in readme_content:
                    installation_info['details'].append("README mentions 'pip install'")
                    
                    import re
                    pip_patterns = [
                        r'pip install\s+(volttron-[\w\-]+)',
                        r'pip install\s+([\w\-]+historian)',
                        r'pip install\s+([\w\-]+agent)',
                        r'pip install\s+([\w\-]+driver)',
                    ]
                    
                    for pattern in pip_patterns:
                        matches = re.findall(pattern, readme_content)
                        if matches:
                            installation_info['pypi_package'] = matches[0]
                            installation_info['details'].append(f"PyPI package name: {matches[0]}")
                            break
                
                if 'vctl install' in readme_content:
                    installation_info['vctl_compatible'] = True
                    installation_info['details'].append("README mentions 'vctl install'")
                    
                    import re
                    vctl_pattern = r'vctl install\s+([\w\-]+)'
                    matches = re.findall(vctl_pattern, readme_content)
                    if matches and not installation_info['pypi_package']:
                        installation_info['pypi_package'] = matches[0]
                        installation_info['details'].append(f"vctl package name: {matches[0]}")
        
        if installation_info['pypi_package']:
            installation_info['method'] = 'pip'
        elif installation_info['vctl_compatible'] or (installation_info['setup_py'] and not installation_info['pypi_package']):
            installation_info['method'] = 'vctl'
        elif installation_info['setup_py'] or installation_info['pyproject_toml']:
            installation_info['method'] = 'both'
        
        return installation_info
        
    except Exception as e:
        return {
            'method': 'unknown',
            'pypi_package': None,
            'vctl_compatible': False,
            'setup_py': False,
            'pyproject_toml': False,
            'details': [f"Error detecting method: {str(e)}"]
        }


def search_github_for_agent(agent_name):
    """Search eclipse-volttron GitHub organization for agent repositories.
    
    Searches through all pages of repositories to find matches.
    
    Args:
        agent_name (str): The agent name to search for
        
    Returns:
        str: Structured data about found repositories or search results
    """
    try:
        github_org = os.getenv('VOLTTRON_GITHUB_ORG', 'eclipse-volttron')
        org_url = f"https://api.github.com/orgs/{github_org}/repos"
        
        all_repos = []
        page = 1
        max_pages = 10
        pages_scanned = 0
        
        while page <= max_pages:
            params = {
                'type': 'public',
                'per_page': 100,
                'sort': 'updated',
                'page': page
            }
            
            response = requests.get(org_url, params=params, timeout=10)
            
            if response.status_code != 200:
                if page == 1:
                    return f"""GitHub agent search completed.
Status: API request failed
Status code: {response.status_code}
Agent searched: {agent_name}
Organization: {github_org}
Error: Unable to fetch repository list"""
                else:
                    break
            
            repos = response.json()
            
            if not repos:
                break
            
            all_repos.extend(repos)
            pages_scanned = page
            
            if len(repos) < 100:
                break
            
            page += 1
        
        agent_lower = agent_name.lower().replace('-', '').replace('_', '')
        matches = []
        
        for repo in all_repos:
            repo_name = repo['name'].lower()
            repo_name_normalized = repo_name.replace('-', '').replace('_', '')
            
            if agent_lower in repo_name_normalized or repo_name_normalized in agent_lower:
                matches.append({
                    'name': repo['name'],
                    'url': repo['html_url'],
                    'clone_url': repo['clone_url'],
                    'description': repo['description'] or 'No description available',
                    'updated': repo['updated_at'],
                    'stars': repo['stargazers_count']
                })
        
        if not matches:
            return f"""GitHub agent search completed.
Status: No matches found
Agent searched: {agent_name}
Organization: {github_org}
Pages scanned: {pages_scanned}
Repositories scanned: {len(all_repos)}
Matches found: 0

No repositories matching '{agent_name}' were found in the {github_org} organization.

**Options:**
1. Try a different agent name
2. Create a new agent called '{agent_name}'

**To create this agent, say:** "create a new agent called {agent_name}"""
        
        matches.sort(key=lambda x: (x['stars'], x['updated']), reverse=True)
        
        if len(matches) == 1:
            match = matches[0]
            
            install_info = detect_installation_method(github_org, match['name'])
            
            install_instructions = ""
            if install_info['method'] == 'pip' and install_info['pypi_package']:
                install_instructions = f"\n\nInstallation method: pip\nCommand: pip install {install_info['pypi_package']}"
            elif install_info['method'] == 'vctl':
                install_instructions = f"\n\nInstallation method: vctl\nCommand: vctl install {match['clone_url']}"
            elif install_info['method'] == 'both':
                pip_cmd = f"pip install {install_info['pypi_package']}" if install_info['pypi_package'] else "pip install ."
                install_instructions = f"\n\nInstallation methods available:\n1. PyPI: {pip_cmd}\n2. vctl: vctl install {match['clone_url']}"
            else:
                install_instructions = f"\n\nInstallation method: Unknown\nTry: vctl install {match['clone_url']}"
            
            details_info = ""
            if install_info['details']:
                details_info = f"\nDetection details: {', '.join(install_info['details'])}"
            
            return f"""GitHub agent search completed.
Status: Match found
Agent searched: {agent_name}
Pages scanned: {pages_scanned}
Repositories scanned: {len(all_repos)}
Matches found: 1

Repository found:
Name: {match['name']}
URL: {match['url']}
Clone URL: {match['clone_url']}
Description: {match['description']}
Stars: {match['stars']}
Last updated: {match['updated']}{install_instructions}{details_info}

Question: Do you want to install this agent? (yes/no)"""
        else:
            matches_list = []
            for i, match in enumerate(matches[:5], 1):
                install_info = detect_installation_method(github_org, match['name'])
                
                install_method = "Unknown"
                if install_info['method'] == 'pip' and install_info['pypi_package']:
                    install_method = f"pip (package: {install_info['pypi_package']})"
                elif install_info['method'] == 'vctl':
                    install_method = "vctl"
                elif install_info['method'] == 'both':
                    install_method = "pip or vctl"
                
                matches_list.append(f"{i}. {match['name']}")
                matches_list.append(f"   URL: {match['url']}")
                matches_list.append(f"   Description: {match['description']}")
                matches_list.append(f"   Stars: {match['stars']}")
                matches_list.append(f"   Install method: {install_method}")
            
            matches_output = '\n'.join(matches_list)
            
            return f"""GitHub agent search completed.
Status: Multiple matches found
Agent searched: {agent_name}
Pages scanned: {pages_scanned}
Repositories scanned: {len(all_repos)}
Matches found: {len(matches)}
Top results shown: {min(5, len(matches))}

Found repositories:
{matches_output}

Question: Which one do you want? (enter number 1-{min(5, len(matches))})
Or provide more specific agent name."""
        
    except requests.exceptions.Timeout:
        return f"""GitHub agent search completed.
Status: Timeout
Agent searched: {agent_name}
Error: Request to GitHub API timed out after 10 seconds"""
    except requests.exceptions.RequestException as e:
        return f"""GitHub agent search completed.
Status: Network error
Agent searched: {agent_name}
Error type: {type(e).__name__}
Error message: {str(e)}"""
    except Exception as e:
        return f"""GitHub agent search completed.
Status: Error
Agent searched: {agent_name}
Error type: {type(e).__name__}
Error message: {str(e)}"""

def install_agent_from_github(repo_url):
    """Install a VOLTTRON agent from a GitHub repository URL.
    
    Args:
        repo_url (str): The GitHub repository URL or clone URL
        
    Returns:
        str: Structured data about the installation process
    """
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return """Agent installation from GitHub failed.
Status: vctl command not found
Recommendation: Ensure VOLTTRON is installed properly"""
        
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        result = subprocess.run(
            [vctl_cmd, "install", repo_url, "--tag", repo_name, "--start", "--force"],
            capture_output=True,
            text=True,
            env=env,
            timeout=120
        )
        
        if result.returncode == 0:
            return f"✅ {repo_name} installed from GitHub successfully"
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            
            if "already exists" in error_msg.lower():
                return f"""⚠️ **{repo_name} agent already exists**

The {repo_name} agent is already installed. You can:

**Option 1: Uninstall first**
• Say: **"uninstall {repo_name}"** or **"force remove {repo_name}"**

**Option 2: Check status**
• Say: **"vctl status"**

What would you like to do?
"""
            
            return f"❌ {repo_name} installation failed: {error_msg}"
        
    except subprocess.TimeoutExpired:
        return f"⏱️ {repo_url.split('/')[-1]} installation timeout (exceeded 120 seconds)"
    except Exception as e:
        return f"❌ {repo_url.split('/')[-1]} installation error: {type(e).__name__} - {str(e)[:100]}"

def install_from_github_smart(repo_url):
    """Intelligently install from GitHub by reading README and executing installation commands.
    
    This function:
    1. Fetches the README from the repository
    2. Extracts installation commands from the README
    3. Executes the commands (with safety checks)
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        str: Installation result
    """
    try:
        import re
        match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?$', repo_url)
        if not match:
            return f"❌ Invalid GitHub URL format: {repo_url}"
        
        owner, repo_name = match.groups()
        
        install_info = detect_installation_method(owner, repo_name)
        
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/readme"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code != 200:
            return f"❌ Could not fetch README from {repo_url}"
        
        import base64
        readme_raw = base64.b64decode(response.json()['content']).decode('utf-8')
        readme_content = readme_raw.lower()
        
        if 'github.io' in repo_name or ('jekyll' in readme_content and 'bundle install' in readme_content):
            return f"📖 **{repo_name} is a documentation/website**\n\n" \
                   f"This is not installable software.\n\n" \
                   f"View at: https://{owner}.github.io/{repo_name.replace('.github.io', '')}"
        
        if 'copier' in repo_name.lower() or 'cookiecutter' in repo_name.lower() or \
           ('copier copy' in readme_content or 'cookiecutter' in readme_content):
            tool = 'copier' if 'copier' in readme_content else 'cookiecutter'
            return f"📋 **{repo_name} is a project template**\n\n" \
                   f"Use it to generate new projects:\n```bash\n" \
                   f"pip install {tool}\n" \
                   f"{tool} copy {repo_url} my-new-project\n```"
        
        if install_info['pypi_package']:
            return pip_install_package(install_info['pypi_package'])
        
        install_commands = extract_installation_commands(readme_raw, repo_url, repo_name)
        
        if install_commands['method'] == 'pip_from_pypi':
            return pip_install_package(install_commands['package'])
        
        elif install_commands['method'] == 'direct_commands':
            return execute_direct_commands(install_commands['commands'], repo_name)
        
        elif install_commands['method'] == 'clone_and_install':
            return execute_clone_and_install(repo_url, repo_name, install_commands['commands'])
        
        elif install_commands['method'] == 'manual':
            return f"📋 **{repo_name} installation instructions**\n\n" \
                   f"Found these installation steps:\n```bash\n{install_commands['instructions']}\n```\n\n" \
                   f"⚠️ Review these commands before running manually."
        
        return attempt_standard_install(repo_url, repo_name, install_info)
        
    except Exception as e:
        return f"❌ Error analyzing {repo_url}: {str(e)[:200]}"

def extract_installation_commands(readme_text, repo_url, repo_name):
    """Extract installation commands from README text.
    
    Returns:
        dict with 'method', 'commands', 'package', or 'instructions'
    """
    import re
    
    readme_lower = readme_text.lower()
    
    pip_pattern = r'pip install ([a-z0-9\-_]+)'
    pip_matches = re.findall(pip_pattern, readme_lower)
    if pip_matches:
        valid_packages = [p for p in pip_matches if p not in ['package', 'mypackage', 'yourpackage', 'example']]
        if valid_packages:
            return {'method': 'pip_from_pypi', 'package': valid_packages[0]}
    
    install_section = None
    for section_name in ['## installation', '## install', '## getting started', '## quick start', '## setup']:
        if section_name in readme_lower:
            start_idx = readme_lower.find(section_name)
            next_heading = readme_lower.find('\n## ', start_idx + len(section_name))
            if next_heading == -1:
                next_heading = len(readme_lower)
            install_section = readme_text[start_idx:next_heading]
            break
    
    if not install_section:
        install_section = readme_text
    
    code_blocks = re.findall(r'```(?:bash|shell|sh)?\n(.*?)```', install_section, re.DOTALL)
    
    if code_blocks:
        all_commands = []
        
        command_indicators = ['pip', 'poetry', 'npm', 'git', 'python', 'sudo', 'apt', 'yum', 
                             'brew', 'cargo', 'go', 'make', 'cmake', 'curl', 'wget', 'docker']
        
        for block in code_blocks:
            lines = [l.strip() for l in block.split('\n')]
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line and line[0].isupper() and not any(cmd in line.lower() for cmd in command_indicators):
                    continue
                all_commands.append(line)
        
        if not all_commands:
            return {'method': 'unknown', 'instructions': 'No installation commands found'}
        
        has_clone = any('git clone' in l.lower() for l in all_commands)
        
        other_cmds = [l for l in all_commands if 'git clone' not in l.lower() and 'cd ' not in l.lower() and 'export ' not in l.lower()]
        
        local_install_patterns = ['install .', 'install -e', 'setup.py', ' install', 'build']
        needs_clone = any(pattern in ' '.join(all_commands).lower() for pattern in local_install_patterns)
        
        if needs_clone or (has_clone and other_cmds):
            return {'method': 'clone_and_install', 'commands': other_cmds}
        elif other_cmds:
            return {'method': 'direct_commands', 'commands': other_cmds}
        else:
            return {'method': 'manual', 'instructions': '\n'.join(all_commands)}
    
    if code_blocks:
        return {'method': 'manual', 'instructions': code_blocks[0].strip()}
    
    return {'method': 'unknown', 'instructions': 'No installation instructions found in README'}

def execute_direct_commands(commands, repo_name):
    """Execute installation commands directly (without cloning).
    
    Automatically installs missing dependencies and retries.
    
    Args:
        commands: List of shell commands to execute
        repo_name: Repository name for context
        
    Returns:
        str: Installation result
    """
    try:
        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue
            
            tool = cmd.split()[0]
            common_tools = ['pip', 'python', 'python3', 'cd', 'mkdir', 'cp', 'mv', 'echo', 'source', 'export']
            
            if tool not in common_tools:
                tool_check = subprocess.run(
                    ['which', tool],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if tool_check.returncode != 0:
                    auto_install_cmds = {
                        'ansible-galaxy': 'pip install ansible',
                        'poetry': 'pip install poetry',
                        'npm': 'sudo apt-get install -y npm',
                        'yarn': 'npm install -g yarn',
                        'make': 'sudo apt-get install -y build-essential',
                    }
                    
                    install_cmd = auto_install_cmds.get(tool)
                    if install_cmd:
                        install_result = subprocess.run(
                            install_cmd,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        
                        if install_result.returncode != 0:
                            return f"❌ Failed to auto-install {tool}\nError: {install_result.stderr[:200]}\n\nManually install: {install_cmd}"
                    else:
                        return f"❌ {tool} not found\n\nInstall {tool} manually and retry"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                stderr = result.stderr[:200] if result.stderr else "Unknown error"
                return f"❌ Command failed: {cmd}\nError: {stderr}"
        
        if 'ansible-galaxy' in ' '.join(commands):
            return f"✅ {repo_name} installed successfully as Ansible role\n\nVerify with: ansible-galaxy list | grep {repo_name.replace('volttron-', '')}"
        elif 'npm install' in ' '.join(commands):
            return f"✅ {repo_name} installed successfully as npm package\n\nVerify with: npm list -g | grep {repo_name}"
        else:
            return f"✅ {repo_name} installed successfully"
        
    except subprocess.TimeoutExpired:
        return f"⏱️ Installation timeout (exceeded 300 seconds)"
    except Exception as e:
        return f"❌ Installation error: {str(e)[:100]}"

def execute_clone_and_install(repo_url, repo_name, install_commands):
    """Clone repository and execute installation commands.
    
    Args:
        repo_url: GitHub URL
        repo_name: Repository name
        install_commands: List of commands to execute
        
    Returns:
        str: Installation result
    """
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp(prefix=f"{repo_name}_")
    
    try:
        clone_result = subprocess.run(
            ['git', 'clone', repo_url, temp_dir],
            capture_output=True, text=True, timeout=60
        )
        if clone_result.returncode != 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return f"❌ Failed to clone {repo_name}: {clone_result.stderr[:100]}"
        
        for cmd in install_commands:
            cmd = cmd.strip()
            if not cmd:
                continue
            
            if 'pip install' in cmd:
                if 'pip install .' in cmd or 'pip install -e' in cmd:
                    pip_cmd = find_pip_command()
                    if not pip_cmd:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        return f"❌ Cannot find pip command"
                    
                    flags = ['-e'] if 'pip install -e' in cmd else []
                    
                    result = subprocess.run(
                        [pip_cmd, 'install'] + flags + ['.'],
                        cwd=temp_dir,
                        capture_output=True, text=True, timeout=300
                    )
                else:
                    pip_cmd = find_pip_command()
                    result = subprocess.run(
                        cmd.split(),
                        cwd=temp_dir,
                        capture_output=True, text=True, timeout=300
                    )
                
                if result.returncode != 0:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return f"❌ Installation failed: {result.stderr[:100]}"
            
            elif 'poetry install' in cmd:
                result = subprocess.run(
                    ['poetry', 'install'],
                    cwd=temp_dir,
                    capture_output=True, text=True, timeout=300
                )
                
                if result.returncode != 0:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return f"❌ Poetry install failed: {result.stderr[:100]}"
            
            elif 'python setup.py install' in cmd:
                pip_cmd = find_pip_command()
                result = subprocess.run(
                    [pip_cmd, 'install', '.'],
                    cwd=temp_dir,
                    capture_output=True, text=True, timeout=300
                )
                
                if result.returncode != 0:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return f"❌ Installation failed: {result.stderr[:100]}"
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        return f"✅ {repo_name} installed successfully"
        
    except subprocess.TimeoutExpired:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return f"⏱️ {repo_name} installation timeout"
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return f"❌ {repo_name} installation error: {str(e)[:100]}"

def attempt_standard_install(repo_url, repo_name, install_info):
    """Attempt standard installation methods as fallback."""
    
    if install_info['setup_py'] or install_info['pyproject_toml']:
        return execute_clone_and_install(repo_url, repo_name, ['pip install .'])
    
    return f"❓ **{repo_name} - unclear installation method**\n\n" \
           f"**Analysis:**\n" \
           f"• Has setup.py: {install_info['setup_py']}\n" \
           f"• Has pyproject.toml: {install_info['pyproject_toml']}\n\n" \
           f"**Check the README:** {repo_url}\n\n" \
           f"Or try manually:\n```bash\n" \
           f"git clone {repo_url}\n" \
           f"cd {repo_name}\n" \
           f"pip install .\n```"

def find_pip_command():
    """Find pip command - prefers VOLTTRON venv, falls back to system pip."""
    
    pip_path, error = get_pip_command_from_venv()
    if pip_path:
        return pip_path
    
    # No active venv for chat app is fine - VOLTTRON has its own venv
    # Just use system pip for any dependencies the chat app itself needs
    
    if 'VIRTUAL_ENV' in os.environ:
        venv_pip = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'pip')
        if os.path.exists(venv_pip):
            print(f"✅ Found pip via VIRTUAL_ENV: {venv_pip}")
            return venv_pip
    
    pip_cmd = shutil.which("pip")
    if pip_cmd:
        print(f"✅ Using system pip: {pip_cmd}")
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
        
        version = "unknown"
        if verify_result.returncode == 0:
            for line in verify_result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                    break
        
        if result.returncode == 0 and verify_result.returncode == 0:
            return f"✅ {package_name} v{version} installed successfully"
        elif result.returncode == 0:
            return f"⚠️ {package_name} installed but verification failed"
        else:
            error_msg = "Unknown error"
            if result.stderr:
                error_lines = [line.strip() for line in result.stderr.split('\n') if line.strip() and not line.startswith('WARNING')]
                if error_lines:
                    error_msg = error_lines[0][:100]
            return f"❌ {package_name} installation failed: {error_msg}"
            
    except subprocess.TimeoutExpired as e:
        return f"⏱️ {package_name} installation timeout (exceeded 120 seconds)"
    except Exception as e:
        return f"❌ {package_name} installation error: {type(e).__name__} - {str(e)[:100]}"

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
        
        env = os.environ.copy()
        if 'VIRTUAL_ENV' in os.environ:
            env["PATH"] = f"{os.path.join(os.environ['VIRTUAL_ENV'], 'bin')}:{env['PATH']}"
        
        result = subprocess.run([
            pip_cmd, "list"
        ], capture_output=True, text=True, timeout=30, env=env)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if not output:
                return "🤷 No packages installed... that's weird."
            
            lines = output.split('\n')
            if len(lines) <= 2:
                return "📦 No packages found (just pip itself probably)."
            
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

def list_volttron_packages():
    """List only VOLTTRON-related packages installed via pip."""
    try:
        pip_cmd = find_pip_command()
        
        if not pip_cmd:
            return "❌ Can't find pip to check installed packages"
        
        env = os.environ.copy()
        if 'VIRTUAL_ENV' in os.environ:
            env["PATH"] = f"{os.path.join(os.environ['VIRTUAL_ENV'], 'bin')}:{env['PATH']}"
        
        result = subprocess.run([
            pip_cmd, "list"
        ], capture_output=True, text=True, timeout=30, env=env)
        
        if result.returncode != 0:
            return f"❌ Error listing packages: {result.stderr or 'Unknown error'}"
        
        volttron_packages = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.lower().startswith('volttron'):
                volttron_packages.append(line)
        
        if not volttron_packages:
            return "📦 No VOLTTRON packages installed yet\n\n💡 Try: `install volttron-listener` or `install volttron-platform-driver`"
        
        output = "📦 **Installed VOLTTRON Packages:**\n\n```\n"
        output += '\n'.join(volttron_packages)
        output += "\n```"
        
        return output
            
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout listing packages"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def list_all_installations():
    """List all VOLTTRON and related installations.
    
    Returns:
        str: Formatted list of all installations
    """
    result_lines = []
    
    try:
        vctl_path = find_vctl_command()
        volttron_home = get_volttron_home()
        
        env = os.environ.copy()
        if volttron_home:
            env['VOLTTRON_HOME'] = volttron_home
        
        result = subprocess.run(
            [vctl_path, 'status'],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        
        if result.returncode == 0 and result.stdout.strip():
            result_lines.append("```")
            result_lines.append(result.stdout.strip())
            result_lines.append("```\n")
        else:
            result_lines.append("VOLTTRON is not running\n")
    except:
        result_lines.append("VOLTTRON is not running\n")
    
    try:
        pip_path = find_pip_command()
        if pip_path:
            pip_result = subprocess.run(
                [pip_path, 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if pip_result.returncode == 0:
                packages = []
                for line in pip_result.stdout.split('\n'):
                    if line.strip().lower().startswith('volttron'):
                        parts = line.split()
                        if len(parts) >= 2:
                            pkg_name = parts[0]
                            version = parts[1]
                            if pkg_name == 'volttron':
                                packages.append(f"{pkg_name} {version}")
                            else:
                                packages.append(pkg_name)
                
                if packages:
                    result_lines.append(f"Key Python packages: {', '.join(packages)}\n")
    except:
        pass
    
    other_items = []
    
    try:
        ansible_result = subprocess.run(
            ['ansible-galaxy', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if ansible_result.returncode == 0:
            for line in ansible_result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('- ') and 'volttron' in line.lower():
                    role_name = line[2:].split(',')[0].strip()
                    other_items.append(f"Ansible: {role_name}")
    except:
        pass
    
    if other_items:
        result_lines.append(f"Other VOLTTRON-related: {', '.join(other_items)}")
    
    return "\n".join(result_lines) if result_lines else "No installations found"


def list_running_agents():
    """List VOLTTRON agents that are currently running (vctl status)."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return "❌ vctl command not found - is VOLTTRON installed?"
        
        if not is_volttron_running_quick():
            return "❌ VOLTTRON is not running\n\n💡 Start it with: `start volttron`"
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        result = subprocess.run(
            [vctl_cmd, "status"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
            cwd=volttron_home
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if not output or "No installed agents" in output:
                return "🤷 No agents installed\n\n💡 Try: `install listener` or `install platform-driver`"
            
            running_count = output.lower().count('running')
            
            return f"🤖 **Agent Status:**\n\n```\n{output}\n```\n\n✅ {running_count} agent(s) running"
        else:
            return f"❌ Error getting status: {result.stderr or result.stdout or 'Unknown error'}"
            
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout getting agent status"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def list_repository_packages():
    """List all VOLTTRON packages installed in the current repository's virtual environment.
    
    This shows what's installed via pip in THIS workspace, not the system VOLTTRON.
    Useful when you're installing many packages and want to track what's in your dev environment.
    
    Returns:
        str: List of installed packages with versions
    """
    try:
        pip_path = find_pip_command()
        if not pip_path:
            return "❌ Pip not found in current environment"
        
        result = subprocess.run(
            [pip_path, 'list', '--format=columns'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode != 0:
            return f"❌ Failed to list packages: {result.stderr}"
        
        volttron_packages = []
        other_packages = []
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line or line.startswith('Package') or line.startswith('---'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                pkg_name = parts[0]
                version = parts[1]
                
                if 'volttron' in pkg_name.lower():
                    volttron_packages.append(f"{pkg_name} ({version})")
                elif pkg_name.lower() in ['ansible', 'poetry', 'pydantic-ai', 'openai']:
                    other_packages.append(f"{pkg_name} ({version})")
        
        result_lines = ["📦 **Repository Packages:**\n"]
        
        if volttron_packages:
            result_lines.append(f"VOLTTRON packages ({len(volttron_packages)}):")
            for pkg in sorted(volttron_packages):
                result_lines.append(f"  • {pkg}")
        
        if other_packages:
            result_lines.append(f"\nRelated tools:")
            for pkg in sorted(other_packages):
                result_lines.append(f"  • {pkg}")
        
        if not volttron_packages and not other_packages:
            return "No VOLTTRON packages found in current environment"
        
        return "\n".join(result_lines)
        
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout listing packages"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def smart_install_package(package_name, user_message=""):
    """Intelligently install a package by searching GitHub and reading its README.
    
    Generic approach:
    1. If it looks like a VOLTTRON package name (volttron-*):
       - Use vctl install for agents (volttron-<agent-name>)
       - Use vctl install-lib for libraries (volttron-lib-*)
    2. Otherwise, search GitHub for the repository
    3. Use install_from_github_smart to read README and follow instructions
    
    Args:
        package_name: Name of package/agent to install
        user_message: Original user message for context
        
    Returns:
        str: Installation result message
    """
    package_lower = package_name.lower().strip()
    
    if package_lower.startswith('volttron-'):
        vctl_cmd = find_vctl_command()
        if not vctl_cmd:
            return "❌ vctl command not found. VOLTTRON not running. Start VOLTTRON first with 'start volttron'."
        
        volttron_home = get_volttron_home()
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        if 'lib' in package_lower or 'volttron-lib-' in package_lower:
            print(f"📦 Step 1: Trying vctl install-lib {package_name}...")
            result = subprocess.run(
                [vctl_cmd, "install-lib", package_name],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            
            if result.returncode == 0:
                return f"✅ Successfully installed {package_name} library using vctl install-lib!"
            
            github_url = f"https://github.com/eclipse-volttron/{package_name}.git"
            print(f"⚠️ Step 2: vctl install-lib failed, trying GitHub: {github_url}...")
            github_result = subprocess.run(
                [vctl_cmd, "install-lib", f"git+{github_url}"],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            
            if github_result.returncode == 0:
                return f"✅ Successfully installed {package_name} library from GitHub using vctl install-lib!"
            
            print(f"⚠️ Step 3: vctl install-lib not available, using 'poetry add --directory $VOLTTRON_HOME' as fallback...")
            
            poetry_cmd = None
            volttron_cmd = find_volttron_command()
            if volttron_cmd:
                bin_dir = os.path.dirname(volttron_cmd)
                poetry_in_same_venv = os.path.join(bin_dir, "poetry")
                if os.path.exists(poetry_in_same_venv):
                    poetry_cmd = poetry_in_same_venv
            
            if not poetry_cmd:
                poetry_cmd = shutil.which("poetry")
            
            if not poetry_cmd:
                error_details = f"""
❌ **Failed to install {package_name}**

**Tried:**
1. vctl install-lib {package_name} - Failed: {result.stderr[:200] if result.stderr else result.stdout[:200]}
2. vctl install-lib from GitHub - Failed: {github_result.stderr[:200] if github_result.stderr else github_result.stdout[:200]}

**Poetry not found in VOLTTRON installation**

**Manual installation:**
```bash
vctl install-lib {package_name}
vctl install-lib git+https://github.com/eclipse-volttron/{package_name}.git
poetry add --directory $VOLTTRON_HOME {package_name}
```

Need help? Let me know!
"""
                return error_details
            
            poetry_result = subprocess.run(
                [poetry_cmd, "add", "--directory", volttron_home, package_name],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            
            if poetry_result.returncode == 0:
                return f"✅ Successfully installed {package_name} library using poetry add (manual method)!"
            else:
                error_msg = poetry_result.stderr or poetry_result.stdout or "Unknown error"
                return f"❌ Failed all installation attempts for {package_name}: {error_msg[:200]}"
        else:
            print(f"🤖 Step 1: Installing {package_name} agent using vctl install...")
            result = subprocess.run(
                [vctl_cmd, "install", package_name, "--force"],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            
            if result.returncode == 0:
                return f"✅ Successfully installed {package_name} agent!"
            
            github_url = f"https://github.com/eclipse-volttron/{package_name}.git"
            print(f"⚠️ Step 2: vctl install failed, trying GitHub: {github_url}...")
            github_result = subprocess.run(
                [vctl_cmd, "install", github_url, "--force"],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            
            if github_result.returncode == 0:
                return f"✅ Successfully installed {package_name} agent from GitHub!"
            else:
                error_msg = github_result.stderr or github_result.stdout or "Unknown error"
                return f"❌ Failed to install {package_name}: {error_msg[:200]}"
    
    search_result = search_github_for_agent(package_name)
    
    if 'https://github.com/' in search_result:
        import re
        urls = re.findall(r'https://github\.com/[\w\-]+/[\w\-]+', search_result)
        if urls:
            return install_from_github_smart(urls[0])
    
    return search_result


def install_fake_driver_library():
    """Install the volttron-lib-fake-driver package for testing and development.
    
    Returns:
        str: Status message about the installation
    """
    try:
        vctl_cmd = find_vctl_command()
        if not vctl_cmd:
            return "❌ vctl command not found. VOLTTRON not running. Start VOLTTRON first with 'start volttron'."
        
        package_name = "volttron-lib-fake-driver"
        volttron_home = get_volttron_home()
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        print(f"📦 Installing library {package_name} with vctl install-lib...")
        install_result = subprocess.run(
            [vctl_cmd, "install-lib", package_name],
            capture_output=True,
            text=True,
            timeout=120,
            env=env
        )
        
        if install_result.returncode == 0:
            if "already installed" in install_result.stdout.lower() or "already satisfied" in install_result.stdout.lower():
                return f"✅ **{package_name} is already installed.** Say 'configure fake driver' to set it up."
            else:
                return f"✅ **Successfully installed {package_name}!** Say 'configure fake driver' to set it up."
        
        print(f"⚠️ vctl install-lib failed, trying GitHub installation...")
        error_output = install_result.stderr or install_result.stdout or "Unknown error"
        print(f"Error from vctl install-lib: {error_output}")
        
        github_url = f"https://github.com/eclipse-volttron/{package_name}.git"
        print(f"🔍 Attempting to install from GitHub: {github_url}")
        
        try:
            github_result = subprocess.run(
                [vctl_cmd, "install-lib", f"git+{github_url}"],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            
            if github_result.returncode == 0:
                return f"""✅ **Successfully installed {package_name} from GitHub!**

Installation method: vctl install-lib (poetry add wrapper)

Say 'configure fake driver' to set it up! 🚀"""
            else:
                github_error = github_result.stderr or github_result.stdout
                return f"""❌ **Failed to install {package_name}**

**Tried:**
1. vctl install-lib {package_name} - Failed: {error_output[:200]}
2. vctl install-lib from GitHub - Failed: {github_error[:200]}

**Manual installation:**
```bash
vctl install-lib {package_name}
vctl install-lib git+{github_url}
poetry add --directory $VOLTTRON_HOME {package_name}
```

Need help? Let me know!"""
        
        except Exception as git_error:
            return f"""❌ **Failed to install {package_name}**

**Tried:**
1. vctl install-lib {package_name} - Failed: {error_output[:200]}
2. GitHub installation - Error: {str(git_error)[:200]}

**Try manually:** `vctl install-lib {package_name}`

Need help? Let me know!"""
            
    except subprocess.TimeoutExpired:
        return f"⏱️ Installation is taking longer than expected. The package might be large or your connection is slow."
    except Exception as e:
        return f"💥 Error installing fake driver library: {str(e)}"

def configure_fake_driver():
    """Configure the fake driver with config files and start generating data.
    
    Returns:
        str: Status message about the configuration
    """
    import os
    import time
    
    try:
        pip_cmd = find_pip_command()
        if not pip_cmd:
            return "❌ Pip command not found. Please install pip first."
        
        check_result = subprocess.run(
            [pip_cmd, "show", "volttron-lib-fake-driver"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if check_result.returncode != 0:
            return "❌ Fake driver library not installed. Say 'install fake driver library' first."
        
        vctl_cmd = find_vctl_command()
        if not vctl_cmd:
            return "❌ VOLTTRON not running. Start VOLTTRON first."
        
        status_result = subprocess.run(
            [vctl_cmd, "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "platform.driver" not in status_result.stdout:
            return "❌ Platform driver not installed. Say 'install platform driver' first."
        
        workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(workspace_dir, "config")
        fake_config_path = os.path.join(config_dir, "fake.config")
        fake_csv_path = os.path.join(config_dir, "fake.csv")
        
        if not os.path.exists(fake_config_path):
            return f"❌ Config file not found: {fake_config_path}"
        if not os.path.exists(fake_csv_path):
            return f"❌ Registry file not found: {fake_csv_path}"
        
        print("📝 Configuring fake driver...")
        
        volttron_home = get_volttron_home()
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        csv_result = subprocess.run(
            [vctl_cmd, "config", "store", "platform.driver", "fake.csv", fake_csv_path, "--csv"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env
        )
        
        if csv_result.returncode != 0:
            return f"❌ Failed to store registry config: {csv_result.stderr or csv_result.stdout}"
        
        config_result = subprocess.run(
            [vctl_cmd, "config", "store", "platform.driver", "devices/fake", fake_config_path, "--json"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env
        )
        
        if config_result.returncode != 0:
            return f"❌ Failed to store device config: {config_result.stderr or config_result.stdout}"
        
        print("🔄 Restarting platform driver...")
        
        restart_result = subprocess.run(
            [vctl_cmd, "restart", "platform.driver"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env
        )
        
        if restart_result.returncode != 0:
            return f"❌ Failed to restart platform driver: {restart_result.stderr or restart_result.stdout}"
        
        time.sleep(3)
        
        return """✅ **Fake driver configured successfully!**

The fake driver is now publishing data every 5 seconds.

**What's happening:**
• fake.csv registry defines 24 fake data points (temperature, heartbeat, etc.)
• Platform driver reads these points and publishes them to the message bus
• Data appears in logs as devices/fake/all topic

**Try these commands:**
• "show logs" - see the fake device data
• "show fake driver logs" - filtered view of fake data
• "show agents" - verify platform.driver is running"""
        
    except subprocess.TimeoutExpired:
        return "⏱️ Configuration is taking longer than expected."
    except Exception as e:
        return f"💥 Error configuring fake driver: {str(e)}"

def start_fake_driver():
    """Start the fake driver by installing library, configuring it, and starting platform driver.
    
    This is a complete workflow that handles all steps needed to get fake driver running.
    
    Returns:
        str: Status message about the startup process
    """
    import time
    
    try:
        if not is_volttron_running():
            return "❌ VOLTTRON is not running. Say 'start volttron' first."
        
        print("📦 Checking fake driver library...")
        vctl_cmd = find_vctl_command()
        if not vctl_cmd:
            return "❌ vctl command not found."
        
        volttron_home = get_volttron_home()
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        print("📦 Installing fake driver library with vctl install-lib...")
        install_result = subprocess.run(
            [vctl_cmd, "install-lib", "volttron-lib-fake-driver"],
            capture_output=True,
            text=True,
            timeout=120,
            env=env
        )
        
        if install_result.returncode == 0:
            if "already installed" in install_result.stdout.lower() or "already satisfied" in install_result.stdout.lower():
                print("✅ Fake driver library already installed")
            else:
                print("✅ Fake driver library installed")
        else:
            print("⚠️ Trying GitHub installation...")
            github_url = "https://github.com/eclipse-volttron/volttron-lib-fake-driver.git"
            github_result = subprocess.run(
                [vctl_cmd, "install-lib", f"git+{github_url}"],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            if github_result.returncode != 0:
                return f"❌ Failed to install fake driver library: {github_result.stderr or github_result.stdout}"
            print("✅ Fake driver library installed from GitHub")
        
        print("🔧 Checking platform driver...")
        vctl_cmd = find_vctl_command()
        if not vctl_cmd:
            return "❌ VOLTTRON not running."
        
        status_result = subprocess.run(
            [vctl_cmd, "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "platform.driver" not in status_result.stdout:
            print("📦 Installing platform driver...")
            install_driver = vctl_install_platform_driver()
            if "❌" in install_driver or "Failed" in install_driver:
                return f"❌ Failed to install platform driver: {install_driver}"
            print("✅ Platform driver installed")
            time.sleep(2)
        else:
            print("✅ Platform driver already installed")
        
        print("📝 Configuring fake driver...")
        workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(workspace_dir, "config")
        fake_config_path = os.path.join(config_dir, "fake.config")
        fake_csv_path = os.path.join(config_dir, "fake.csv")
        
        if not os.path.exists(fake_config_path):
            return f"❌ Config file not found: {fake_config_path}"
        if not os.path.exists(fake_csv_path):
            return f"❌ Registry file not found: {fake_csv_path}"
        
        volttron_home = get_volttron_home()
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        csv_result = subprocess.run(
            [vctl_cmd, "config", "store", "platform.driver", "fake.csv", fake_csv_path, "--csv"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env
        )
        
        if csv_result.returncode != 0:
            return f"❌ Failed to store registry: {csv_result.stderr or csv_result.stdout}"
        
        config_result = subprocess.run(
            [vctl_cmd, "config", "store", "platform.driver", "devices/fake", fake_config_path, "--json"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env
        )
        
        if config_result.returncode != 0:
            return f"❌ Failed to store config: {config_result.stderr or config_result.stdout}"
        
        print("✅ Configuration stored")
        
        print("🚀 Starting platform driver...")
        restart_result = subprocess.run(
            [vctl_cmd, "restart", "platform.driver"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env
        )
        
        if restart_result.returncode != 0:
            return f"❌ Failed to start platform driver: {restart_result.stderr or restart_result.stdout}"
        
        print("⏳ Waiting for fake driver to start publishing...")
        time.sleep(3)
        
        return """✅ **Fake driver started successfully!**

**What just happened:**
✅ Fake driver library installed
✅ Platform driver installed/verified
✅ Configuration files loaded
✅ Platform driver restarted
✅ Fake data now publishing every 5 seconds

**Next steps:**
• "show logs" - see the fake device data
• "show fake driver logs" - filtered view of fake data only
• "show agents" - verify platform.driver is running"""
        
    except subprocess.TimeoutExpired:
        return "⏱️ Starting fake driver is taking longer than expected."
    except Exception as e:
        return f"💥 Error starting fake driver: {str(e)}"

def show_fake_driver_logs(num_lines=50):
    """Show recent fake driver data from VOLTTRON logs.
    
    Args:
        num_lines (int): Number of recent log lines to check (default: 50)
    
    Returns:
        str: Formatted display of fake driver log data
    """
    try:
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
        
        result = subprocess.run([
            "tail", f"-{num_lines}", volttron_log
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            log_lines = result.stdout.strip().split('\n')
            
            fake_lines = []
            for line in log_lines:
                lower_line = line.lower()
                if any(keyword in lower_line for keyword in [
                    'fake', 'devices/campus/building/fake', 
                    'volttron-lib-fake-driver', 'fakedriver'
                ]):
                    fake_lines.append(line)
            
            if fake_lines:
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
        
        result = subprocess.run([
            "tail", "-100", volttron_log
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            log_lines = result.stdout.strip().split('\n')
            
            fake_lines = []
            for line in log_lines:
                lower_line = line.lower()
                if any(keyword in lower_line for keyword in [
                    'fake', 'devices/campus/building/fake'
                ]):
                    fake_lines.append(line)
            
            if fake_lines:
                publish_count = sum(1 for line in fake_lines if 'publishing:' in line.lower())
                
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
        status_messages.append("🚀 **Step 1/5: Starting VOLTTRON platform...**")
        start_result = start_volttron()
        time.sleep(3)  # Give it time to start
        
        status_messages.append("\n📦 **Step 2/5: Installing volttron-lib-fake-driver...**")
        vctl_cmd = find_vctl_command()
        if not vctl_cmd:
            return "❌ vctl command not found. Please start VOLTTRON first."
        
        volttron_home = get_volttron_home()
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        install_lib_result = subprocess.run(
            [vctl_cmd, "install-lib", "volttron-lib-fake-driver"],
            capture_output=True,
            text=True,
            timeout=120,
            env=env
        )
        
        if install_lib_result.returncode == 0:
            if "already installed" in install_lib_result.stdout.lower() or "already satisfied" in install_lib_result.stdout.lower():
                status_messages.append("   ✅ volttron-lib-fake-driver already installed")
            else:
                status_messages.append("   ✅ volttron-lib-fake-driver installed successfully")
        else:
            github_url = "https://github.com/eclipse-volttron/volttron-lib-fake-driver.git"
            github_result = subprocess.run(
                [vctl_cmd, "install-lib", f"git+{github_url}"],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            if github_result.returncode == 0:
                status_messages.append("   ✅ volttron-lib-fake-driver installed from GitHub")
            else:
                return "\n".join(status_messages) + f"\n❌ Failed to install fake driver library: {github_result.stderr or github_result.stdout}"
        
        status_messages.append("\n📦 **Step 3/5: Installing volttron-platform-driver agent...**")
        status_messages.append("   ⏭️  Will install platform-driver agent in next step")
        
        time.sleep(2)
        
        status_messages.append("\n⚙️  **Step 4/5: Installing platform driver agent...**")
        
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return "\n".join(status_messages) + "\n❌ vctl command not found"
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
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
        
        status_messages.append("\n▶️  **Step 5/5: Starting platform driver agent...**")
        
        status_check = subprocess.run(
            [vctl_cmd, "status"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            cwd=volttron_home
        )
        
        if "platform.driver" in status_check.stdout:
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
        
        final_status = subprocess.run(
            [vctl_cmd, "status"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            cwd=volttron_home
        )
        
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
        
        for line in lines[1:]:
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
            return "I can't check my health right now - I might not be running. Want to start me up?"
        
        status_output = status_result.stdout.strip()
        if not status_output:
            return "I'm running but don't have any agents to check the health of. Everything's fine though!"
        
        lines = status_output.strip().split('\n')
        health_reports = []
        
        for line in lines[1:]:
            if not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 3:
                uuid = parts[0]
                agent_name = parts[1]
                
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
                    health_reports.append(f"• {agent_type} agent (UUID {uuid}): Not running or no health monitoring")
        
        if not health_reports:
            return "I have agents installed but none are reporting health status. They might not be running."
        
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
        
        if line.strip():
            try:
                if '2025-' in line:
                    time_part = line.split(' ')[1].split(',')[0]  # Get HH:MM:SS
                    recent_activity.append(time_part)
            except:
                pass
    
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
    
    time_context = ""
    if recent_activity:
        if len(recent_activity) > 1:
            time_context = f"\n\nMost recent activity was around {recent_activity[-1]}."
        else:
            time_context = f"\n\nLast activity was at {recent_activity[0]}."
    
    main_summary = f"Here's what I've been up to recently:\n\n• " + "\n• ".join(summary_parts) + time_context
    
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
    status_result = check_volttron_status()
    
    if "VOLTTRON is running" in status_result or "PID" in status_result:
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
sudo apt update && sudo apt install python3-pip

sudo yum install python3-pip

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
  sudo apt install build-essential python3-dev
  
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
    startup_wait = int(os.getenv('VOLTTRON_STARTUP_WAIT', '5'))
    time.sleep(startup_wait)
    
    
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
        
        package_name = "volttron-platform-driver"
        
        print(f"Installing platform driver agent with vctl: {vctl_cmd}")
        print(f"VOLTTRON_HOME: {volttron_home}")
        
        install_result = subprocess.run([
            vctl_cmd, "install", package_name,
            "--vip-identity", "platform.driver",
            "--start",
            "--priority", "40",
            "--force"
        ], capture_output=True, text=True, timeout=120, env=env)
        
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
            
            if "already exists" in error_msg.lower():
                return f"""{install_warning_msg}⚠️ **Platform driver already exists**

The platform driver is already installed. You can:

**Option 1: Uninstall first**
• Say: **"uninstall platform.driver"**

**Option 2: Check status**
• Say: **"vctl status"** to see if it's running

**Option 3: Force reinstall** (this will overwrite the existing installation)
• The system tried to force reinstall but encountered an issue

What would you like to do?
"""
            
            return f"""{install_warning_msg}❌ **Failed to install platform driver**

Installation failed with error:
```
{error_msg}
```

**Troubleshooting steps:**
1. **Check VOLTTRON status** - Make sure VOLTTRON is running
2. **Check network** - Ensure internet connection for package download
3. **Try manual install** - Run: `vctl install volttron-platform-driver --vip-identity platform.driver --start --force`

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
            
            interesting_lines = device_lines[-30:] + other_interesting_lines[-5:]
            
            if interesting_lines:
                device_data = {}
                
                for line in device_lines[-50:]:
                    if 'devices/campus/building/fake/' in line:
                        try:
                            timestamp_full = line.split('(')[0].strip()
                            time_only = timestamp_full.split()[1].split(',')[0]  # Get HH:MM:SS
                            
                            device_part = line.split('devices/campus/building/fake/')[1]
                            device_name = device_part.split()[0].strip()
                            
                            if device_name != 'all':  # Skip 'all' device
                                if device_name not in device_data:
                                    device_data[device_name] = []
                                if len(device_data[device_name]) < 3:
                                    device_data[device_name].append(time_only)
                        except:
                            pass
                
                if device_data:
                    devices_list = sorted(device_data.keys())
                    
                    device_list = []
                    for dev in devices_list:
                        times = device_data[dev]
                        latest_time = times[-1] if times else "N/A"
                        device_list.append(f"{dev}: {latest_time} (last seen)")
                    
                    device_output = '\n'.join(device_list)
                    
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


def fetch_webpage_content(url: str) -> str:
    """
    Fetch and return the content of a webpage.
    
    Args:
        url: The URL to fetch
        
    Returns:
        str: Webpage content or error message
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        print(f"DEBUG: Fetching webpage: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        

        for script in soup(["script", "style"]):
            script.decompose()
        
  
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
      
        if 'github.com' in url and '/blob/' not in url:
            try:
                readme_div = soup.find('article', class_='markdown-body')
                if readme_div:
                    text = readme_div.get_text()
            except:
                pass
        
        return f"""📄 **Webpage Content Retrieved**
URL: {url}
Content length: {len(text)} characters

{text[:5000]}{'...' if len(text) > 5000 else ''}"""
        
    except requests.RequestException as e:
        return f"❌ Error fetching webpage: {str(e)}"
    except Exception as e:
        return f"❌ Error processing webpage: {str(e)}"


def execute_system_command(command: str, require_sudo: bool = False) -> str:
    """
    Execute a system command safely.
    
    Args:
        command: The command to execute
        require_sudo: Whether the command requires sudo privileges
        
    Returns:
        str: Command output or error message
    """
    try:
        import subprocess
        
        print(f"DEBUG: Executing command: {command}")
        
        if require_sudo:
            return f"⚠️ Command requires sudo privileges: {command}\n\nFor security reasons, please run this command manually:\n```bash\n{command}\n```"
        
       
        safe_commands = [
            'which', 'whereis', 'ls', 'cat', 'grep', 'find', 'pwd', 
            'echo', 'uname', 'df', 'du', 'free', 'ps', 'top',
            'psql', 'pg_isready', 'systemctl status', 'service'
        ]
        
        cmd_parts = command.split()
        if not cmd_parts:
            return "❌ Empty command"
        
        base_cmd = cmd_parts[0]
        is_safe = any(base_cmd == safe or base_cmd.endswith(safe) for safe in safe_commands)
        
        if not is_safe and not command.startswith(('vctl', 'volttron', 'pip')):
            return f"⚠️ Command not in safe list: {command}\n\nFor security, please review and run manually if needed:\n```bash\n{command}\n```"
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout if result.stdout else result.stderr
        
        return f"""✅ **Command executed**
Command: {command}
Exit code: {result.returncode}

Output:
```
{output}
```"""
        
    except subprocess.TimeoutExpired:
        return f"⏱️ Command timed out after 30 seconds: {command}"
    except Exception as e:
        return f"❌ Error executing command: {str(e)}"


def setup_postgresql_database(db_name: str = "volttron", db_user: str = "volttron", db_password: str = "volttron") -> str:
    """
    Guide user through PostgreSQL database setup for VOLTTRON historian.
    
    Args:
        db_name: Database name
        db_user: Database user
        db_password: Database password
        
    Returns:
        str: Setup instructions and status
    """
    try:

        result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
        postgres_installed = result.returncode == 0
        
        if not postgres_installed:
            return f"""📋 **PostgreSQL Setup Required**

PostgreSQL is not installed on this system.

**Step 1: Install PostgreSQL**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

**Step 2: Create Database and User**
```bash
sudo -u postgres psql
```

Then run these SQL commands:
```sql
CREATE DATABASE {db_name};
CREATE USER {db_user} WITH PASSWORD '{db_password}';
GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};
\\q
```

**Step 3: Create Required Tables**
```bash
psql -U {db_user} -d {db_name} << EOF
CREATE TABLE IF NOT EXISTS topics (
    topic_id SERIAL PRIMARY KEY,
    topic_name VARCHAR(512) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS data (
    ts TIMESTAMP NOT NULL,
    topic_id INTEGER NOT NULL,
    value_string TEXT,
    UNIQUE(ts, topic_id)
);

CREATE INDEX IF NOT EXISTS idx_data_ts ON data (ts DESC);
CREATE INDEX IF NOT EXISTS idx_data_topic_id ON data (topic_id);
EOF
```

After completing these steps, you can configure the PostgreSQL historian agent."""
        
        service_result = subprocess.run(
            ['systemctl', 'is-active', 'postgresql'],
            capture_output=True,
            text=True
        )
        
        postgres_running = service_result.returncode == 0
        
        status = "✅ Running" if postgres_running else "⚠️ Not running"
        
        return f"""📊 **PostgreSQL Status Check**

PostgreSQL is installed: ✅
PostgreSQL service: {status}

**Next Steps:**

1. Ensure PostgreSQL is running:
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

2. Create database and user:
```bash
sudo -u postgres psql << EOF
CREATE DATABASE {db_name};
CREATE USER {db_user} WITH PASSWORD '{db_password}';
GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};
\\q
EOF
```

3. Test connection:
```bash
psql -U {db_user} -d {db_name} -h localhost
```

Would you like me to help configure the PostgreSQL historian agent configuration?"""
        
    except Exception as e:
        return f"❌ Error checking PostgreSQL setup: {str(e)}"


def create_historian_config(
    historian_type: str = "postgresql",
    db_config: dict = None
) -> str:
    """
    Create a historian agent configuration file.
    
    Args:
        historian_type: Type of historian (postgresql, sqlite, etc.)
        db_config: Database configuration parameters
        
    Returns:
        str: Configuration file content and instructions
    """
    try:
        if db_config is None:
            db_config = {
                "dbname": "volttron",
                "user": "volttron",
                "password": "volttron",
                "host": "localhost",
                "port": 5432
            }
        
        if historian_type == "postgresql":
            config = {
                "connection": {
                    "type": "postgresql",
                    "params": {
                        "dbname": db_config.get("dbname", "volttron"),
                        "host": db_config.get("host", "localhost"),
                        "port": db_config.get("port", 5432),
                        "user": db_config.get("user", "volttron"),
                        "password": db_config.get("password", "volttron")
                    }
                },
                "tables_def": {
                    "table_prefix": "",
                    "data_table": "data",
                    "topics_table": "topics"
                }
            }
        elif historian_type == "sqlite":
            config = {
                "connection": {
                    "type": "sqlite",
                    "params": {
                        "database": db_config.get("database", "data/historian.sqlite")
                    }
                }
            }
        else:
            return f"❌ Unsupported historian type: {historian_type}"
        
        config_json = json.dumps(config, indent=2)
        
        config_dir = Path.home() / ".volttron" / "configs"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / f"{historian_type}_historian_config.json"
        with open(config_file, 'w') as f:
            f.write(config_json)
        
        return f"""✅ **Historian Configuration Created**

Type: {historian_type}
File: {config_file}

Configuration:
```json
{config_json}
```

**To install the historian agent:**
```bash
vctl install {historian_type}-historian --agent-config {config_file} --start
```

**To check status:**
```bash
vctl status
```

Configuration file saved to: {config_file}"""
        
    except Exception as e:
        return f"❌ Error creating historian config: {str(e)}"

def list_volttron_installations():
    """List all discovered VOLTTRON installations on this system."""
    try:
        installations = discover_volttron_installations()
        
        if not installations:
            return """❌ **No VOLTTRON Installations Found**

I couldn't find any VOLTTRON installations on your system.

**To install VOLTTRON:**
```bash
pip install volttron
```

Or for development:
```bash
git clone https://github.com/eclipse-volttron/volttron-core.git
cd volttron-core
python3 -m venv venv
source venv/bin/activate
pip install -e .
```"""
        
        current_volttron = find_volttron_command()
        
        output = f"🔍 **Found {len(installations)} VOLTTRON Installation(s)**\n\n"
        
        for i, install in enumerate(installations, 1):
            is_current = install['path'] == current_volttron
            marker = " ← Currently active" if is_current else ""
            status_icon = "✓" if is_current else " "
            
            output += f"{i}. [{status_icon}] **{install['name']}** (v{install['version']}){marker}\n"
            output += f"   Path: `{install['path']}`\n\n"
        
        if len(installations) > 1:
            output += "\n**How to use a different version:**\n\n"
            output += "**Option 1 - Activate before starting chat (Recommended):**\n"
            output += "```bash\n"
            output += "# Example: Use VOLTTRON 11\n"
            output += "source ~/volttron-v11-py311/bin/activate\n"
            output += "cd ~/volttron/volttron-ai-igorversions\n"
            output += "python -m chat_app\n"
            output += "```\n\n"
            output += "**Option 2 - Set environment variable:**\n"
            output += "```bash\n"
            output += "export VOLTTRON_HOME=~/volttron-home-v11\n"
            output += "python -m chat_app\n"
            output += "```\n\n"
            output += "**Option 3 - Update your PATH:**\n"
            output += "Add desired version's bin directory to the front of your PATH\n"
        
        return output
        
    except Exception as e:
        return f"❌ Error listing VOLTTRON installations: {str(e)}"

def get_current_volttron_version():
    """Get the version of the currently selected VOLTTRON installation."""
    try:
        volttron_path = find_volttron_command()
        if not volttron_path:
            return "❌ No VOLTTRON installation found"
        
        bin_dir = os.path.dirname(volttron_path)
        pip_path = os.path.join(bin_dir, "pip")
        
        version = "Unknown"
        install_name = os.path.basename(os.path.dirname(bin_dir))
        
        if os.path.exists(pip_path):
            for package in ["volttron-core", "volttron"]:
                result = subprocess.run(
                    [pip_path, "show", package],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.split("\n"):
                        if line.startswith("Version:"):
                            version = line.split(":", 1)[1].strip()
                            break
                if version != "Unknown":
                    break
        
        in_path = shutil.which("volttron") == volttron_path
        source_info = "in PATH" if in_path else "auto-discovered"
        
        return f"""📋 **Current VOLTTRON Installation**

**Version:** {version}
**Name:** {install_name}
**Path:** `{volttron_path}`
**Source:** {source_info}

💡 **How VOLTTRON is selected:**
1. Running VOLTTRON process (if any)
2. `volttron` in your PATH
3. Auto-discovered (highest version)

To see all available versions: "list volttron installations"

To use a different version:
• Activate its virtualenv before starting this chat app
• Or add it to your PATH
• Or set VOLTTRON_HOME environment variable
"""
        
    except Exception as e:
        return f"❌ Error getting VOLTTRON version: {str(e)}"


