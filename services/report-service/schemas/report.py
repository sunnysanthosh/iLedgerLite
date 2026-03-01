import uuid
from datetime import date

from pydantic import BaseModel


class ProfitLossResponse(BaseModel):
    start_date: date
    end_date: date
    total_income: str = "0.00"
    total_expenses: str = "0.00"
    net_profit: str = "0.00"
    income_by_category: list[dict]
    expense_by_category: list[dict]


class CashflowResponse(BaseModel):
    start_date: date
    end_date: date
    period: str  # "daily", "weekly", "monthly"
    periods: list[dict]
    total_inflows: str = "0.00"
    total_outflows: str = "0.00"
    net_cashflow: str = "0.00"


class BudgetCategoryItem(BaseModel):
    category_id: uuid.UUID | None
    category_name: str
    spent: str = "0.00"
    transaction_count: int = 0


class BudgetResponse(BaseModel):
    start_date: date
    end_date: date
    categories: list[BudgetCategoryItem]
    total_spent: str = "0.00"


class SummaryResponse(BaseModel):
    total_balance: str = "0.00"
    total_income: str = "0.00"
    total_expenses: str = "0.00"
    net_profit: str = "0.00"
    transaction_count: int = 0
    account_count: int = 0
    top_expense_categories: list[dict]
    top_income_categories: list[dict]
    outstanding_receivables: str = "0.00"
    outstanding_payables: str = "0.00"


class ExportResponse(BaseModel):
    format: str
    filename: str
    content_type: str
    data: str  # base64-encoded or CSV text
