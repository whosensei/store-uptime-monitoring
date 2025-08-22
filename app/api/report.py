from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from app.models.schemas import TriggerReportResponse
from app.services import report_service

router = APIRouter()


@router.post("/trigger_report", response_model=TriggerReportResponse)
def trigger_report(background_tasks: BackgroundTasks) -> TriggerReportResponse:
    report_id = report_service.trigger_report(background_tasks)
    return TriggerReportResponse(report_id=report_id)


@router.get("/get_report")
def get_report(report_id: str):
    info = report_service.get_report_info(report_id)
    
    if info is None:
        raise HTTPException(status_code=404, detail="report_id not found")

    if info.status == "running":
        return JSONResponse(status_code=200, content={"status": "Running"})

    if info.status == "failed":
        raise HTTPException(status_code=500, detail=info.error_message or "Report generation failed")

    if not info.output_csv_path:
        raise HTTPException(status_code=500, detail="Report file missing")

    headers = {"X-Report-Status": "Complete"}
    return FileResponse(
        path=str(info.output_csv_path), 
        media_type="text/csv", 
        filename="report.csv", 
        headers=headers
    )