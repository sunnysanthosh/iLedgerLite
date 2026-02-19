from fastapi import FastAPI

from routers.customers import router as customers_router
from routers.ledger import router as ledger_router

app = FastAPI(title="Ledger Service", version="0.1.0")

app.include_router(customers_router)
app.include_router(ledger_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ledger"}
