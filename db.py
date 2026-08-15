import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

DB_URL = os.environ["DB_URL"]
SCHEMA = "kanvas"

engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)

# Set search_path on every new connection
@event.listens_for(engine, "connect")
def set_search_path(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute(f"SET search_path TO {SCHEMA}, public")
    cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create schema and all tables."""
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    _init_chat_tables()


def _init_chat_tables():
    """Create chat and auction tables if they don't exist."""
    ddl = [
        """CREATE TABLE IF NOT EXISTS kanvas.chat_users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS kanvas.chat_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES kanvas.chat_users(id),
            title VARCHAR(255) DEFAULT 'New chat',
            agent_slug VARCHAR(100),
            share_token VARCHAR(64),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS kanvas.chat_messages (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES kanvas.chat_sessions(id),
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            agent_slug VARCHAR(100),
            tool_calls JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS kanvas.ai_content_reports (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES kanvas.chat_users(id) ON DELETE SET NULL,
            session_id INTEGER REFERENCES kanvas.chat_sessions(id) ON DELETE SET NULL,
            reason VARCHAR(100) NOT NULL,
            response_content TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )""",
        # Cross-container dedup for the email digest: the period (e.g. ISO week)
        # is the primary key, so only the first container to INSERT it sends.
        """CREATE TABLE IF NOT EXISTS kanvas.digest_log (
            period VARCHAR(32) PRIMARY KEY,
            sent_at TIMESTAMPTZ DEFAULT NOW(),
            recipients INTEGER
        )""",
        """CREATE TABLE IF NOT EXISTS kanvas.auction_lots (
            id SERIAL PRIMARY KEY,
            auction_date BIGINT NOT NULL,
            author VARCHAR(255) NOT NULL,
            start_price BIGINT NOT NULL,
            end_price BIGINT NOT NULL,
            year BIGINT,
            decade BIGINT,
            tech VARCHAR(255),
            category VARCHAR(100),
            dimension DOUBLE PRECISION,
            auction_provider VARCHAR(100) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )""",
    ]
    migrations = [
        "ALTER TABLE kanvas.auction_lots ADD COLUMN IF NOT EXISTS title VARCHAR(500)",
        "ALTER TABLE kanvas.auction_lots ADD COLUMN IF NOT EXISTS lot_number INTEGER",
        "ALTER TABLE kanvas.auction_lots ADD COLUMN IF NOT EXISTS dimensions_raw VARCHAR(100)",
        "ALTER TABLE kanvas.auction_lots ADD COLUMN IF NOT EXISTS bid_count INTEGER",
        "ALTER TABLE kanvas.auction_lots ADD COLUMN IF NOT EXISTS auction_name VARCHAR(255)",
        "ALTER TABLE kanvas.auction_lots ADD COLUMN IF NOT EXISTS image_url VARCHAR(500)",
        "ALTER TABLE kanvas.auction_lots ADD COLUMN IF NOT EXISTS source_url VARCHAR(500)",
        "ALTER TABLE kanvas.auction_lots ADD COLUMN IF NOT EXISTS sold BOOLEAN DEFAULT TRUE",
        "ALTER TABLE kanvas.auction_lots ALTER COLUMN start_price SET DEFAULT 0",
        "ALTER TABLE kanvas.auction_lots ALTER COLUMN end_price SET DEFAULT 0",
        "CREATE INDEX IF NOT EXISTS idx_auction_lots_source_url ON kanvas.auction_lots(source_url)",
        "ALTER TABLE kanvas.auction_lots ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'",
        "CREATE INDEX IF NOT EXISTS idx_auction_lots_provider ON kanvas.auction_lots(auction_provider)",
        "CREATE INDEX IF NOT EXISTS idx_auction_lots_author ON kanvas.auction_lots(author)",
        "CREATE INDEX IF NOT EXISTS idx_auction_lots_date ON kanvas.auction_lots(auction_date)",
        "CREATE INDEX IF NOT EXISTS idx_auction_lots_end_price ON kanvas.auction_lots(end_price)",
        "CREATE INDEX IF NOT EXISTS idx_auction_lots_status ON kanvas.auction_lots(status)",
        "CREATE INDEX IF NOT EXISTS idx_auction_lots_category ON kanvas.auction_lots(category)",
        "CREATE INDEX IF NOT EXISTS idx_auction_lots_tech ON kanvas.auction_lots(tech)",
        "CREATE INDEX IF NOT EXISTS idx_auction_lots_status_price ON kanvas.auction_lots(status, end_price)",
        # Auth columns on chat_users
        "ALTER TABLE kanvas.chat_users ADD COLUMN IF NOT EXISTS name VARCHAR(255)",
        "ALTER TABLE kanvas.chat_users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)",
        "ALTER TABLE kanvas.chat_users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE",
        "ALTER TABLE kanvas.chat_users ADD COLUMN IF NOT EXISTS verify_token VARCHAR(64)",
        "ALTER TABLE kanvas.chat_users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(64)",
        "ALTER TABLE kanvas.chat_users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMPTZ",
        # Widen country column for full country names
        "ALTER TABLE kanvas.user_profiles ALTER COLUMN country TYPE VARCHAR(100)",
        # User profiles table
        f"""CREATE TABLE IF NOT EXISTS {SCHEMA}.user_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES {SCHEMA}.chat_users(id) ON DELETE CASCADE UNIQUE,
            phone VARCHAR(30),
            country VARCHAR(100),
            city VARCHAR(100),
            currency VARCHAR(3) DEFAULT 'EUR',
            language VARCHAR(5) DEFAULT 'en',
            budget_min_eur NUMERIC(12,2),
            budget_max_eur NUMERIC(12,2),
            preferred_mediums JSONB DEFAULT '[]',
            preferred_periods JSONB DEFAULT '[]',
            preferred_auction_houses JSONB DEFAULT '[]',
            preferred_countries JSONB DEFAULT '[]',
            min_year INTEGER,
            max_year INTEGER,
            notify_new_results BOOLEAN DEFAULT TRUE,
            notify_price_alerts BOOLEAN DEFAULT TRUE,
            notify_weekly_digest BOOLEAN DEFAULT TRUE,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )""",
    ]
    with engine.connect() as conn:
        for stmt in ddl:
            conn.execute(text(stmt))
        for stmt in migrations:
            conn.execute(text(stmt))
        conn.commit()
