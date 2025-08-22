from typing import Dict, List, Tuple

import pandas as pd

from app.database.config import get_db_session
from app.database.models import StoreStatus, MenuHours, StoreTimezone
from app.models.schemas import MenuHourRecord


def load_all_data() -> Tuple[pd.DataFrame, List[MenuHourRecord], Dict[int, str]]:

    session = get_db_session()
    try:
        # Load store status as DataFrame
        print("Loading store status from database...")
        status_query = session.query(StoreStatus).order_by(StoreStatus.store_id, StoreStatus.timestamp_utc)
        status_data = []
        for record in status_query:
            status_data.append({
                'store_id': record.store_id,
                'timestamp_utc': record.timestamp_utc,
                'status': record.status
            })
        status_df = pd.DataFrame(status_data)
        
        # Load menu hours as list of records
        print("Loading menu hours from database...")
        menu_hours_query = session.query(MenuHours)
        menu_hours = []
        for record in menu_hours_query:
            menu_hours.append(MenuHourRecord(
                store_id=record.store_id,  # Keep as string
                day_of_week=record.day_of_week,
                start_time_local=str(record.start_time_local),
                end_time_local=str(record.end_time_local)
            ))
        
        # Load timezones as dictionary
        print("Loading timezones from database...")
        timezone_query = session.query(StoreTimezone)
        timezones = {}
        for record in timezone_query:
            timezones[record.store_id] = record.timezone_str  # Keep as string
        
        print(f"Loaded {len(status_df)} status records, {len(menu_hours)} menu hours, {len(timezones)} timezones")
        return status_df, menu_hours, timezones
        
    finally:
        session.close()


def get_current_time_from_data(status_df: pd.DataFrame) -> pd.Timestamp:
    if len(status_df) == 0:
        return pd.Timestamp.now(tz='UTC')
    return status_df['timestamp_utc'].max()
