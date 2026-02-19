from fastapi import FastAPI

from routers.ai import router as ai_router

app = FastAPI(title="AI Service", version="0.1.0")
app.include_router(ai_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai"}
