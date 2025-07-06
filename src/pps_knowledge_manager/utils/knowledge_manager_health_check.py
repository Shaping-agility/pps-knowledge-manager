"""
Health check utilities that use KnowledgeManager as the single source of truth.
"""

from ..core.knowledge_manager import KnowledgeManager


def knowledge_manager_health_check() -> bool:
    """
    Perform health check using KnowledgeManager's configured storage backend.
    This ensures all test/dev cycles use the same database configuration.
    """
    try:
        print("Initializing KnowledgeManager for health check...")

        # Initialize KnowledgeManager (will use config from ConfigManager)
        km = KnowledgeManager()

        print("KnowledgeManager initialized successfully")

        # Perform health check on all storage backends
        health = km.health_check()
        print(f"KnowledgeManager health check results: {health}")

        # Check if all storage backends are healthy
        if health.get("storage", False):
            print("All storage backends are healthy")
            return True
        else:
            print("One or more storage backends are unhealthy")
            return False

    except Exception as e:
        print(f"KnowledgeManager health check failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def get_knowledge_manager() -> KnowledgeManager:
    """
    Get a configured KnowledgeManager instance.
    This ensures all code uses the same configuration.
    """
    return KnowledgeManager()
