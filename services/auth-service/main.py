from config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware import TraceIDMiddleware, configure_logging
from routers.auth import router as auth_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

configure_logging()
app = FastAPI(title="Auth Service", version="0.1.0")

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
app.add_middleware(TraceIDMiddleware)

app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth"}
