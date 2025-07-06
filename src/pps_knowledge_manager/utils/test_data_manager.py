"""
Test data management for PPS Knowledge Manager.
Handles database reset, script execution, and smoke testing for test cycles.
"""

import os
import psycopg2
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabaseTestDataManager:
    """Manages test database setup and teardown for Supabase."""

    def __init__(self, database_name: str = "pps_km_test"):
        self.database_name = database_name
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.service_role_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url:
            raise ValueError("Supabase URL must be set in environment variables.")

        # Extract host, port, user from Supabase URL
        # For local Supabase: http://localhost:54321 -> localhost:54322
        # For cloud Supabase: https://project-ref.supabase.co -> db.project-ref.supabase.co:5432
        if "localhost" in self.supabase_url:
            # Local Supabase
            self.host = "localhost"
            self.port = (
                5432  # Local Supabase PostgreSQL port (standard PostgreSQL port)
            )
            # Use dedicated environment variables for local development
            self.user = os.getenv("SUPABASE_USER", "postgres")
            self.password = os.getenv("SUPABASE_PW")
            if not self.password:
                raise ValueError("SUPABASE_PW must be set for local development")
        else:
            # Cloud Supabase
            self.host = self.supabase_url.replace("https://", "").replace(
                ".supabase.co", ""
            )
            self.host = f"db.{self.host}.supabase.co"
            self.port = 5432
            self.user = "postgres"
            # Extract password from service role key for cloud
            self.password = self._extract_password_from_key()

    def _extract_password_from_key(self) -> str:
        """Extract database password from service role key."""
        # This is a simplified approach - in practice, you might need to decode the JWT
        # For now, we'll use the service role key as the password
        # TODO: Implement proper JWT decoding to extract the actual database password
        if self.service_role_key is None:
            raise ValueError("Service role key is not set")
        return self.service_role_key

    def _get_admin_connection(
        self, database: str = "postgres"
    ) -> psycopg2.extensions.connection:
        """Get a direct PostgreSQL connection for admin operations."""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=database,
                user=self.user,
                password=self.password,
            )
            conn.autocommit = True  # Required for DROP/CREATE DATABASE
            return conn
        except Exception as e:
            raise Exception(f"Failed to connect to PostgreSQL: {e}")

    def reset(self) -> bool:
        """Reset the test database to a clean state."""
        try:
            print(f"Resetting test database: {self.database_name}")

            # Step 1: Drop and recreate database
            self._reset_database()

            # Step 2: Run script sequence
            script_paths = [
                "data/DDL/rolemanagement.sql",
                "data/DDL/tables.sql",
            ]
            success = self.run_script_sequence(script_paths)

            if not success:
                print("Script sequence failed during reset")
                return False

            # Step 3: Run smoke test
            if not self.smoke_test():
                print("Smoke test failed after reset")
                return False

            print(f"Database reset completed successfully")
            return True

        except Exception as e:
            print(f"Database reset failed: {e}")
            return False

    def _reset_database(self) -> None:
        """Drop and recreate the test database."""
        try:
            # Connect to default postgres database
            conn = self._get_admin_connection("postgres")

            # Terminate all connections to the test database first
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{self.database_name}'
                    AND pid <> pg_backend_pid()
                """
                )
                print(f"Terminated connections to {self.database_name}")

            # Drop database if it exists
            with conn.cursor() as cursor:
                cursor.execute(f"DROP DATABASE IF EXISTS {self.database_name}")
                print(f"Dropped database {self.database_name}")

            # Create new database
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE {self.database_name}")
                print(f"Created database {self.database_name}")

            conn.close()

        except Exception as e:
            raise Exception(f"Failed to reset database: {e}")

    def execute_script(self, script_path: str) -> bool:
        """Execute a single SQL script file."""
        try:
            script_file = Path(script_path)
            if not script_file.exists():
                print(f"Script file not found: {script_path}")
                return False

            print(f"Executing script: {script_path}")

            # Read script content
            with open(script_file, "r") as f:
                script_content = f.read()

            # Connect to test database
            conn = self._get_admin_connection(self.database_name)

            # Split script into individual statements
            statements = [
                stmt.strip() for stmt in script_content.split(";") if stmt.strip()
            ]

            # Execute each statement
            with conn.cursor() as cursor:
                for statement in statements:
                    if statement and not statement.startswith("--"):
                        try:
                            cursor.execute(statement)
                            print(f"Executed: {statement[:50]}...")
                        except Exception as e:
                            print(f"Failed to execute statement: {statement}")
                            print(f"Error: {e}")
                            conn.rollback()
                            conn.close()
                            return False

            conn.commit()
            conn.close()
            print(f"Script executed successfully: {script_path}")
            return True

        except Exception as e:
            print(f"Failed to execute script {script_path}: {e}")
            return False

    def run_script_sequence(self, script_paths: List[str]) -> bool:
        """Execute a sequence of SQL scripts in order."""
        print(f"Running script sequence: {script_paths}")

        for script_path in script_paths:
            if not self.execute_script(script_path):
                print(f"Script sequence failed at: {script_path}")
                return False

        print("Script sequence completed successfully")
        return True

    def smoke_test(
        self, query: str = "SELECT COUNT(1) FROM health_test", expected_count: int = 0
    ) -> bool:
        """Run a smoke test to verify database setup."""
        try:
            print(f"Running smoke test: {query}")

            # Connect to test database
            conn = self._get_admin_connection(self.database_name)

            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                count = result[0] if result else 0

            conn.close()

            print(f"Smoke test result: {count} (expected: {expected_count})")

            if count == expected_count:
                print("Smoke test passed")
                return True
            else:
                print(f"Smoke test failed: expected {expected_count}, got {count}")
                return False

        except Exception as e:
            print(f"Smoke test failed with error: {e}")
            return False
