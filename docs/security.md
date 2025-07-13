# Security & Configuration Guide

> **Important**: PII/PIA checks are currently **disabled**.  Set `require_pii_check=true` in your environment or deployment manifest to enable them when needed.

## Environment Variables
| Variable | Description | Required for | Example |
|----------|-------------|--------------|---------|
| `SUPABASE_URL` | Public URL of the Supabase project | All environments | `https://xyzcompany.supabase.co` |
| `SUPABASE_KEY` | Service-role key (server-side code only) | Local testing, migrations | `eyJhbGciOi...` |
| `SUPABASE_ANON_KEY` | anon key (client-side, Lambda read-only paths) | Lambda, frontend | `eyJhbGciOi...` |
| `SUPABASE_USER` | Postgres username for direct psql access | Local tests | `postgres` |
| `SUPABASE_PW` | Password for the Postgres user | Local tests | `postgres` |
| `require_pii_check` | Toggle to enable PII/PIA redaction | Future | `false` |

All secrets are loaded via `python-dotenv`; `.env` should live at project root and **never** be committed.

## Database Roles & Row-Level Security (RLS)
1. `service_role` – Full access, used only by migrations and test data manager.
2. `anon` – Read-only queries through public API & Lambdas.

### Policies
```
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks    ENABLE ROW LEVEL SECURITY;

-- Allow anyone with anon key to read chunks/documents
CREATE POLICY anon_read_documents ON documents FOR SELECT USING (true);
CREATE POLICY anon_read_chunks    ON chunks    FOR SELECT USING (true);

-- service_role bypasses RLS automatically
```
These statements live in `data/DDL/security.sql` and are executed as part of the reset sequence.

## Key Rotation
Rotate both keys every 90 days.  Update the secret manager or `.env` and restart services.

## Threat Model (current scope)
• Internal developers and CI agents are trusted.
• No PII processing – flag disabled.
• Attack surface limited to Supabase REST and Postgres endpoints.

Refer to ADR-0002 for rationale behind removing Docker-dependent auth hacks. 