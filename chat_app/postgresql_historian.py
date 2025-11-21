"""PostgreSQL Historian installation and configuration functions."""

import os
import subprocess
import json


def install_postgresql_historian(config_path=None, dbname="volttron", 
                                 host=None, port=5432, user=None, 
                                 password=None, timescale=False):
    """
    Install and configure VOLTTRON PostgreSQL historian agent.
    
    Args:
        config_path (str, optional): Path to custom configuration file
        dbname (str): Database name. Default: "volttron"
        host (str, optional): Database host. If None, uses Unix socket
        port (int): Database port. Default: 5432
        user (str, optional): Database user
        password (str, optional): Database password
        timescale (bool): Enable TimescaleDB support. Default: False
    
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
            return """PostgreSQL historian installation failed.
Status: vctl command not found
Recommendation: Install VOLTTRON first"""
        
        is_ready, wait_message = wait_for_volttron_ready(max_wait_seconds=15)
        if not is_ready:
            return f"""PostgreSQL historian installation failed.
Status: VOLTTRON not ready
Message: {wait_message}
Recommendation: Start VOLTTRON first"""
        
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        if config_path is None:
            config_path = create_default_postgresql_config(
                volttron_home, dbname, host, port, user, password, timescale
            )
        
        install_args = [
            vctl_cmd, "install", 
            "volttron-postgresql-historian",
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
            db_info = f"{dbname}@{host}:{port}" if host else f"{dbname} (local)"
            return f"✅ PostgreSQL historian installed and started successfully (DB: {db_info})"
        else:
            # Extract short error message
            error_msg = "Unknown error"
            if result.stderr:
                error_lines = [line.strip() for line in result.stderr.split('\n') if line.strip()]
                if error_lines:
                    error_msg = error_lines[0][:100]
            return f"❌ PostgreSQL historian installation failed: {error_msg}"
            
    except Exception as e:
        return f"❌ PostgreSQL historian installation error: {type(e).__name__} - {str(e)[:100]}"


def create_default_postgresql_config(volttron_home, dbname="volttron", 
                                     host=None, port=5432, user=None, 
                                     password=None, timescale=False):
    """
    Create a default PostgreSQL historian configuration file.
    
    Args:
        volttron_home (str): Path to VOLTTRON_HOME directory
        dbname (str): Database name
        host (str, optional): Database host
        port (int): Database port
        user (str, optional): Database user
        password (str, optional): Database password
        timescale (bool): Enable TimescaleDB support
    
    Returns:
        str: Path to created configuration file
    """
    params = {"dbname": dbname}
    
    if host:
        params["host"] = host
        params["port"] = port
    
    if user:
        params["user"] = user
    
    if password:
        params["password"] = password
    
    if timescale:
        params["timescale_dialect"] = True
    
    config = {
        "connection": {
            "type": "postgresql",
            "params": params
        },
        "tables_def": {
            "table_prefix": "",
            "data_table": "data",
            "topics_table": "topics"
        }
    }
    
    config_dir = os.path.join(volttron_home, "configs")
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "postgresql-historian.config")
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path


def create_postgresql_historian_config(dbname="volttron", host="localhost", 
                                       port=5432, user="volttron", password=None,
                                       table_prefix="", data_table="data", 
                                       topics_table="topics", timescale=False):
    """
    Create a custom PostgreSQL historian configuration.
    
    Args:
        dbname (str): Database name. Default: "volttron"
        host (str): Database host. Default: "localhost"
        port (int): Database port. Default: 5432
        user (str): Database user. Default: "volttron"
        password (str, optional): Database password
        table_prefix (str): Prefix for database tables. Default: ""
        data_table (str): Name of data table. Default: "data"
        topics_table (str): Name of topics table. Default: "topics"
        timescale (bool): Enable TimescaleDB support. Default: False
    
    Returns:
        str: Path to created configuration file
    """
    from chat_app.volttron_commands import get_volttron_home
    
    volttron_home = get_volttron_home()
    
    params = {
        "dbname": dbname,
        "host": host,
        "port": port,
        "user": user
    }
    
    if password:
        params["password"] = password
    
    if timescale:
        params["timescale_dialect"] = True
    
    config = {
        "connection": {
            "type": "postgresql",
            "params": params
        },
        "tables_def": {
            "table_prefix": table_prefix,
            "data_table": data_table,
            "topics_table": topics_table
        }
    }
    
    config_dir = os.path.join(volttron_home, "configs")
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "postgresql-historian-custom.config")
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path


def check_postgresql_historian_status():
    """
    Check if PostgreSQL historian is installed and running.
    
    Returns:
        str: Status information about PostgreSQL historian
    """
    from chat_app.volttron_commands import find_vctl_command, get_volttron_home
    
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return """PostgreSQL historian status check failed.
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
        
        if "postgresql" in full_output.lower() or "historian" in full_output.lower():
            return f"""PostgreSQL historian status:

{full_output}

VOLTTRON_HOME: {volttron_home}
Command: {vctl_cmd} status
"""
        else:
            return f"""PostgreSQL historian status:

Status: Not found in agent list
Installed agents:
{full_output}

Recommendation: Install with 'install postgresql historian'
"""
            
    except Exception as e:
        return f"""PostgreSQL historian status check error.

Error type: {type(e).__name__}
Error details: {str(e)}
"""


def get_postgresql_setup_instructions():
    """
    Get detailed setup instructions for PostgreSQL historian.
    
    Returns:
        str: Setup instructions and SQL commands
    """
    return """PostgreSQL Historian Setup Instructions

Prerequisites:
- Python >= 3.10
- PostgreSQL database running
- psycopg2 library: pip install psycopg2-binary

Database Setup (run as database admin):

1. Create Database:
   CREATE DATABASE volttron;

2. Create TOPICS table:
   CREATE TABLE IF NOT EXISTS topics (
       topic_id SERIAL PRIMARY KEY NOT NULL,
       topic_name VARCHAR(512) NOT NULL,
       metadata TEXT,
       UNIQUE (topic_name)
   );

3. Create DATA table:
   CREATE TABLE IF NOT EXISTS data (
       ts TIMESTAMP NOT NULL,
       topic_id INTEGER NOT NULL,
       value_string TEXT NOT NULL,
       UNIQUE (topic_id, ts)
   );

4. Optional - TimescaleDB Hypertable:
   SELECT create_hypertable(data, 'ts', if_not_exists => true);

5. Create Index (if using hypertables):
   CREATE INDEX IF NOT EXISTS idx_data ON data (topic_id, ts);

   Or (if not using hypertables):
   CREATE INDEX IF NOT EXISTS idx_data ON data (ts ASC);

6. Create User and Grant Permissions:
   CREATE USER volttron WITH ENCRYPTED PASSWORD 'your_password';
   GRANT SELECT, INSERT, UPDATE ON DATABASE volttron TO volttron;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO volttron;
   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO volttron;

Installation:
1. Install dependencies: pip install psycopg2-binary
2. Configure database connection
3. Install agent: install postgresql historian

Configuration Options:
- Local database (Unix socket): Only specify dbname
- Remote database: Specify host, port, user, password
- TimescaleDB: Set timescale parameter to true

For more details, see: https://github.com/eclipse-volttron/volttron-postgresql-historian
"""
