from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.report import router as report_router
from app.api.polling import router as polling_router

app = FastAPI(title="Store Monitoring Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router)
app.include_router(polling_router, prefix="/polling", tags=["polling"])
