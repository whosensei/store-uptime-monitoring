from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel

class TriggerReportResponse(BaseModel):
    report_id: str


@dataclass 
class ReportInfo:
    report_id: str
    status: Literal["running", "complete", "failed"]
    output_csv_path: Optional[Path] = None
    error_message: Optional[str] = None


class MenuHourRecord(BaseModel):
    store_id: str  # UUID string
    day_of_week: int  # 0=Monday .. 6=Sunday
    start_time_local: str  # HH:MM:SS
    end_time_local: str  # HH:MM:SS


class WindowResult(BaseModel):
    store_id: str  # UUID string
    uptime_minutes_1h: int
    downtime_minutes_1h: int
    uptime_hours_24h: float
    downtime_hours_24h: float
    uptime_hours_7d: float
    downtime_hours_7d: float
