from config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.notifications import router as notifications_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

app = FastAPI(title="Notification Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(notifications_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "notification"}
