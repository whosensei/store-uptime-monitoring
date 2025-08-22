import uuid
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from fastapi import BackgroundTasks

from app.models.schemas import ReportInfo
from app.services.calculator import compute_store_uptime
from app.services.data_loader import get_current_time_from_data, load_all_data

# Simple module-level state
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Global dictionary to track reports
_reports: Dict[str, ReportInfo] = {}


def trigger_report(background_tasks: BackgroundTasks) -> str:
    report_id = str(uuid.uuid4())
    
    report_info = ReportInfo(report_id=report_id, status="running")
    _reports[report_id] = report_info
    
    background_tasks.add_task(generate_report_sync, report_id)
    
    return report_id


def get_report_info(report_id: str) -> Optional[ReportInfo]:
    return _reports.get(report_id)


def generate_report_sync(report_id: str) -> None:
    try:
        status_df, menu_hours, store_timezones = load_all_data()
        
        current_time = get_current_time_from_data(status_df).to_pydatetime()
        
        results = compute_store_uptime(status_df, menu_hours, store_timezones, current_time)
        
        output_path = REPORTS_DIR / f"report_{report_id}.csv"
        _save_results_csv(results, output_path)
        
        _reports[report_id].status = "complete"
        _reports[report_id].output_csv_path = output_path
            
    except Exception as e:
        _reports[report_id].status = "failed"
        _reports[report_id].error_message = str(e)


def _save_results_csv(results, output_path):
    rows = []
    for result in results:
        rows.append({
            "store_id": result.store_id,
            "uptime_last_hour(in minutes)": result.uptime_minutes_1h,
            "uptime_last_day(in hours)": result.uptime_hours_24h,
            "uptime_last_week(in hours)": result.uptime_hours_7d,
            "downtime_last_hour(in minutes)": result.downtime_minutes_1h,
            "downtime_last_day(in hours)": result.downtime_hours_24h,
            "downtime_last_week(in hours)": result.downtime_hours_7d,
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values("store_id")
    df.to_csv(output_path, index=False)