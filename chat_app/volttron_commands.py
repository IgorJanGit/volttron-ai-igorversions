import subprocess
import os

def get_volttron_env_path():
    """Get the path to the VOLTTRON virtual environment."""
    # Check if VIRTUAL_ENV is set (when running in activated venv)
    venv_path = os.getenv("VIRTUAL_ENV")
    if venv_path:
        return venv_path
    
    # Fallback to common VOLTTRON env location
    return "/home/riley/WORK/AI/volttron-ai/env" # TODO remove hardcode

def get_volttron_home():
    """Get the VOLTTRON_HOME directory."""
    # Check if VOLTTRON_HOME is set in environment
    volttron_home = os.getenv("VOLTTRON_HOME")
    if volttron_home:
        return volttron_home
    
    # Fallback to detected location
    return "/home/riley/WORK/AI/volttron-ai/volttron_home_new" # TODO remove hardcode

def start_volttron():
    """Start volttron in the background using the correct virtual environment."""
    try:
        venv_path = get_volttron_env_path()
        volttron_home = get_volttron_home()
        volttron_cmd = os.path.join(venv_path, "bin", "volttron")
        
        # Check if the volttron command exists
        if not os.path.exists(volttron_cmd):
            return f"Error: volttron command not found at {volttron_cmd}"
        
        # Set environment variables for VOLTTRON
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Start volttron in the background with output redirected to /dev/null
        # Using the exact command that works: volttron -vv -l volttron.log &>/dev/null &
        process = subprocess.Popen(
            [volttron_cmd, "-vv", "-l", "volttron.log"], 
            env=env,
            cwd=volttron_home,  # Run from VOLTTRON_HOME directory
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return f"VOLTTRON started with PID {process.pid} (VOLTTRON_HOME: {volttron_home})"
    except Exception as e:
        return f"Error starting VOLTTRON: {str(e)}"

def stop_volttron():
    """Stop volttron platform using the correct virtual environment."""
    try:
        venv_path = get_volttron_env_path()
        volttron_home = get_volttron_home()
        vctl_cmd = os.path.join(venv_path, "bin", "vctl")
        
        # Check if the vctl command exists
        if not os.path.exists(vctl_cmd):
            return f"Error: vctl command not found at {vctl_cmd}"
        
        # Set environment variables for VOLTTRON
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Stop volttron platform using the exact command that works: vctl shutdown
        result = subprocess.run(
            [vctl_cmd, "shutdown"], 
            capture_output=True, 
            text=True,
            env=env,
            cwd=volttron_home,
            timeout=30
        )
        
        if result.returncode == 0:
            return "VOLTTRON stopped successfully"
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return f"VOLTTRON stop failed: {error_msg}"
    except subprocess.TimeoutExpired:
        return "VOLTTRON stop command timed out after 30 seconds"
    except Exception as e:
        return f"Error stopping VOLTTRON: {str(e)}"

def check_volttron_status():
    """Check VOLTTRON status and show recent log entries."""
    try:
        venv_path = get_volttron_env_path()
        volttron_home = get_volttron_home()
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # Check if VOLTTRON processes are running
        try:
            ps_result = subprocess.run(
                ["pgrep", "-f", "volttron"], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            
            if ps_result.returncode == 0 and ps_result.stdout.strip():
                pids = ps_result.stdout.strip().split('\n')
                status_msg = f"VOLTTRON is running (PIDs: {', '.join(pids)})"
            else:
                status_msg = "VOLTTRON is not running"
        except Exception:
            status_msg = "Could not determine VOLTTRON status"
        
        # Try to get detailed status with vctl if available
        vctl_cmd = os.path.join(venv_path, "bin", "vctl")
        if os.path.exists(vctl_cmd):
            try:
                result = subprocess.run(
                    [vctl_cmd, "status"], 
                    capture_output=True, 
                    text=True,
                    env=env,
                    cwd=volttron_home,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    status_msg += f"\n\nDetailed status:\n{result.stdout}"
                else:
                    # Just return the basic status
                    pass
            except Exception:
                # vctl failed, just return basic status
                pass
        
        # Add recent log info
        log_info = read_volttron_log(5)
        if log_info and "No log file found" not in log_info:
            status_msg += f"\n\nRecent logs:\n{log_info}"
        
        return status_msg
        
    except Exception as e:
        return f"Error checking VOLTTRON status: {str(e)}"

def read_volttron_log(num_lines=10):
    """Read the last N lines from the VOLTTRON log file."""
    try:
        volttron_home = get_volttron_home()
        log_file_path = os.path.join(volttron_home, "volttron.log")
        
        if not os.path.exists(log_file_path):
            return "No log file found"
        
        # Read last N lines
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-num_lines:] if len(lines) >= num_lines else lines
            return ''.join(recent_lines).strip()
    except Exception as e:
        return f"Error reading log: {str(e)}"