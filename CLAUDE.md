# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kanvas.ai is an AI art advisory platform for the Estonian and Baltic art market. It combines 8 specialist LLM agents, auction data from 11,000+ lots across 7+ galleries, and a chat UI — all built with FastHTML (server-rendered Python, no React/Vue/Svelte).

## Running Locally

```bash
python main.py          # Monolith (web + chat + game) on port 5009 (or PORT env var)
python -m api.fastapi_app  # Standalone JSON API on port 5012 (for api.kanvas.ai / mobile app)
docker compose up --build  # Docker alternative (monolith)
```

The app requires a `.env` file with `DB_URL` (PostgreSQL), `XAI_API_KEY` (Grok LLM), `POSTMARK_API_TOKEN` (email), and optionally `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` (OAuth) and `JWT_SECRET` (mobile API tokens).

## Tech Stack

- **Framework**: FastHTML (Python) — server-rendered hypermedia, no SPA
- **LLM**: LangChain + LangGraph ReAct agents, xAI Grok via `utils/llm.py`
- **Database**: PostgreSQL (`kanvas` schema), SQLAlchemy for ORM models, raw SQL via `text()` for chat/auth/auction tables
- **CSS**: Tailwind CSS via CDN
- **API**: FastAPI (`api/`) — JSON API for the mobile app, JWT auth
- **Deployment**: Docker + Coolify. Two apps deploy from `main` (both auto-deploy on push): `kanvas-monolith` (kanvas.ai, `Dockerfile`, port 5009) and `api` (api.kanvas.ai, `Dockerfile.api`, port 5012)

## FastHTML Conventions (MUST FOLLOW)

- `from fasthtml.common import *` — always use the wildcard import
- `app, rt = fast_app(...)` for app init; `@rt` decorator for routes
- `serve()` at the bottom — never `if __name__ == "__main__"`
- Return FT components (FastTags) from handlers; use `cls` for CSS classes
- `RedirectResponse` with `status_code=303` for redirects
- Sessions via `sess` parameter; auth state via `utils/session.py` helpers
- Prefer Python over JS; use `Style()`/`Script()` for inline CSS/JS
- Use `APIRouter` (`ar`) for route modules that mount via `ar.to_app(app)`

## Architecture

### Two UI layers

1. **Public pages** (`pages/`, `components/layout.py`): Marketing site with `Page()` wrapper, navbar, footer. Routes in `main.py`.
2. **Chat app** (`chat/`): 3-pane UI (sidebar + messages + artifact pane). Routes registered via `register_chat_routes(rt)`. Layout in `chat/layout.py`, components in `chat/components.py`, JS in `static/chat.js`.

### Agent system (`agents/`)

- **Registry** (`registry.py`): Static `AGENTS` tuple of `AgentSpec` dataclasses. `AGENTS_BY_SLUG` dict for lookup. 4 categories: research, market, advisory, valuation.
- **Router** (`router.py`): 3-tier routing — prefix match (`artist: query`) > keyword scoring > LLM classification fallback. Returns agent slug.
- **Base** (`base.py`): `build_agent()` creates LangGraph ReAct agents from spec + tools. System prompts from `prompts/system/{slug}.md` + shared context from `prompts/shared/art_context.md`. `cached_agent(slug)` caches built agents.
- **Agent modules** (`research/`, `market/`, `advisory/`, `valuation/`): Each defines a `build()` function returning a LangGraph graph with its own tool set.

### Tools (`tools/`)

LangChain `StructuredTool` instances with Pydantic input schemas. Available tools: `auctions.py` (lot lookup, artist history), `sql_query.py` (text-to-SQL via LLM), `charts.py` (treemap/price trends), `artworks.py` (artwork DB search), `search.py` (Exa web search), `news.py` (RSS + Exa news).

**Tool ordering matters**: Agents prefer tools listed earlier. For auction queries, direct DB tools (`search_auction_lots`, `artist_auction_history`) must come before `art_market_query` (which adds an LLM round-trip to draft SQL). Never add web search tools to the auction_tracker agent.

### Chat streaming (`chat/routes.py`, `chat/sse.py`)

POST `/app/chat` streams SSE events via `StreamingResponse`. Flow: route message to agent, build LangChain history (last 20 msgs), stream `graph.astream_events(version="v2")`. Event types: `AGENT_ROUTE`, `TOKEN`, `TOOL_START`, `TOOL_END`, `ARTIFACT`, `DONE`, `ERROR`. Messages and tool calls persisted to `chat_messages` table.

### Auth (`auth/`)

