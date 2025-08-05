"""
Configuration management for BorgDash
"""

import toml
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel


class ServerConfig(BaseModel):
    """Server configuration"""
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    data_dir: str = "./data"
    config_dir: str = "./config"


class AuthConfig(BaseModel):
    """Authentication configuration"""
    username: str = "admin"
    password: str = "admin"  # plaintext for now
    jwt_secret: str = "your-jwt-secret-change-this"
    jwt_expire_hours: int = 24
    api_tokens: List[str] = ["your-api-token-change-this"]  # API tokens for push endpoints


class Config(BaseModel):
    """Main configuration"""
    server: ServerConfig = ServerConfig()
    auth: AuthConfig = AuthConfig()


def load_config(config_path: str) -> Config:
    """Load configuration from TOML file"""
    config_file = Path(config_path)
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config_data = toml.load(f)
            return Config(**config_data)
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}")
            print("Using default configuration")
    else:
        print(f"Config file {config_path} not found, using defaults")
    
    return Config()


def get_all_job_configs(config_dir: str) -> Dict[str, Dict[str, Any]]:
    """Load and validate all job configurations"""
    from validation import validate_configs
    
    try:
        return validate_configs(config_dir)
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        # Return empty dict if validation fails
        return {}
