#!/usr/bin/env python3
"""
Database Setup with SQLAlchemy - Simple and Clean!

This script handles everything with pure SQLAlchemy:
- Creates tables from models
- Ingests CSV/Excel data

No migration complexity - perfect for this project!

Usage:
    python setup_database.py
    python setup_database.py --reset  # Reset entire database
"""
import sys
from pathlib import Path

# Add the app to the path
sys.path.append(str(Path(__file__).parent))

from app.database.config import create_tables, get_db_session
from app.database.ingestion import ingest_all_data
from app.database.models import StoreStatus, MenuHours, StoreTimezone


def main():
    """Run the simplified database setup - no migrations needed!"""
    print("Store Monitoring - SIMPLE Database Setup")
    print("=" * 50)
    
    try:
        # Step 1: Create tables directly with SQLAlchemy
        print("\n1. Creating database tables (SQLAlchemy direct)...")
        create_tables()
        print("   Tables created successfully!")
        
        # Step 2: Ingest data
        print("\n2. Ingesting data from CSV/Excel files...")
        ingest_all_data()
        print("   Data ingestion completed!")
        
        # Step 3: Verify data
        print("\n3. Verifying data...")
        verify_data()
        print("   Data verification completed!")
        
        print("\nDatabase setup completed successfully!")
        print("\nTo run the API server:")
        print("   uvicorn app.main:app --reload")
        
        print("\nPure SQLAlchemy setup - no migration complexity!")
        
    except Exception as e:
        print(f"\nError during setup: {e}")
        print("\nTroubleshooting:")
        print("   1. Check internet connection (connecting to Neon cloud)")
        print("   2. Verify DATABASE_URL in app/database/config.py")
        print("   3. Ensure CSV files are in the 'files/' directory")
        print("   4. Check if Neon project is accessible")
        sys.exit(1)


def verify_data():
    """Verify that data was loaded correctly."""
    session = get_db_session()
    try:
        # Count records in each table
        status_count = session.query(StoreStatus).count()
        hours_count = session.query(MenuHours).count()
        timezone_count = session.query(StoreTimezone).count()
        
        print(f"   Store Status Records: {status_count:,}")
        print(f"   Menu Hours Records: {hours_count:,}")
        print(f"   Timezone Records: {timezone_count:,}")
        
        if status_count == 0:
            raise Exception("No store status records found! Check the Excel file.")
        if timezone_count == 0:
            raise Exception("No timezone records found! Check the CSV file.")
        
        # Sample some data
        sample_status = session.query(StoreStatus).first()
        if sample_status:
            print(f"   Sample Status: Store {sample_status.store_id} was {sample_status.status} at {sample_status.timestamp_utc}")
    finally:
        session.close()


def reset_database():
    """Reset the entire database - useful for testing."""
    print("Resetting database...")
    # Note: We don't have drop_tables in simplified config
    # Just re-run the ingestion which clears and reloads data
    ingest_all_data()
    print("Database reset completed!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database()
    else:
        main()
