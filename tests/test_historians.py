#!/usr/bin/env python3
"""
Comprehensive Unit Tests for VOLTTRON Historian Modules

This test suite covers:
- SQLite Historian installation and configuration
- PostgreSQL Historian installation and configuration
- Configuration file creation and validation
- Status checking functionality
- Error handling and edge cases
- Integration with VOLTTRON platform

Author: VOLTTRON AI System
Date: November 2025
"""

import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_app.sqlite_historian import (
    install_sqlite_historian,
    create_default_sqlite_config,
    create_sqlite_historian_config,
    check_sqlite_historian_status
)
from chat_app.postgresql_historian import (
    install_postgresql_historian,
    create_default_postgresql_config,
    create_postgresql_historian_config,
    check_postgresql_historian_status,
    get_postgresql_setup_instructions
)


class TestSQLiteHistorian(unittest.TestCase):
    """Test suite for SQLite Historian functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.volttron_home = os.path.join(self.test_dir, "volttron_home")
        os.makedirs(self.volttron_home, exist_ok=True)
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_create_default_sqlite_config(self):
        """Test creation of default SQLite historian configuration."""
        config_path = create_default_sqlite_config(self.volttron_home)
        
        self.assertTrue(os.path.exists(config_path))
        self.assertIn("sqlite-historian.config", config_path)
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertIn("connection", config)
        self.assertEqual(config["connection"]["type"], "sqlite")
        self.assertIn("params", config["connection"])
        self.assertEqual(config["connection"]["params"]["database"], "data/historian.sqlite")
        
        self.assertIn("tables_def", config)
        self.assertEqual(config["tables_def"]["data_table"], "data")
        self.assertEqual(config["tables_def"]["topics_table"], "topics")
    
    def test_create_sqlite_historian_config_custom(self):
        """Test creation of custom SQLite historian configuration."""
        with patch('chat_app.volttron_commands.get_volttron_home', return_value=self.volttron_home):
            config_path = create_sqlite_historian_config(
                database_path="custom/path/historian.db",
                table_prefix="custom_",
                data_table="custom_data",
                topics_table="custom_topics"
            )
        
        self.assertTrue(os.path.exists(config_path))
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertEqual(config["connection"]["params"]["database"], "custom/path/historian.db")
        self.assertEqual(config["tables_def"]["table_prefix"], "custom_")
        self.assertEqual(config["tables_def"]["data_table"], "custom_data")
        self.assertEqual(config["tables_def"]["topics_table"], "custom_topics")
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.wait_for_volttron_ready')
    def test_install_sqlite_historian_success(self, mock_wait, mock_home, mock_vctl, mock_run):
        """Test successful SQLite historian installation."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = self.volttron_home
        mock_wait.return_value = (True, "VOLTTRON ready")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Agent installed successfully"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = install_sqlite_historian()
        
        self.assertIn("✅", result)
        self.assertIn("SQLite historian installed", result)
        mock_run.assert_called_once()
        
        call_args = mock_run.call_args[0][0]
        self.assertIn("volttron-sqlite-historian", call_args)
        self.assertIn("--start", call_args)
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    def test_install_sqlite_historian_no_vctl(self, mock_vctl):
        """Test SQLite historian installation when vctl is not found."""
        mock_vctl.return_value = None
        
        result = install_sqlite_historian()
        
        self.assertIn("installation failed", result)
        self.assertIn("vctl command not found", result)
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.wait_for_volttron_ready')
    def test_install_sqlite_historian_not_ready(self, mock_wait, mock_home, mock_vctl):
        """Test SQLite historian installation when VOLTTRON is not ready."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = self.volttron_home
        mock_wait.return_value = (False, "VOLTTRON not ready after 15 seconds")
        
        result = install_sqlite_historian()
        
        self.assertIn("installation failed", result)
        self.assertIn("VOLTTRON not ready", result)
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    def test_check_sqlite_historian_status_installed(self, mock_home, mock_vctl, mock_run):
        """Test checking SQLite historian status when installed."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = self.volttron_home
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "sqlite-historian RUNNING"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = check_sqlite_historian_status()
        
        self.assertIn("SQLite historian status", result)
        self.assertIn("sqlite-historian RUNNING", result)
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    def test_check_sqlite_historian_status_not_found(self, mock_home, mock_vctl, mock_run):
        """Test checking SQLite historian status when not installed."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = self.volttron_home
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "listener RUNNING"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = check_sqlite_historian_status()
        
        self.assertIn("Not found", result)
        self.assertIn("Install with", result)


class TestPostgreSQLHistorian(unittest.TestCase):
    """Test suite for PostgreSQL Historian functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.volttron_home = os.path.join(self.test_dir, "volttron_home")
        os.makedirs(self.volttron_home, exist_ok=True)
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_create_default_postgresql_config_local(self):
        """Test creation of default PostgreSQL config for local connection."""
        config_path = create_default_postgresql_config(
            self.volttron_home,
            dbname="test_db"
        )
        
        self.assertTrue(os.path.exists(config_path))
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertEqual(config["connection"]["type"], "postgresql")
        self.assertEqual(config["connection"]["params"]["dbname"], "test_db")
        self.assertNotIn("host", config["connection"]["params"])
        self.assertNotIn("timescale_dialect", config["connection"]["params"])
    
    def test_create_default_postgresql_config_remote(self):
        """Test creation of default PostgreSQL config for remote connection."""
        config_path = create_default_postgresql_config(
            self.volttron_home,
            dbname="test_db",
            host="db.example.com",
            port=5432,
            user="testuser",
            password="testpass"
        )
        
        self.assertTrue(os.path.exists(config_path))
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertEqual(config["connection"]["params"]["dbname"], "test_db")
        self.assertEqual(config["connection"]["params"]["host"], "db.example.com")
        self.assertEqual(config["connection"]["params"]["port"], 5432)
        self.assertEqual(config["connection"]["params"]["user"], "testuser")
        self.assertEqual(config["connection"]["params"]["password"], "testpass")
    
    def test_create_default_postgresql_config_timescale(self):
        """Test creation of PostgreSQL config with TimescaleDB support."""
        config_path = create_default_postgresql_config(
            self.volttron_home,
            dbname="test_db",
            timescale=True
        )
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertTrue(config["connection"]["params"]["timescale_dialect"])
    
    def test_create_postgresql_historian_config_custom(self):
        """Test creation of custom PostgreSQL historian configuration."""
        with patch('chat_app.volttron_commands.get_volttron_home', return_value=self.volttron_home):
            config_path = create_postgresql_historian_config(
                dbname="custom_db",
                host="custom.host.com",
                port=5433,
                user="custom_user",
                password="custom_pass",
                table_prefix="prefix_",
                data_table="custom_data",
                topics_table="custom_topics",
                timescale=True
            )
        
        self.assertTrue(os.path.exists(config_path))
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertEqual(config["connection"]["params"]["dbname"], "custom_db")
        self.assertEqual(config["connection"]["params"]["host"], "custom.host.com")
        self.assertEqual(config["connection"]["params"]["port"], 5433)
        self.assertEqual(config["connection"]["params"]["user"], "custom_user")
        self.assertEqual(config["connection"]["params"]["password"], "custom_pass")
        self.assertTrue(config["connection"]["params"]["timescale_dialect"])
        
        self.assertEqual(config["tables_def"]["table_prefix"], "prefix_")
        self.assertEqual(config["tables_def"]["data_table"], "custom_data")
        self.assertEqual(config["tables_def"]["topics_table"], "custom_topics")
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.wait_for_volttron_ready')
    def test_install_postgresql_historian_success(self, mock_wait, mock_home, mock_vctl, mock_run):
        """Test successful PostgreSQL historian installation."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = self.volttron_home
        mock_wait.return_value = (True, "VOLTTRON ready")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Agent installed successfully"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = install_postgresql_historian(
            dbname="test_db",
            host="localhost",
            port=5432,
            user="testuser",
            password="testpass"
        )
        
        self.assertIn("✅", result)
        self.assertIn("PostgreSQL historian installed", result)
        self.assertIn("test_db@localhost:5432", result)
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertIn("volttron-postgresql-historian", call_args)
        self.assertIn("--start", call_args)
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.wait_for_volttron_ready')
    def test_install_postgresql_historian_local(self, mock_wait, mock_home, mock_vctl, mock_run):
        """Test PostgreSQL historian installation with local Unix socket."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = self.volttron_home
        mock_wait.return_value = (True, "VOLTTRON ready")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Agent installed successfully"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = install_postgresql_historian(dbname="test_db")
        
        self.assertIn("✅", result)
        self.assertIn("PostgreSQL historian installed", result)
        self.assertIn("test_db (local)", result)
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.wait_for_volttron_ready')
    def test_install_postgresql_historian_timescale(self, mock_wait, mock_home, mock_vctl, mock_run):
        """Test PostgreSQL historian installation with TimescaleDB."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = self.volttron_home
        mock_wait.return_value = (True, "VOLTTRON ready")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Agent installed successfully"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = install_postgresql_historian(
            dbname="test_db",
            host="localhost",
            timescale=True
        )
        
        # Concise format just shows success, TimescaleDB is in config not output
        self.assertIn("✅", result)
        self.assertIn("PostgreSQL historian installed", result)
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    def test_install_postgresql_historian_no_vctl(self, mock_vctl):
        """Test PostgreSQL historian installation when vctl is not found."""
        mock_vctl.return_value = None
        
        result = install_postgresql_historian()
        
        self.assertIn("installation failed", result)
        self.assertIn("vctl command not found", result)
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.wait_for_volttron_ready')
    def test_install_postgresql_historian_not_ready(self, mock_wait, mock_home, mock_vctl):
        """Test PostgreSQL historian installation when VOLTTRON is not ready."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = self.volttron_home
        mock_wait.return_value = (False, "VOLTTRON not ready after 15 seconds")
        
        result = install_postgresql_historian()
        
        self.assertIn("installation failed", result)
        self.assertIn("VOLTTRON not ready", result)
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    def test_check_postgresql_historian_status_installed(self, mock_home, mock_vctl, mock_run):
        """Test checking PostgreSQL historian status when installed."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = self.volttron_home
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "postgresql-historian RUNNING"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = check_postgresql_historian_status()
        
        self.assertIn("PostgreSQL historian status", result)
        self.assertIn("postgresql-historian RUNNING", result)
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    def test_check_postgresql_historian_status_not_found(self, mock_home, mock_vctl, mock_run):
        """Test checking PostgreSQL historian status when not installed."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = self.volttron_home
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "listener RUNNING"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = check_postgresql_historian_status()
        
        self.assertIn("Not found", result)
        self.assertIn("Install with", result)
    
    def test_get_postgresql_setup_instructions(self):
        """Test retrieval of PostgreSQL setup instructions."""
        result = get_postgresql_setup_instructions()
        
        self.assertIn("PostgreSQL Historian Setup Instructions", result)
        self.assertIn("CREATE DATABASE volttron", result)
        self.assertIn("CREATE TABLE IF NOT EXISTS topics", result)
        self.assertIn("CREATE TABLE IF NOT EXISTS data", result)
        self.assertIn("CREATE INDEX", result)
        self.assertIn("TimescaleDB", result)
        self.assertIn("GRANT", result)


