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
    ]
    with engine.connect() as conn:
        for stmt in ddl:
            conn.execute(text(stmt))
        for stmt in migrations:
            conn.execute(text(stmt))
        conn.commit()
