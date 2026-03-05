# Kanvas.ai - Fine Art Investment Platform

A fractional art investment platform connecting investors with museum-quality artworks. Built with FastHTML, SQLAlchemy, and PostgreSQL.

## Features

### For Investors
- Browse blue-chip art investment opportunities
- Fractional ownership of museum-quality artworks
- Secondary market for trading positions
- Historical appreciation avg. 13.8% p.a.
- Minimum investment from $500
- Portfolio dashboard and tracking

### For Artists & Galleries
- Consign artworks to reach new collectors
- Eligible categories: Paintings, Sculpture, Photography, Prints, Mixed Media
- Professional valuation and authentication
- Climate-controlled, insured storage

### Platform
- Full admin interface at `/admin` with CRUD for all models
- JSON API at `/api/*`
- Session-based authentication
- Mobile-responsive design
- Health check endpoint

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | [FastHTML](https://fastht.ml) (Python) |
| Database | PostgreSQL + SQLAlchemy |
| CSS | Tailwind CSS (Cormorant Garamond + Inter) |
| Server | Uvicorn |
| Deployment | Docker / Docker Compose / Coolify |

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DB_URL=postgresql://user:pass@host:5432/dbname

# Run the app
python main.py
# Access at http://localhost:5009
```

### Docker

```bash
docker compose up --build
# Access at http://localhost:5009
```

### Default Admin

- URL: `http://localhost:5009/admin`
- Email: `admin@kanvas.ai`
- Password: `admin123`

## Project Structure

```
kanvas/
├── main.py                 # App entry point, routes, auth
├── db.py                   # SQLAlchemy engine & session
├── models.py               # Data models (Artwork, Investment, etc.)
├── components/
│   └── layout.py           # Design system, nav, footer
├── pages/
│   ├── home.py             # Landing page
│   ├── how_it_works.py     # Process explanation
│   ├── investors.py        # Investor info
│   ├── artists.py          # Artist/gallery info
│   ├── about.py            # About page
│   └── contact.py          # Contact page
├── admin/
│   └── views.py            # Admin CRUD interface
├── api/
│   └── routes.py           # JSON API endpoints
├── sql/
│   └── schema.sql          # Full database DDL
├── tasks/
│   └── seed_artworks.py    # Seed sample artworks & FAQs
├── tests/
│   └── test_api_endpoints.py
├── Dockerfile              # Production container
├── docker-compose.yml      # Docker stack
└── requirements.txt        # Python dependencies
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/stats` | Platform statistics |
| `GET /api/artworks` | List active artworks |
| `GET /api/artworks/{id}` | Artwork details |
| `GET /api/opportunities` | Open investment opportunities |
| `GET /api/opportunities/{id}` | Opportunity details |
| `GET /api/faqs` | Active FAQs |

## Database

The app uses PostgreSQL with a dedicated `kanvas` schema. Tables are auto-created on startup via SQLAlchemy, or you can apply the DDL manually:

```bash
psql -h host -U user -d dbname -f sql/schema.sql
```

### Models

- **User** - Investors, artists, admins
- **Gallery** - Galleries and dealers
- **Artwork** - Art pieces with provenance and valuation
- **InvestmentOpportunity** - Fractional ownership campaigns
- **Investment** - Individual investments
- **ProjectUpdate** - Valuation and status updates
- **Repayment** - Return distributions
- **Dividend** - Dividend payments
- **Payment** - Transaction records
- **SecondaryMarket** - Position trading
- **AutoInvest** - Automated investing rules
- **InvestorVoting / UserVote** - Governance
- **Notification** - User notifications
- **FAQ** - Platform FAQs

## Deployment (Coolify)

1. Connect the GitHub repo in Coolify
2. Set build pack to **Dockerfile**
3. Set environment variables:
   - `DB_URL` - PostgreSQL connection string
   - `PORT` - Server port (default: 5009)
4. Deploy

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_URL` | *(required)* | PostgreSQL connection string |
| `PORT` | `5009` | Server port |

## License

Proprietary - Predictive Labs AI
