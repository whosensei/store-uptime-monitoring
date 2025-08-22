from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from app.services.polling_service import polling_service

router = APIRouter()

@router.post("/start_polling")
async def start_polling(background_tasks: BackgroundTasks):
    if polling_service.is_running:
        raise HTTPException(status_code=400, detail="Polling is already running")
    
    background_tasks.add_task(polling_service.start_polling)
    
    return {"message": "Hourly polling started"}


@router.post("/stop_polling")
def stop_polling():
    if not polling_service.is_running:
        raise HTTPException(status_code=400, detail="Polling is not running")
    
    polling_service.stop_polling()
    return {"message": "Polling stopped"}


@router.get("/status")
def get_status():
    return {
        "is_running": polling_service.is_running,
        "last_report_id": polling_service.last_report_id,
        "last_check_time": polling_service.last_check_time.isoformat() if polling_service.last_check_time else None
    }


@router.get("/last_report")
def get_last_report():
    if not polling_service.last_report_id:
        return {"message": "No reports generated yet"}
    
    from app.services import report_service
    
    try:
        report_info = report_service.get_report_info(polling_service.last_report_id)
        if not report_info:
            return {"message": "Report not found"}
        
        return {
            "report_id": polling_service.last_report_id,
            "status": report_info.status,
            "generated_at": report_info.timestamp.isoformat() if report_info.timestamp else None
        }
    except Exception as e:
        return {"error": str(e)}
