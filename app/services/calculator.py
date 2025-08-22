from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd

from app.models.schemas import MenuHourRecord, WindowResult


def compute_store_uptime(
    status_df: pd.DataFrame,
    menu_hours: List[MenuHourRecord], 
    store_timezones: Dict[str, str],  # UUID string -> timezone
    current_time: datetime
) -> List[WindowResult]:
    """
    Calculate uptime/downtime for each store using simple observation counting.
    This is much simpler than complex interpolation - just count how many
    observations were 'active' vs 'inactive' in each time window and estimate
    uptime as a proportion.
    """
    
    # Get all unique stores from all data sources
    status_stores = set(status_df['store_id'].unique()) if len(status_df) > 0 else set()
    hours_stores = {h.store_id for h in menu_hours}
    tz_stores = set(store_timezones.keys())
    all_stores = status_stores | hours_stores | tz_stores
    
    results = []
    
    # Define time windows (looking backwards from current_time)
    hour_ago = current_time - timedelta(hours=1)
    day_ago = current_time - timedelta(days=1) 
    week_ago = current_time - timedelta(weeks=1)
    
    for store_id in sorted(all_stores):
        # Get this store's data
        store_data = status_df[status_df['store_id'] == store_id].copy()
        
        if len(store_data) == 0:
            # No observations = assume all downtime
            result = WindowResult(
                store_id=store_id,
                uptime_minutes_1h=0, downtime_minutes_1h=60,
                uptime_hours_24h=0.0, downtime_hours_24h=24.0,
                uptime_hours_7d=0.0, downtime_hours_7d=168.0
            )
            results.append(result)
            continue
            
        # Calculate uptime for each window
        uptime_1h, downtime_1h = _calculate_window_uptime(store_data, hour_ago, current_time, 60)
        uptime_1d, downtime_1d = _calculate_window_uptime(store_data, day_ago, current_time, 24 * 60)
        uptime_1w, downtime_1w = _calculate_window_uptime(store_data, week_ago, current_time, 7 * 24 * 60)
        
        result = WindowResult(
            store_id=store_id,
            uptime_minutes_1h=int(uptime_1h),
            downtime_minutes_1h=int(downtime_1h),
            uptime_hours_24h=round(uptime_1d / 60, 2),
            downtime_hours_24h=round(downtime_1d / 60, 2), 
            uptime_hours_7d=round(uptime_1w / 60, 2),
            downtime_hours_7d=round(downtime_1w / 60, 2)
        )
        results.append(result)
    
    return results


def _calculate_window_uptime(store_data: pd.DataFrame, start_time: datetime, end_time: datetime, total_minutes: int):
    """
    Simple uptime calculation: count active vs inactive observations in the window.
    Estimate uptime as proportion of active observations * total window time.
    """
    # Filter data to window
    window_data = store_data[
        (store_data['timestamp_utc'] >= start_time) & 
        (store_data['timestamp_utc'] <= end_time)
    ]
    
    if len(window_data) == 0:
        # No observations in window = assume inactive (conservative estimate)
        return 0, total_minutes
    
    # Count active vs inactive observations
    active_count = len(window_data[window_data['status'] == 'active'])
    total_count = len(window_data)
    
    # Estimate uptime as proportion
    uptime_ratio = active_count / total_count
    uptime_minutes = uptime_ratio * total_minutes
    downtime_minutes = total_minutes - uptime_minutes
    
    return uptime_minutes, downtime_minutes


# TODO: For production, add business hours filtering
# def _filter_to_business_hours(store_data, menu_hours, timezone):
#     """Filter observations to only include business hours"""
#     # This would convert business hours to UTC and filter data
#     # For now, we include all hours (24x7 assumption)
#     return store_data
