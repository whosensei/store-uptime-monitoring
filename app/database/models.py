"""
SQLAlchemy database models for store monitoring system.
"""
from datetime import time
from sqlalchemy import Column, Integer, String, DateTime, Time, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class StoreStatus(Base):
    """Store status observations - the main time-series table."""
    __tablename__ = "store_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String(50), nullable=False, index=True)  # Changed from UUID for compatibility
    timestamp_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive')", name="status_check"),
        UniqueConstraint("store_id", "timestamp_utc", name="uq_store_status_store_time"),
        Index("idx_store_status_time", "timestamp_utc"),
    )


class MenuHours(Base):
    """Business hours for each store by day of week."""
    __tablename__ = "menu_hours"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String(50), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time_local = Column(Time, nullable=False)
    end_time_local = Column(Time, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="day_of_week_check"),
        Index("idx_menu_hours_store", "store_id"),
    )


class StoreTimezone(Base):
    """Timezone information for each store."""
    __tablename__ = "store_timezones"
    
    store_id = Column(String(50), primary_key=True)
    timezone_str = Column(String(50), nullable=False)
