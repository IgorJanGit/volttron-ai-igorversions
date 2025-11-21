"""SQLite Historian installation and configuration functions."""

import os
import subprocess
import tempfile
import yaml
import json


def install_sqlite_historian(config_path=None):
    """
    Install and configure VOLTTRON SQLite historian agent.
    
    Args:
        config_path (str, optional): Path to custom configuration file. 
                                     If None, creates default config.
    
    Returns:
        str: Installation result message with structured data
    """
    from chat_app.volttron_commands import (
        find_vctl_command, 
        get_volttron_home,
        wait_for_volttron_ready
    )
    
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return """SQLite historian installation failed.
Status: vctl command not found
Recommendation: Install VOLTTRON first"""
        
        is_ready, wait_message = wait_for_volttron_ready(max_wait_seconds=15)
        if not is_ready:
            return f"""SQLite historian installation failed.
Status: VOLTTRON not ready
Message: {wait_message}
Recommendation: Start VOLTTRON first"""
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        if config_path is None:
            config_path = create_default_sqlite_config(volttron_home)
        
        install_args = [
            vctl_cmd, "install", 
            "volttron-sqlite-historian",
            "--agent-config", config_path,
            "--start"
        ]
        
        result = subprocess.run(
            install_args,
            capture_output=True, 
            text=True, 
            timeout=60, 
            env=env
        )
        
        if result.returncode == 0:
            return f"✅ SQLite historian installed and started successfully"
        else:
            # Extract short error message
            error_msg = "Unknown error"
            if result.stderr:
                error_lines = [line.strip() for line in result.stderr.split('\n') if line.strip()]
                if error_lines:
                    error_msg = error_lines[0][:100]
            return f"❌ SQLite historian installation failed: {error_msg}"
            
    except Exception as e:
        return f"❌ SQLite historian installation error: {type(e).__name__} - {str(e)[:100]}"


def create_default_sqlite_config(volttron_home):
    """
    Create a default SQLite historian configuration file.
    
    Args:
        volttron_home (str): Path to VOLTTRON_HOME directory
    
    Returns:
        str: Path to created configuration file
    """
    config = {
        "connection": {
            "type": "sqlite",
            "params": {
                "database": "data/historian.sqlite"
            }
        },
        "tables_def": {
            "table_prefix": "",
            "data_table": "data",
            "topics_table": "topics"
        }
    }
    
    config_dir = os.path.join(volttron_home, "configs")
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "sqlite-historian.config")
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path


def create_sqlite_historian_config(database_path=None, table_prefix="", 
                                   data_table="data", topics_table="topics"):
    """
    Create a custom SQLite historian configuration.
    
    Args:
        database_path (str, optional): Path to SQLite database file. 
                                      Defaults to "data/historian.sqlite"
        table_prefix (str): Prefix for database tables. Default: ""
        data_table (str): Name of data table. Default: "data"
        topics_table (str): Name of topics table. Default: "topics"
    
    Returns:
        str: Path to created configuration file
    """
    from chat_app.volttron_commands import get_volttron_home
    
    volttron_home = get_volttron_home()
    
    if database_path is None:
        database_path = "data/historian.sqlite"
    
    config = {
        "connection": {
            "type": "sqlite",
            "params": {
                "database": database_path
            }
        },
        "tables_def": {
            "table_prefix": table_prefix,
            "data_table": data_table,
            "topics_table": topics_table
        }
    }
    
    config_dir = os.path.join(volttron_home, "configs")
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "sqlite-historian-custom.config")
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path


def check_sqlite_historian_status():
    """
    Check if SQLite historian is installed and running.
    
    Returns:
        str: Status information about SQLite historian
    """
    from chat_app.volttron_commands import find_vctl_command, get_volttron_home
    
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return """SQLite historian status check failed.
Status: vctl command not found"""
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        result = subprocess.run(
            [vctl_cmd, "status"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        
        full_output = result.stderr + "\n" + result.stdout
        
        if "sqlite" in full_output.lower() or "historian" in full_output.lower():
            return f"""SQLite historian status:

{full_output}

VOLTTRON_HOME: {volttron_home}
Command: {vctl_cmd} status
"""
        else:
            return f"""SQLite historian status:

Status: Not found in agent list
Installed agents:
{full_output}

Recommendation: Install with 'install sqlite historian'
"""
            
    except Exception as e:
        return f"""SQLite historian status check error.

Error type: {type(e).__name__}
Error details: {str(e)}
"""
