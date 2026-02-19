from fastapi import FastAPI

from routers.accounts import router as accounts_router
from routers.categories import router as categories_router
from routers.transactions import router as transactions_router

app = FastAPI(title="Transaction Service", version="0.1.0")

app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(transactions_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "transaction"}
