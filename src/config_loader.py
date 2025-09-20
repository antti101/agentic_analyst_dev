# config_loader.py - Configuration management utility

import yaml
import os
from typing import Dict, Any

class ConfigManager:
    """Manages configuration loading and access for the Cube Analyst application"""
    
    def __init__(self, config_path: str = None):
        if config_path:
            self.config_path = config_path
        else:
            # Build path relative to this file's location to make it robust
            project_root = os.path.join(os.path.dirname(__file__), '..')
            self.config_path = os.path.join(project_root, 'assets', 'config.yaml')
            self.config_path = os.path.normpath(self.config_path)
        
        print(f"DEBUG: Attempting to load config from absolute path: {self.config_path}")
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with fallback to defaults"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    print(f"Loaded configuration from {self.config_path}")
                    return config
            else:
                print(f"Config file {self.config_path} not found, using defaults")
                return self.get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if config file is not available"""
        return {
            "semantic_layer": {
                "file_path": "assets/semantic_layer.txt",
                "reload_interval": 3600
            },
            "autogen": {
                "bi_analyst": {
                    "model": "gpt-4",
                    "temperature": 0.1,
                    "max_tokens": 2000,
                    "max_turns": 1
                }
            },
            "data_platform": {
                "cube_categories": ["orders", "products", "inventory", "customers", "marketing", "delivery"],
                "default_search_limit": 50,
                "analysis_hints": [
                    "Consider both measures and dimensions for complete analysis",
                    "Check cube relationships when analyzing across data marts",
                    "Use dimension variants to understand possible filter values"
                ]
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "cube_analyst.log"
            },
            "performance": {
                "cache_enabled": True,
                "cache_size": 1000,
                "timeout_seconds": 30
            }
        }
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'autogen.bi_analyst.model')"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_semantic_layer_path(self) -> str:
        """Get semantic layer file path from config file."""
        # NOTE: Environment variable check is temporarily removed for debugging.
        print("--- DEBUGGING get_semantic_layer_path (v3) ---")
        final_path = self.get("semantic_layer.file_path", "assets/semantic_layer.txt")
        print(f"DEBUG: Final path chosen by config loader: {final_path}")
        print("-----------------------------------------")
        return final_path
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for AutoGen"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        model = self.get("autogen.bi_analyst.model", "gpt-4")
        temperature = self.get("autogen.bi_analyst.temperature", 0.1)
        max_tokens = self.get("autogen.bi_analyst.max_tokens", 2000)
        
        return {
            "config_list": [
                {
                    "model": model,
                    "api_key": api_key,
                    "api_type": "openai"
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

# Global config instance
config = ConfigManager()
