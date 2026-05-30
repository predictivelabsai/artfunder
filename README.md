# Kanvas.ai - AI Art Advisory Platform

AI-powered art advisory combining market intelligence, auction analytics, and collection management for the Estonian and Baltic art market.

![Kanvas.ai Product Tour](docs/kanvas.gif)

## Features

### AI Advisory (8 Specialist Agents)
- **Artist Lookup & Compare** — research and compare Estonian artists
- **Market Analyst & Auction Tracker** — real-time market intelligence from 7 auction houses
- **Acquisition Advisor** — personalized buying recommendations
- **Portfolio Analyst** — collection valuation and tracking
- **Valuator & Provenance Checker** — artwork authentication and pricing

### Art Guru
- AI-powered text RPG — build an art collection as one of 6 characters
- Real Estonian artists and auction data woven into gameplay
- Resource management: gold, knowledge, reputation

### Market Map
- Interactive treemap of 11,000+ auction lots from 7 Estonian galleries
- Price trends by category, artist sales rankings
- Data from Haus, Allee, Vaal, Vernissage, Art&Tonic, E-Kunstisalong (1998-2026)

### Internationalization
- 9 languages: English, Estonian, German, French, Swedish, Latvian, Norwegian, Danish, Polish
- Auto-detection via IP geolocation

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | [FastHTML](https://fastht.ml) (Python) |
| Database | PostgreSQL + SQLAlchemy |
| AI | LangGraph ReAct agents, xAI Grok / OpenAI |
| CSS | Tailwind CSS (Cormorant Garamond + Inter) |
| Scrapers | Playwright (7 Estonian auction galleries) |
| Server | Uvicorn |
| CI/CD | GitHub Actions + Coolify auto-deploy |

## Quick Start

### Local Development

```bash
pip install -r requirements.txt
export DB_URL=postgresql://user:pass@host:5432/dbname
python main.py
# Access at http://localhost:5009
```

### Docker

```bash
docker compose up --build
```

## Project Structure

```
kanvas/
├── main.py                 # App entry point, routes, auth
├── db.py                   # SQLAlchemy engine & session
├── models.py               # Data models
├── components/layout.py    # Navbar, footer, page wrapper
├── pages/                  # Landing pages (home, investors, artists, about, contact)
├── chat/                   # AI chat UI (components, routes, layout, SSE, market map)
├── agents/                 # LangGraph ReAct agents (8 specialists)
├── tools/                  # Agent tools (SQL query, news, auctions, web search)
├── game/                   # Art Guru RPG (engine, prompts, routes)
├── prompts/system/         # Agent system prompts (markdown)
├── scripts/scrapers/       # Playwright scrapers for 7 auction galleries
├── utils/                  # i18n, config, LLM factory, version
├── sql/                    # Schema DDL + schema.json for text-to-SQL
├── admin/                  # Admin CRUD interface
├── api/                    # JSON API endpoints
├── static/                 # CSS, JS
├── .github/workflows/      # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Database

PostgreSQL with `kanvas` schema. Key tables:

- **auction_lots** — 11,000+ lots from 7 providers with prices, artist, technique, dimensions
- **users** — investors, artists, admins
- **artworks** — art pieces with provenance and valuation
- **chat_sessions / chat_messages** — conversation history

## Deployment

CI/CD: push to `main` triggers GitHub Actions, which calls Coolify webhook for auto-deploy (~90s).

Live at [kanvas.ai](https://kanvas.ai)

## License

Proprietary - Predictive Labs AI
