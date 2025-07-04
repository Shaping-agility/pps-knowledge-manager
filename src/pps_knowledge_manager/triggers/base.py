"""
Base trigger classes and interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path


class Trigger(ABC):
    """Base class for all triggers in the system."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def start(self) -> None:
        """Start the trigger."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the trigger."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if the trigger is currently running."""
        pass


class FileTrigger(Trigger):
    """Base class for file-based triggers."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.watch_path = Path(config.get("watch_path", ""))
        self.file_types = config.get("file_types", [])

    def validate_config(self) -> bool:
        """Validate the trigger configuration."""
        return self.watch_path.exists() and self.watch_path.is_dir()


class WebhookTrigger(Trigger):
    """Base class for webhook-based triggers."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get("endpoint", "/webhook")
        self.method = config.get("method", "POST")

    def validate_config(self) -> bool:
        """Validate the trigger configuration."""
        return bool(self.endpoint and self.method)