class TestHistorianConfigurationValidation(unittest.TestCase):
    """Test configuration file validation for both historians."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.volttron_home = os.path.join(self.test_dir, "volttron_home")
        os.makedirs(self.volttron_home, exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_sqlite_config_json_format(self):
        """Test that SQLite config is valid JSON."""
        config_path = create_default_sqlite_config(self.volttron_home)
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertIsInstance(config, dict)
        self.assertIsInstance(config["connection"], dict)
        self.assertIsInstance(config["tables_def"], dict)
    
    def test_postgresql_config_json_format(self):
        """Test that PostgreSQL config is valid JSON."""
        config_path = create_default_postgresql_config(self.volttron_home)
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertIsInstance(config, dict)
        self.assertIsInstance(config["connection"], dict)
        self.assertIsInstance(config["tables_def"], dict)
    
    def test_sqlite_config_required_fields(self):
        """Test that SQLite config has all required fields."""
        config_path = create_default_sqlite_config(self.volttron_home)
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_fields = ["connection", "tables_def"]
        for field in required_fields:
            self.assertIn(field, config)
        
        self.assertIn("type", config["connection"])
        self.assertIn("params", config["connection"])
        self.assertIn("database", config["connection"]["params"])
    
    def test_postgresql_config_required_fields(self):
        """Test that PostgreSQL config has all required fields."""
        config_path = create_default_postgresql_config(self.volttron_home)
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_fields = ["connection", "tables_def"]
        for field in required_fields:
            self.assertIn(field, config)
        
        self.assertIn("type", config["connection"])
        self.assertIn("params", config["connection"])
        self.assertIn("dbname", config["connection"]["params"])
    
    def test_sqlite_config_directory_creation(self):
        """Test that config directory is created if it doesn't exist."""
        config_dir = os.path.join(self.volttron_home, "configs")
        self.assertFalse(os.path.exists(config_dir))
        
        create_default_sqlite_config(self.volttron_home)
        
        self.assertTrue(os.path.exists(config_dir))
    
    def test_postgresql_config_directory_creation(self):
        """Test that config directory is created if it doesn't exist."""
        config_dir = os.path.join(self.volttron_home, "configs")
        self.assertFalse(os.path.exists(config_dir))
        
        create_default_postgresql_config(self.volttron_home)
        
        self.assertTrue(os.path.exists(config_dir))


