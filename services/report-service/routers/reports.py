from datetime import date

from db import get_db
from fastapi import APIRouter, Depends, Query
from models.org import OrgMembership
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
from services.security import get_org_member
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/profit-loss", response_model=ProfitLossResponse)
async def profit_loss_endpoint(
    start_date: date = Query(default_factory=lambda: date.today().replace(day=1)),
    end_date: date = Query(default_factory=date.today),
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    return await get_profit_loss(membership.org_id, start_date, end_date, db)


@router.get("/cashflow", response_model=CashflowResponse)
async def cashflow_endpoint(
    start_date: date = Query(default_factory=lambda: date.today().replace(day=1)),
    end_date: date = Query(default_factory=date.today),
    period: str = Query("monthly", pattern="^(daily|weekly|monthly)$"),
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    return await get_cashflow(membership.org_id, start_date, end_date, period, db)


@router.get("/budget", response_model=BudgetResponse)
async def budget_endpoint(
    start_date: date = Query(default_factory=lambda: date.today().replace(day=1)),
    end_date: date = Query(default_factory=date.today),
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    return await get_budget_report(membership.org_id, start_date, end_date, db)


@router.get("/summary", response_model=SummaryResponse)
async def summary_endpoint(
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    return await get_summary(membership.org_id, db)


@router.get("/export", response_model=ExportResponse)
async def export_endpoint(
    start_date: date = Query(default_factory=lambda: date.today().replace(day=1)),
    end_date: date = Query(default_factory=date.today),
    format: str = Query("csv", pattern="^(csv)$"),
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    return await export_report(membership.org_id, start_date, end_date, format, db)
