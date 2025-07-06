"""
Test data management for PPS Knowledge Manager.
Handles database reset, script execution, and smoke testing for test cycles.
"""

import os
import psycopg2
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from ..core.knowledge_manager import KnowledgeManager

# Load environment variables
load_dotenv()


class SupabaseTestDataManager:
    """Manages test database setup and teardown for Supabase (public schema only)."""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.service_role_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url:
            raise ValueError("Supabase URL must be set in environment variables.")

        # Extract host, port, user from Supabase URL
        if "localhost" in self.supabase_url:
            self.host = "localhost"
            self.port = 5432
            self.user = os.getenv("SUPABASE_USER", "postgres")
            self.password = os.getenv("SUPABASE_PW")
            if not self.password:
                raise ValueError("SUPABASE_PW must be set for local development")
        else:
            self.host = self.supabase_url.replace("https://", "").replace(
                ".supabase.co", ""
            )
            self.host = f"db.{self.host}.supabase.co"
            self.port = 5432
            self.user = "postgres"
            self.password = self._extract_password_from_key()

    def _extract_password_from_key(self) -> str:
        if self.service_role_key is None:
            raise ValueError("Service role key is not set")
        return self.service_role_key

    def _get_admin_connection(
        self, database: str = "postgres"
    ) -> psycopg2.extensions.connection:
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=database,
                user=self.user,
                password=self.password,
            )
            conn.autocommit = True
            return conn
        except Exception as e:
            raise Exception(f"Failed to connect to PostgreSQL: {e}")

    def reset(self) -> bool:
        try:
            print(f"Resetting test database (public schema only)")
            script_paths = [
                "data/DDL/dropEntities.sql",
                "data/DDL/rolemanagement.sql",
                "data/DDL/tables.sql",
            ]
            success = self.run_script_sequence(script_paths)
            if not success:
                print("Script sequence failed during reset")
                return False
            if not self.smoke_test():
                print("Smoke test failed after reset")
                return False
            print(f"Database reset completed successfully")
            return True
        except Exception as e:
            print(f"Database reset failed: {e}")
            return False

    def execute_script(self, script_path: str) -> bool:
        try:
            script_file = Path(script_path)
            if not script_file.exists():
                print(f"Script file not found: {script_path}")
                return False
            print(f"Executing script: {script_path}")
            with open(script_file, "r") as f:
                script_content = f.read()
            conn = self._get_admin_connection("postgres")
            statements = [
                stmt.strip() for stmt in script_content.split(";") if stmt.strip()
            ]
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
        print(f"Running script sequence: {script_paths}")
        for script_path in script_paths:
            if not self.execute_script(script_path):
                print(f"Script sequence failed at: {script_path}")
                return False
        print("Script sequence completed successfully")
        return True

    def smoke_test(self, query: str | None = None, expected_count: int = 0) -> bool:
        try:
            if query is None:
                query = "SELECT COUNT(1) FROM health_test"
            print(f"Running smoke test: {query}")
            conn = self._get_admin_connection("postgres")
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
