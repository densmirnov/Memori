# Memori Gateway MVP

The gateway container runs both the FastAPI HTTP surface and the Memori core runtime in a single process, so deploying this stack automatically brings up “Memori itself” alongside the HTTP and MCP entrypoints. The only external dependency is your Supabase/Postgres instance that already lives on the shared `dokploy-network`.

> Context: `docs/llms.txt` describes how `Memori(...)` instances persist memories, optionally enabling `conscious_ingest` and `auto_ingest` to surface relevant context (eg. `memori = Memori(conscious_ingest=True, auto_ingest=True)`), so the gateway simply toggles those behaviours through environment variables.

## Files

| Path | Purpose |
| --- | --- |
| `requirements.txt` | Runtime dependencies plus an editable install of the local Memori SDK. |
| `Dockerfile` | Builds a Python 3.11 image containing both Memori and the gateway app. |
| `docker-compose.yml` | Starts the HTTP gateway and the optional MCP sidecar inside the same compose project while reusing the external Supabase/Postgres. |

## Environment

```
MEMORI_DB_DSN=postgresql://supabase_user:supabase_pass@supabase-host:5432/memori
OPENAI_API_KEY=sk-...
GATEWAY_API_KEY=change-me
MEMORI_DEFAULT_MODEL=gpt-4o-mini
MEMORI_AUTO_INGEST=true
MEMORI_CONSCIOUS_INGEST=false
```

These map directly to the `Memori` constructor flags and API key guards exposed in `app/config.py`, keeping the behaviour identical between the HTTP API and MCP tool.

## Usage

```bash
cd memori-gateway
docker compose --project-name memori up -d
```

- `memori-gateway` – HTTP API listening on `0.0.0.0:8000` for `/chat` and `/health`.
- `memori-gateway-mcp` – optional MCP server that runs the same `chat_with_memory` logic over stdio. Scale it up only when you need IDE/Cursor integration.

> The compose file expects an existing external `dokploy-network` where Supabase/Postgres is already reachable. No extra database container is created here.

Once the stack is up you can drive the HTTP endpoint from tooling such as n8n:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${GATEWAY_API_KEY}" \
  -d '{"session_id":"demo","input":"Что ты помнишь обо мне?"}'
```
