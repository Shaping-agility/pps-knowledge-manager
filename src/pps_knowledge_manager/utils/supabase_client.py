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


def get_supabase_client(
    database_name: str | None = None, use_anon_key: bool = False
) -> Client:
    """Get a Supabase client instance. Use as context manager for proper resource management."""
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
    """Context manager for Supabase connections."""

    def __init__(self, database_name: str | None = None, use_anon_key: bool = False):
        self.database_name = database_name
        self.use_anon_key = use_anon_key
        self.client = None

    def __enter__(self):
        self.client = get_supabase_client(self.database_name, self.use_anon_key)
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Supabase client doesn't need explicit cleanup, but we can set to None
        self.client = None


def supabase_health_check() -> bool:
    try:
        # Log the credentials being used (mask the key for security)
        print(f"Supabase health check - URL: {SUPABASE_URL}")

        # For health checks, use anon key for basic API operations
        print("Using anon key for health check...")

        # Debug: Get and log the anon key
        anon_key = get_supabase_anon_key()
        if anon_key:
            masked_anon_key = (
                anon_key[:10] + "..." + anon_key[-10:] if len(anon_key) > 20 else "***"
            )
            print(f"Retrieved anon key: {masked_anon_key}")
        else:
            print("Failed to retrieve anon key")
            return False

        # Use stateless connection pattern
        with SupabaseConnection(use_anon_key=True) as client:
            print("Supabase client created successfully with anon key")

            # Try a simple query that doesn't require a specific table
            print("Attempting to query system information...")
            response = client.rpc("version").execute()

            print(f"Response received: {response}")
            print(f"Response data: {response.data if response else 'None'}")

            if response is not None:
                print("Supabase health check passed")
                return True
            else:
                print(
                    f"Supabase health check failed: No data returned. Full response: {response}"
                )
                return False
    except Exception as e:
        import traceback

        print(f"Supabase health check failed with exception: {e}")
        print(f"Exception type: {type(e).__name__}")
        traceback.print_exc()
        return False
