"""
Test data management for PPS Knowledge Manager.
Handles database reset, script execution, and smoke testing for test cycles.
"""

import os
import psycopg2
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from ..core.knowledge_manager import KnowledgeManager
from .sql_parser import parse_postgresql_script


# Load environment variables
load_dotenv()


class SupabaseTestDataManager:
    """Manages test database setup and teardown for Supabase (public schema only)."""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.service_role_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url:
            raise ValueError("Supabase URL must be set in environment variables.")

        connection_config = self._determine_connection_config()
        self.host = connection_config["host"]
        self.port = connection_config["port"]
        self.user = connection_config["user"]
        self.password = connection_config["password"]

    def _determine_connection_config(self) -> Dict[str, Any]:
        """Determine connection configuration based on environment."""
        if self.supabase_url and "localhost" in self.supabase_url:
            return self._get_local_connection_config()
        else:
            return self._get_remote_connection_config()

    def _get_local_connection_config(self) -> Dict[str, Any]:
        """Get connection configuration for local development."""
        password = os.getenv("SUPABASE_PW")
        if not password:
            raise ValueError("SUPABASE_PW must be set for local development")

        return {
            "host": "localhost",
            "port": 5432,
            "user": os.getenv("SUPABASE_USER", "postgres"),
            "password": password,
        }

    def _get_remote_connection_config(self) -> Dict[str, Any]:
        """Get connection configuration for remote Supabase."""
        if not self.supabase_url:
            raise ValueError("Supabase URL is required for remote connection")

        host = self.supabase_url.replace("https://", "").replace(".supabase.co", "")
        host = f"db.{host}.supabase.co"

        return {
            "host": host,
            "port": 5432,
            "user": "postgres",
            "password": self._extract_password_from_key(),
        }

    def _extract_password_from_key(self) -> str:
        if self.service_role_key is None:
            raise ValueError("Service role key is not set")
        return self.service_role_key

    def _get_admin_connection(
        self, database: str = "postgres"
    ) -> psycopg2.extensions.connection:
        """Create and return a PostgreSQL connection with autocommit enabled."""
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
                "data/DDL/vector_search.sql",
                "data/DDL/security.sql",
            ]
            success = self.run_script_sequence(script_paths)
            if not success:
                print("Script sequence failed during reset")
                return False
            if not self.smoke_test():
                print("Smoke test failed after reset")
                return False
            if not self.smoke_test_tables_exist():
                print("Table existence smoke test failed after reset")
                return False
            print(f"Database reset completed successfully")
            return True
        except Exception as e:
            print(f"Database reset failed: {e}")
            return False

    def execute_script(self, script_path: str) -> bool:
        """Execute script using direct PostgreSQL connection with robust SQL parsing."""
        try:
            script_file = Path(script_path)
            if not script_file.exists():
                print(f"Script file not found: {script_path}")
                return False
            print(f"Executing script: {script_path}")

            script_content = self._read_script_file(script_file)
            statements = parse_postgresql_script(script_content)
            return self._execute_statements(statements, script_path)
        except Exception as e:
            print(f"Failed to execute script {script_path}: {e}")
            return False

    def _read_script_file(self, script_file: Path) -> str:
        """Read the content of a script file."""
        with open(script_file, "r") as f:
            return f.read()

    def _execute_statements(self, statements: List[str], script_path: str) -> bool:
        """Execute a list of SQL statements."""
        conn = self._get_admin_connection("postgres")

        try:
            with conn.cursor() as cursor:
                for i, statement in enumerate(statements):
                    print(f"Processing Statement {i+1}: {statement[:100]}...")
                    if not self._execute_single_statement(cursor, statement, i + 1):
                        return False
            conn.commit()
            print(f"Script executed successfully: {script_path}")
            return True
        finally:
            conn.close()

    def _execute_single_statement(
        self, cursor, statement: str, statement_number: int
    ) -> bool:
        """Execute a single SQL statement."""
        try:
            cursor.execute(statement)
            print(f"Executed Statement {statement_number}: {statement[:50]}...")
            return True
        except Exception as e:
            print(f"Failed to execute statement {statement_number}: {statement}")
            print(f"Error: {e}")
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

    def smoke_test_tables_exist(self) -> bool:
        """Check that required tables exist after setup."""
        try:
            print("Running table existence smoke test...")
            conn = self._get_admin_connection("postgres")

            required_tables = ["health_test", "documents", "chunks"]
            required_indexes = ["idx_chunks_embedding"]

            existing_tables = self._check_table_existence(conn, required_tables)
            existing_indexes = self._check_index_existence(conn, required_indexes)

            conn.close()

            return self._validate_existence_results(existing_tables, existing_indexes)

        except Exception as e:
            print(f"Table existence smoke test failed with error: {e}")
            return False

    def _check_table_existence(self, conn, required_tables: List[str]) -> List[tuple]:
        """Check existence of required tables."""
        existing_tables = []
        with conn.cursor() as cursor:
            for table in required_tables:
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                    (table,),
                )
                result = cursor.fetchone()
                exists = result[0] if result else False
                existing_tables.append((table, exists))
                print(f"Table {table}: {'✓' if exists else '✗'}")
        return existing_tables

    def _check_index_existence(self, conn, required_indexes: List[str]) -> List[tuple]:
        """Check existence of required indexes."""
        existing_indexes = []
        with conn.cursor() as cursor:
            for index in required_indexes:
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname = %s)",
                    (index,),
                )
                result = cursor.fetchone()
                exists = result[0] if result else False
                existing_indexes.append((index, exists))
                print(f"Index {index}: {'✓' if exists else '✗'}")
        return existing_indexes

    def _validate_existence_results(
        self, existing_tables: List[tuple], existing_indexes: List[tuple]
    ) -> bool:
        """Validate that all required tables and indexes exist."""
        missing_tables = [table for table, exists in existing_tables if not exists]
        missing_indexes = [index for index, exists in existing_indexes if not exists]

        if missing_tables or missing_indexes:
            print(
                f"Smoke test failed: Missing tables: {missing_tables}, Missing indexes: {missing_indexes}"
            )
            return False
        else:
            print("All required tables and indexes exist ✓")
            return True
