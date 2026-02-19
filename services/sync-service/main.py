from fastapi import FastAPI

from routers.sync import router as sync_router

app = FastAPI(title="Sync Service", version="0.1.0")
app.include_router(sync_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sync"}
