"""
Simple database configuration using Neon PostgreSQL (serverless).
The connection string points to a cloud-hosted Neon database.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base

# Neon PostgreSQL serverless database connection
DATABASE_URL = "postgresql://neondb_owner:npg_HhsbAqQ3uio1@ep-polished-river-adfy94dl-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Get a database session."""
    return SessionLocal()
