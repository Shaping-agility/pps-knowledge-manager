"""
Pytest configuration for PPS Knowledge Manager tests.
"""

import pytest
from src.pps_knowledge_manager.utils.test_data_manager import SupabaseTestDataManager


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Reset the test database before running the test suite.
    This fixture runs automatically for all tests.
    """
    print("Setting up test database...")

    try:
        # Create test data manager
        manager = SupabaseTestDataManager()

        # Reset database to clean state
        success = manager.reset()

        if not success:
            pytest.fail("Failed to reset test database")

        print("Test database setup completed successfully")

        # Yield to allow tests to run
        yield

        # No cleanup required as per requirements

    except Exception as e:
        pytest.fail(f"Failed to setup test database: {e}")


@pytest.fixture
def test_data_manager():
    """
    Provide a test data manager instance for individual tests.
    """
    return SupabaseTestDataManager()
