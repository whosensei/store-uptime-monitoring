"""
CSV to database ingestion functions.
"""
from datetime import datetime, time
from pathlib import Path
from typing import List

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.database.config import get_db_session
from app.database.models import StoreStatus, MenuHours, StoreTimezone

# Data file paths
DATA_DIR = Path("files")
DEFAULT_TIMEZONE = "America/Chicago"


def ingest_all_data():
    """
    Ingest all CSV/Excel files into the database.
    This should be run once to populate the database.
    """
    print("Starting data ingestion...")
    
    session = get_db_session()
    try:
        # Clear existing data (for clean re-ingestion)
        print("  Clearing existing data...")
        session.query(StoreStatus).delete()
        session.query(MenuHours).delete() 
        session.query(StoreTimezone).delete()
        
        # Ingest each data source
        ingest_store_status(session)
        ingest_menu_hours(session)
        ingest_store_timezones(session)
        
        session.commit()
        print("Data ingestion completed!")
        
    except Exception as e:
        session.rollback()
        print(f"Error during ingestion: {e}")
        raise
    finally:
        session.close()


def ingest_store_status(session: Session):
    """Ingest store status observations from Excel file (first 50k entries only)."""
    print("  Ingesting store status data (first 50k entries)...")
    
    file_path = DATA_DIR / "store_status.xlsx"
    df = pd.read_excel(file_path, nrows=50000)  # Only read first 50k rows
    df.columns = [c.strip() for c in df.columns]
    
    # Clean the data
    df = df.dropna(subset=["store_id", "timestamp_utc", "status"]).copy()
    df["store_id"] = df["store_id"].astype(str)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    df["status"] = df["status"].astype(str).str.lower()
    df = df[df["status"].isin(["active", "inactive"])]
    
    print(f"    Processing {len(df)} records in batches...")
    
    # Process in batches to avoid transaction size limits
    batch_size = 1000  # Reasonable batch size for 50k records
    total_processed = 0
    
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i + batch_size]
        
        # Convert batch to list of dictionaries
        records = []
        for _, row in batch_df.iterrows():
            records.append({
                "store_id": row["store_id"],
                "timestamp_utc": row["timestamp_utc"].to_pydatetime(),
                "status": row["status"]
            })
        
        # Bulk insert batch using PostgreSQL UPSERT
        if records:
            stmt = insert(StoreStatus).values(records)
            # Skip conflict handling for now to get data loaded
            # stmt = stmt.on_conflict_do_nothing(index_elements=["store_id", "timestamp_utc"])
            session.execute(stmt)
            
        total_processed += len(records)
        print(f"    Batch {i//batch_size + 1}: processed {len(records)} records ({total_processed}/{len(df)} total)")
        
    print(f"    Successfully inserted {total_processed} store status records")


def ingest_menu_hours(session: Session):
    """Ingest business hours from CSV file (first 50k entries)."""
    print("  Ingesting menu hours data (first 50k entries)...")
    
    file_path = DATA_DIR / "menu_hours.csv"
    df = pd.read_csv(file_path, nrows=50000)  # Limit to 50k rows
    df.columns = [c.strip() for c in df.columns]
    
    # Handle different column name formats
    if "dayOfWeek" in df.columns:
        df = df.rename(columns={"dayOfWeek": "day_of_week"})
    
    # Clean the data
    df = df.dropna(subset=["store_id", "day_of_week", "start_time_local", "end_time_local"]).copy()
    df["store_id"] = df["store_id"].astype(str)
    df["day_of_week"] = df["day_of_week"].astype(int)
    
    # Convert to records
    records = []
    for _, row in df.iterrows():
        # Parse time strings (handle different formats)
        start_time = _parse_time_string(row["start_time_local"])
        end_time = _parse_time_string(row["end_time_local"])
        
        if start_time and end_time:
            records.append({
                "store_id": row["store_id"],
                "day_of_week": row["day_of_week"],
                "start_time_local": start_time,
                "end_time_local": end_time
            })
    
    # Bulk insert
    if records:
        stmt = insert(MenuHours).values(records)
        # Skip conflict handling for now to avoid parameter limits
        # stmt = stmt.on_conflict_do_nothing(index_elements=["store_id", "day_of_week", "start_time_local", "end_time_local"])
        session.execute(stmt)
        
    print(f"    Inserted {len(records)} menu hours records")


def ingest_store_timezones(session: Session):
    """Ingest store timezones from CSV file (first 10k entries)."""
    print("  Ingesting timezone data (first 10k entries)...")
    
    file_path = DATA_DIR / "timezones.csv"
    df = pd.read_csv(file_path, nrows=10000)  # Limit to 10k rows
    df.columns = [c.strip() for c in df.columns]
    
    # Handle different column name formats
    if "timezone" in df.columns and "timezone_str" not in df.columns:
        df = df.rename(columns={"timezone": "timezone_str"})
    
    # Clean the data
    df = df.dropna(subset=["store_id"]).copy()
    df["store_id"] = df["store_id"].astype(str)
    df["timezone_str"] = df["timezone_str"].fillna(DEFAULT_TIMEZONE)
    
    # Convert to records
    records = [
        {
            "store_id": row["store_id"],
            "timezone_str": row["timezone_str"]
        }
        for _, row in df.iterrows()
    ]
    
    # Bulk insert
    if records:
        stmt = insert(StoreTimezone).values(records)
        # Skip conflict handling for now to avoid parameter limits  
        # stmt = stmt.on_conflict_do_update(index_elements=["store_id"], set_=dict(timezone_str=stmt.excluded.timezone_str))
        session.execute(stmt)
        
    print(f"    Inserted {len(records)} timezone records")


def _parse_time_string(time_str: str) -> time:
    """Parse time string in various formats to time object."""
    try:
        # Try HH:MM:SS format first
        if len(str(time_str).split(":")) == 3:
            return datetime.strptime(str(time_str), "%H:%M:%S").time()
        # Try HH:MM format
        elif len(str(time_str).split(":")) == 2:
            return datetime.strptime(str(time_str), "%H:%M").time()
        else:
            return None
    except (ValueError, AttributeError):
        return None


# CLI function for running ingestion
if __name__ == "__main__":
    from app.database.config import create_tables
    
    print("Creating database tables...")
    create_tables()
    
    print("Starting data ingestion...")
    ingest_all_data()
