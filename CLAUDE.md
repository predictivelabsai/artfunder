# Kanvas.ai - Fine Art Investment Platform

## Project Overview
Kanvas.ai is a fine art-backed investment platform built entirely with FastHTML + SQLAlchemy + PostgreSQL. It connects artists and galleries seeking capital with investors looking for art-backed returns through fractional ownership.

## Tech Stack
- **Framework**: FastHTML (Python) - server-rendered hypermedia application
- **CSS**: Tailwind CSS via CDN
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Schema**: `kanvas` schema in PostgreSQL
- **Deployment**: Docker + Docker Compose (Coolify-ready)
- **Server**: Uvicorn (via FastHTML's `serve()`)

## FastHTML Conventions (MUST FOLLOW)
- Always `from fasthtml.common import *`
- Use `app, rt = fast_app(...)` for app initialization
- Use `@rt` decorator for routes; function name = route path
- Use `serve()` at the bottom - never write `if __name__ == "__main__"`
- Return FT components (FastTags) from route handlers
- Use `cls` for CSS classes (maps to HTML `class`)
- Use `_for` for label `for` attribute
- Use `Titled("Page Title", content...)` when a page title is needed
- Prefer Python over JS; never use React/Vue/Svelte
- Use `Style()` for inline CSS, `Script()` for JS
- Use `Link(rel='stylesheet', href=...)` for external CSS
- Use `Beforeware` for auth/middleware
- Use `APIRouter` to organize routes across files
- Use `fill_form()` to populate forms from objects
- Dataclass type annotations auto-unpack form data
- For file uploads, `Form` defaults to multipart/form-data
- Use `setup_toasts(app)` for toast notifications
- Use `RedirectResponse` for redirects (with status_code=303)
- Sessions via `sess` parameter in handlers
- Auth via `req.scope['auth']` in Beforeware

## Project Structure
```
kanvas/
├── main.py              # FastHTML app entry point
├── models.py            # SQLAlchemy models
├── db.py                # Database connection & session management
├── components/
│   └── layout.py        # Navbar, footer, page wrapper
├── pages/
│   ├── home.py          # Landing page
│   ├── how_it_works.py  # How it works page
│   ├── investors.py     # Investor information
│   ├── artists.py       # Artist/gallery information
│   ├── about.py         # About page
│   └── contact.py       # Contact page
├── admin/
│   ├── __init__.py      # Admin router
│   └── views.py         # Admin CRUD views
├── api/
│   └── routes.py        # API endpoints
├── sql/
│   └── schema.sql       # Database schema DDL
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Database
- Connection: `DB_URL` environment variable
- Schema: `kanvas` in PostgreSQL
- ORM: SQLAlchemy with declarative models
- All tables prefixed with schema: `kanvas.table_name`

## Key Domain Concepts
- **Artworks**: Fine art pieces available for fractional investment
- **Investment Opportunities**: Funding campaigns for artworks
- **Investments**: Individual investor contributions
- **Artists/Galleries**: Creators and institutions consigning works
- **Investors**: People investing in art-backed offerings
- **Repayments**: Revenue distribution from artwork sales
- **Secondary Market**: Trading of fractional positions

## Running Locally
```bash
python main.py  # Starts on port 5001
```

## Docker
```bash
docker compose up --build
```
