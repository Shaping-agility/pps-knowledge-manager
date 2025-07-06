import os
import subprocess
from supabase import create_client, Client
from dotenv import load_dotenv

# Always load environment variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Service role key


def get_supabase_anon_key() -> str | None:
    """Get the anon key from local Supabase Kong container."""
    try:
        result = subprocess.run(
            ["docker", "exec", "supabase-kong", "env"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.split("\n"):
            if line.startswith("SUPABASE_ANON_KEY="):
                return line.split("=", 1)[1]
    except Exception as e:
        print(f"Failed to get anon key from Kong container: {e}")
    return None


def get_supabase_client(use_anon_key: bool = False) -> Client:
    """Get a Supabase client instance with schema support. Use as context manager for proper resource management."""
    if not SUPABASE_URL:
        raise ValueError("Supabase URL is not set in environment variables.")

    if use_anon_key:
        # For local development, get anon key from Kong container
        if "localhost" in SUPABASE_URL:
            anon_key = get_supabase_anon_key()
            if not anon_key:
                raise ValueError("Could not retrieve anon key from local Supabase")
            return create_client(SUPABASE_URL, anon_key)
        else:
            # For cloud, we'd need SUPABASE_ANON_KEY env var
            anon_key = os.getenv("SUPABASE_ANON_KEY")
            if not anon_key:
                raise ValueError("SUPABASE_ANON_KEY is required for anon operations")
            return create_client(SUPABASE_URL, anon_key)
    else:
        # Use service role key
        if not SUPABASE_KEY:
            raise ValueError(
                "Supabase service role key is not set in environment variables."
            )
        return create_client(SUPABASE_URL, SUPABASE_KEY)


class SupabaseConnection:
    """Context manager for Supabase connections with schema support."""

    def __init__(self, use_anon_key: bool = False):
        self.use_anon_key = use_anon_key
        self.client = None

    def __enter__(self):
        self.client = get_supabase_client(self.use_anon_key)
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Supabase client doesn't need explicit cleanup, but we can set to None
        self.client = None


def supabase_health_check() -> bool:
    """Legacy health check for backward compatibility - checks main database connectivity."""
    try:
        print(f"Supabase health check - URL: {SUPABASE_URL}")

        # Use service role key for basic connectivity check
        print("Using service role key for health check...")

        # Use stateless connection pattern with service role key
        with SupabaseConnection(use_anon_key=False) as client:
            print("Supabase client created successfully with service role key")

            # Try a simple query to verify connectivity
            print("Attempting to verify connectivity...")
            response = (
                client.table("_dummy_table_that_does_not_exist_")
                .select("*")
                .limit(1)
                .execute()
            )

            # We expect this to fail with a specific error, but the fact that we get a response
            # means the connection is working
            print(f"Response received: {response}")

            # If we get here, the connection is working (even if the table doesn't exist)
            print("Supabase health check passed - connection verified")
            return True

    except Exception as e:
        # Check if it's the expected "table doesn't exist" error
        if "does not exist" in str(e) or "42P01" in str(e):
            print(
                "Supabase health check passed - connection verified (expected table not found error)"
            )
            return True
        else:
            print(f"Supabase health check failed with unexpected exception: {e}")
            print(f"Exception type: {type(e).__name__}")
            return False
