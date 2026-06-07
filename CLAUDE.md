# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kanvas.ai is an AI art advisory platform for the Estonian and Baltic art market. It combines 8 specialist LLM agents, auction data from 11,000+ lots across 7+ galleries, and a chat UI — all built with FastHTML (server-rendered Python, no React/Vue/Svelte).

## Running Locally

```bash
python main.py          # Starts on port 5009 (or PORT env var)
docker compose up --build  # Docker alternative
```

The app requires a `.env` file with `DB_URL` (PostgreSQL), `XAI_API_KEY` (Grok LLM), `POSTMARK_API_TOKEN` (email), and optionally `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` (OAuth).

## Tech Stack

- **Framework**: FastHTML (Python) — server-rendered hypermedia, no SPA
- **LLM**: LangChain + LangGraph ReAct agents, xAI Grok via `utils/llm.py`
- **Database**: PostgreSQL (`kanvas` schema), SQLAlchemy for ORM models, raw SQL via `text()` for chat/auth/auction tables
- **CSS**: Tailwind CSS via CDN
- **Deployment**: Docker + Coolify, push-to-main auto-deploys via webhook

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

LangChain `StructuredTool` instances with Pydantic input schemas. Available tools: `auctions.py` (lot lookup, artist history), `sql_query.py` (direct SQL), `charts.py` (treemap/price trends), `artworks.py` (artwork DB search), `search.py` (Exa web search), `news.py` (RSS + Exa news).

### Chat streaming (`chat/routes.py`, `chat/sse.py`)

POST `/app/chat` streams SSE events via `StreamingResponse`. Flow: route message to agent, build LangChain history (last 20 msgs), stream `graph.astream_events(version="v2")`. Event types: `AGENT_ROUTE`, `TOKEN`, `TOOL_START`, `TOOL_END`, `ARTIFACT`, `DONE`, `ERROR`. Messages and tool calls persisted to `chat_messages` table.

### Auth (`auth/`)

Email/password + Google OAuth. `auth/routes.py` has register, login, verify, forgot/reset password, profile/preferences endpoints. `auth/utils.py` has bcrypt hashing and Postmark email sending. Session keys: `chat_email`, `chat_uid` via `utils/session.py`.

### Database (`db.py`)

Two patterns coexist:
1. **SQLAlchemy ORM** (`models.py`, `Base`): Used for admin-facing `users`, `artworks`, `investments` tables.
2. **Raw SQL via `text()`**: Used for `chat_users`, `chat_sessions`, `chat_messages`, `auction_lots`, `user_profiles`. DDL lives in `db.py:_init_chat_tables()` with `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ADD COLUMN IF NOT EXISTS` migrations.

All tables in the `kanvas` schema. `search_path` set on every connection via SQLAlchemy event listener.

### Scrapers (`scripts/scrapers/`)

Playwright-based auction data scrapers for 15+ galleries (Estonian, Nordic, international). Shared utilities in `base.py` (price parsing, browser setup, painting detection). Run via `python -m scripts.scrape_auctions --provider haus`. Data saved to `data/auctions/` as JSON.

### i18n (`utils/i18n.py`)

12 languages. `t(key, lang)` for translations with English fallback. `get_lang(sess)` with IP-based detection. `js_translations(lang)` exports to frontend via `<script type="application/json">`.

### Daily digest (`scripts/daily_deals.py`)

Scans auction data for bidding wars, value finds, market movers. Sends HTML email via Postmark. Built-in scheduler in `main.py` runs at `DIGEST_HOUR` (default 7 AM). `--all` flag sends to all registered users; respects `notify_weekly_digest` preference.

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
| `SECRET_KEY` | HMAC secret for unsubscribe tokens |
