import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.database.config import get_db_session
from app.database.models import StoreStatus
from app.services import report_service

class SimplePollingService:
    
    def __init__(self):
        self.is_running = False
        self.last_report_id = None
        self.last_check_time = None
        
    async def start_polling(self):
        """Start hourly polling loop."""
        self.is_running = True
        self.last_check_time = datetime.now(timezone.utc) - timedelta(hours=1)  # Start from 1 hour ago
        print("Starting hourly polling service...")
        
        while self.is_running:
            try:
                await self._check_for_new_data()
                print("Next check in 1 hour...")
                await asyncio.sleep(3600)  # 1 hour = 3600 seconds
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    def stop_polling(self):
        self.is_running = False
        print("Stopping polling service...")
    
    async def _check_for_new_data(self):
        session = get_db_session()
        try:
            current_time = datetime.now(timezone.utc)
            
            # Count new records since last check
            new_records_count = session.query(StoreStatus).filter(
                StoreStatus.timestamp_utc > self.last_check_time
            ).count()
            
            if new_records_count > 0:
                print(f"Found {new_records_count} new records since last check")
                
                # Generate report
                try:
                    report_id = report_service.trigger_report()
                    self.last_report_id = report_id
                    print(f"Generated report: {report_id}")
                except Exception as e:
                    print(f"Failed to generate report: {e}")
            else:
                print("No new data found")
            
            # Update last check time
            self.last_check_time = current_time
            
        except Exception as e:
            print(f"Error checking for new data: {e}")
        finally:
            session.close()


# Global polling service instance  
polling_service = SimplePollingService()


async def start_polling_background():
    """Start polling in the background."""
    await polling_service.start_polling()


def stop_polling_background():
    """Stop background polling."""
    polling_service.stop_polling()
