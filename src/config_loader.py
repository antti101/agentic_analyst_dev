# config_loader.py - Configuration management utility

import yaml
import os
from typing import Dict, Any


class ConfigManager:
    """Manages configuration loading and access for the Cube Analyst application."""

    def __init__(self, config_path: str = None):
        # Determine config path relative to project root if not provided
        if config_path:
            self.config_path = config_path
        else:
            project_root = os.path.join(os.path.dirname(__file__), '..')
            self.config_path = os.path.join(project_root, 'assets', 'config.yaml')
            self.config_path = os.path.normpath(self.config_path)

        print(f"DEBUG: Attempting to load config from absolute path: {self.config_path}")
        self.config = self.load_config()

    # -------------------------------------------------------------------------
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file (no fallback defaults)."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Critical configuration file missing: {self.config_path}"
            )

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                if not config:
                    raise ValueError(f"Configuration file {self.config_path} is empty.")
                print(f"Loaded configuration from {self.config_path}")
                return config
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")

    # -------------------------------------------------------------------------
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'autogen.bi_analyst.model')."""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    # -------------------------------------------------------------------------
    def get_semantic_layer_path(self) -> str:
        """Get semantic layer file path from config (required)."""
        path = self.get("semantic_layer.file_path")
        if not path or not os.path.exists(path):
            raise FileNotFoundError(
                f"Semantic layer file not found or path not set: {path}"
            )
        print(f"DEBUG: Semantic layer path resolved to: {path}")
        return path

    # -------------------------------------------------------------------------
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for Azure OpenAI."""
        api_key = os.getenv("AZURE_OPENAI_KEY")
        azure_endpoint = "https://ahava-agentic-fbp-mini.cognitiveservices.azure.com/"
        api_version = "2024-12-01-preview"
        deployment_name = "agentic-fbp-mini"

        if not api_key:
            raise ValueError("AZURE_OPENAI_KEY environment variable required.")

        temperature = self.get("autogen.bi_analyst.temperature", 0.1)
        max_tokens = self.get("autogen.bi_analyst.max_tokens", 2000)

        return {
            "config_list": [
                {
                    "model": deployment_name,
                    "api_key": api_key,
                    "api_type": "azure",
                    "base_url": azure_endpoint,
                    "api_version": api_version,
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }


# Global config instance
config = ConfigManager()