Email/password + Google OAuth. `auth/routes.py` has register, login, verify, forgot/reset password, profile/preferences endpoints. `auth/utils.py` has bcrypt hashing and Postmark email sending. Session keys: `chat_email`, `chat_uid` via `utils/session.py`.

### Standalone API (`api/`)

A FastAPI app serving the mobile client at `api.kanvas.ai`, decoupled from the FastHTML monolith. `api/fastapi_app.py:create_app()` builds the app with **no route prefix** — the prefix comes from the mount point or reverse proxy. It is consumed two ways:
1. **Standalone** (`python -m api.fastapi_app`, port 5012) — deployed via `Dockerfile.api` to `api.kanvas.ai`.
2. **Mounted** in `main.py` at `/api/v1` (`app.mount("/api/v1", api_app)`, docs at `/api/v1/docs`) for dual deploy.

Auth is **JWT** (`api/fastapi_auth.py`, HS256 signed with `JWT_SECRET` → falls back to `SECRET_KEY`, 72h expiry) — distinct from the monolith's cookie sessions. DB access via FastAPI deps (`api/fastapi_deps.py`: `get_db`, `get_current_user`, `get_optional_user`). Schemas in `api/fastapi_schemas.py`; chat reuses the same agent/streaming stack and returns SSE. `api/swagger.json` is the published OpenAPI spec. Note: `api/routes.py` (the `ar` APIRouter) and `api/mobile_auth.py` are separate FastHTML-side routes mounted in `main.py`, NOT part of the FastAPI app.

### Database (`db.py`)

Two patterns coexist:
1. **SQLAlchemy ORM** (`models.py`, `Base`): Used for admin-facing `users`, `artworks`, `investments` tables.
2. **Raw SQL via `text()`**: Used for `chat_users`, `chat_sessions`, `chat_messages`, `auction_lots`, `user_profiles`. DDL lives in `db.py:_init_chat_tables()` with `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ADD COLUMN IF NOT EXISTS` migrations.

All tables in the `kanvas` schema. `search_path` set on every connection via SQLAlchemy event listener.

**`auction_lots` indexes**: provider, author, date, end_price, status, category, tech, source_url, and composite (status, end_price). All defined as `CREATE INDEX IF NOT EXISTS` in `db.py` migrations. When adding new query patterns, check if an index is needed.

### Scrapers (`scripts/scrapers/`)

Playwright-based auction data scrapers for 15+ galleries (Estonian, Nordic, international). Shared utilities in `base.py` (price parsing, browser setup, painting detection). Run via `python -m scripts.scrape_auctions --provider haus`. Data saved to `data/auctions/` as JSON.

### i18n (`utils/i18n.py`)

12 languages. `t(key, lang)` for translations with English fallback. `get_lang(sess)` with IP-based detection. `js_translations(lang)` exports to frontend via `<script type="application/json">`.

### Daily digest (`scripts/daily_deals.py`)

Scans auction data for bidding wars, value finds, market movers. Sends HTML email via Postmark. Built-in scheduler in `main.py` runs at `DIGEST_HOUR` (default 7 AM). `--all` flag sends to all registered users; respects `notify_weekly_digest` preference.

### Chat session sharing (`chat/routes.py`)

`POST /api/chat/share` generates a `secrets.token_urlsafe(16)` share token stored in `chat_sessions.share_token`. `GET /share/{token}` renders a public read-only view via `shared_chat_page()`. Sidebar sessions show share icons on hover (desktop) or always (mobile). Header has Copy and Share buttons with SVG icons and checkmark feedback animation.

### Art Guru game (`game/`)

Text RPG reusing chat streaming infrastructure. `GameState` tracks character, round, resources. Game-specific system prompts in `game/prompts.py`.

## Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `DB_URL` | PostgreSQL connection string |
| `XAI_API_KEY` | xAI Grok API key for LLM agents |
| `POSTMARK_API_TOKEN` | Transactional email |
| `GOOGLE_CLIENT_ID/SECRET` | Google OAuth |
| `SERVICE_URL` | Public base URL (default: https://kanvas.ai) |
| `PORT` | Server port (default: 5009) |
| `DIGEST_ENABLED` | Enable daily digest scheduler (default: "1") |
| `DIGEST_HOUR` | Hour to send digest (default: 7) |
| `SECRET_KEY` | HMAC secret for unsubscribe tokens (JWT fallback) |
| `JWT_SECRET` | Signing secret for mobile API tokens (`api/`) |
| `EXA_API_KEY` | Exa web search (artist research + news fallback) |
| `NEWS_INTERVAL_SECONDS` | News feed cache/poll interval (default 1800) |
