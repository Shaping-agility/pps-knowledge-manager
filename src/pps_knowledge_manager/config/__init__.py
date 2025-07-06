"""
Configuration management for PPS Knowledge Manager.
"""

from typing import Dict, Any
import yaml
from pathlib import Path


class ConfigManager:
    """Manages configuration for the knowledge manager."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or Path("config/knowledge_manager.yaml")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "storage": {
                "supabase": {
                    "url": "http://localhost:54321",
                    "key": "your-supabase-key",
                    "database_name": "postgres",
                    "enabled": True,
                },
                "neo4j": {
                    "uri": "bolt://localhost:7687",
                    "username": "neo4j",
                    "password": "password",
                    "enabled": False,
                },
            },
            "chunking": {
                "default_strategy": "lda",
                "strategies": {"lda": {"num_topics": 10, "chunk_size": 1000}},
            },
            "triggers": {
                "webhook": {"enabled": True, "port": 8000},
                "file_monitor": {"enabled": False, "watch_paths": []},
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)