class TestHistorianErrorHandling(unittest.TestCase):
    """Test error handling for both historians."""
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.wait_for_volttron_ready')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_sqlite_install_exception_handling(self, mock_run, mock_wait, mock_home, mock_vctl):
        """Test SQLite historian installation exception handling."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = "/tmp/volttron_home"
        mock_wait.return_value = (True, "VOLTTRON ready")
        mock_run.side_effect = Exception("Test exception")
        
        result = install_sqlite_historian()
        
        self.assertIn("installation error", result)
        self.assertIn("Test exception", result)
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.wait_for_volttron_ready')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_postgresql_install_exception_handling(self, mock_run, mock_wait, mock_home, mock_vctl):
        """Test PostgreSQL historian installation exception handling."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = "/tmp/volttron_home"
        mock_wait.return_value = (True, "VOLTTRON ready")
        mock_run.side_effect = Exception("Test exception")
        
        result = install_postgresql_historian()
        
        self.assertIn("installation error", result)
        self.assertIn("Test exception", result)
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_sqlite_status_exception_handling(self, mock_run, mock_home, mock_vctl):
        """Test SQLite historian status check exception handling."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = "/tmp/volttron_home"
        mock_run.side_effect = Exception("Test exception")
        
        result = check_sqlite_historian_status()
        
        self.assertIn("status check error", result)
        self.assertIn("Test exception", result)
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_postgresql_status_exception_handling(self, mock_run, mock_home, mock_vctl):
        """Test PostgreSQL historian status check exception handling."""
        mock_vctl.return_value = "/path/to/vctl"
        mock_home.return_value = "/tmp/volttron_home"
        mock_run.side_effect = Exception("Test exception")
        
        result = check_postgresql_historian_status()
        
        self.assertIn("status check error", result)
        self.assertIn("Test exception", result)


if __name__ == '__main__':
    unittest.main()
