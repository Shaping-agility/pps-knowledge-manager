import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Always load environment variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase credentials are not set in environment variables.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def supabase_health_check() -> bool:
    try:
        client = get_supabase_client()
        # Try a simple query: list tables in the public schema
        response = client.table("health_test").select("*").limit(1).execute()
        if response is not None and response.data is not None:
            return True
        else:
            print(
                f"Supabase health check failed: No data returned. Full response: {response}"
            )
            return False
    except Exception as e:
        import traceback

        print(f"Supabase health check failed with exception: {e}")
        traceback.print_exc()
        return False
