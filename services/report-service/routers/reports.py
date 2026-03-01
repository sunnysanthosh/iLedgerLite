from datetime import date

from db import get_db
from fastapi import APIRouter, Depends, Query
from models.user import User
from schemas.report import (
    BudgetResponse,
    CashflowResponse,
    ExportResponse,
    ProfitLossResponse,
    SummaryResponse,
)
from services.report_service import (
    export_report,
    get_budget_report,
    get_cashflow,
    get_profit_loss,
    get_summary,
)
from services.security import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/profit-loss", response_model=ProfitLossResponse)
async def profit_loss_endpoint(
    start_date: date = Query(default_factory=lambda: date.today().replace(day=1)),
    end_date: date = Query(default_factory=date.today),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_profit_loss(user.id, start_date, end_date, db)


@router.get("/cashflow", response_model=CashflowResponse)
async def cashflow_endpoint(
    start_date: date = Query(default_factory=lambda: date.today().replace(day=1)),
    end_date: date = Query(default_factory=date.today),
    period: str = Query("monthly", pattern="^(daily|weekly|monthly)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_cashflow(user.id, start_date, end_date, period, db)


@router.get("/budget", response_model=BudgetResponse)
async def budget_endpoint(
    start_date: date = Query(default_factory=lambda: date.today().replace(day=1)),
    end_date: date = Query(default_factory=date.today),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_budget_report(user.id, start_date, end_date, db)


@router.get("/summary", response_model=SummaryResponse)
async def summary_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_summary(user.id, db)


@router.get("/export", response_model=ExportResponse)
async def export_endpoint(
    start_date: date = Query(default_factory=lambda: date.today().replace(day=1)),
    end_date: date = Query(default_factory=date.today),
    format: str = Query("csv", pattern="^(csv)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await export_report(user.id, start_date, end_date, format, db)
