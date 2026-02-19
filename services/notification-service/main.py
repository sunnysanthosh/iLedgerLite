from fastapi import FastAPI

from routers.notifications import router as notifications_router

app = FastAPI(title="Notification Service", version="0.1.0")

app.include_router(notifications_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "notification"}
