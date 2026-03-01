from fastapi import FastAPI
from routers.reports import router as reports_router

app = FastAPI(title="Report Service", version="0.1.0")

app.include_router(reports_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "report"}
