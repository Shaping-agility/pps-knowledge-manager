# ADR 0002 – Remove Docker-dependent anon-key retrieval

Date: 2025-07-13

## Status
Accepted

## Context
Early in the project we used a quick-and-dirty helper (`get_supabase_anon_key`) that executed `docker exec supabase-kong env` to scrape the local Supabase anon key.  This worked on a single developer workstation but broke in CI, on Windows without Docker Desktop, and in Lambda where no Docker socket exists.

## Decision
1. Delete the helper and any call-sites.
2. Rely exclusively on environment variables loaded via `python-dotenv` (`SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_ANON_KEY`).
3. Document the required variables in `docs/security.md` and the project README.

## Consequences
+ **Portability** – Code now runs in any environment that can provide a `.env` file or secret manager injection.
+ **Security** – No more shelling out in production; attack surface reduced.
+ **Simplicity** – Fewer moving parts and less brittle local setup.

No rollback needed; the helper was already bypassed in most code-paths and will be removed in the same commit. 