"""
Simple database configuration using Neon PostgreSQL (serverless).
The connection string points to a cloud-hosted Neon database.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.database.models import Base

# Load environment variables from .env file
load_dotenv()

# Neon PostgreSQL serverless database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please check your .env file.")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Get a database session."""
    return SessionLocal()
