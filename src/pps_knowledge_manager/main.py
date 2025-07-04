"""
PPS Knowledge Manager - Main module
"""

from pathlib import Path
from .core.knowledge_manager import KnowledgeManager


def main():
    """Main entry point for the application."""
    print("Initializing PPS Knowledge Manager...")

    # Initialize the knowledge manager
    km = KnowledgeManager()

    # Perform health check
    health = km.health_check()
    print(f"System health: {health}")

    print("PPS Knowledge Manager initialized successfully!")


if __name__ == "__main__":
    main()
