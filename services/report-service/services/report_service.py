import csv
import io
import uuid
from datetime import date, timedelta
from decimal import Decimal

from models.account import Account
from models.category import Category
from models.ledger_entry import LedgerEntry
from models.transaction import Transaction
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_profit_loss(
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    db: AsyncSession,
) -> dict:
    """Profit & Loss: income vs expenses by date range with category breakdown."""
    from datetime import datetime, timezone

    start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
    end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)

    # Total income/expense
    totals_result = await db.execute(
        select(
            func.coalesce(
                func.sum(case((Transaction.type == "income", Transaction.amount), else_=Decimal("0.00"))),
                Decimal("0.00"),
            ).label("total_income"),
            func.coalesce(
                func.sum(case((Transaction.type == "expense", Transaction.amount), else_=Decimal("0.00"))),
                Decimal("0.00"),
            ).label("total_expenses"),
        ).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_dt,
            Transaction.transaction_date <= end_dt,
        )
    )
    totals = totals_result.one()

    # Income by category
    income_by_cat = await db.execute(
        select(
            Category.id,
            Category.name,
            func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label("total"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "income",
            Transaction.transaction_date >= start_dt,
            Transaction.transaction_date <= end_dt,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )
    income_categories = [
        {"category_id": str(r.id) if r.id else None, "category_name": r.name or "Uncategorized", "total": str(r.total)}
        for r in income_by_cat.all()
    ]

    # Expense by category
    expense_by_cat = await db.execute(
        select(
            Category.id,
            Category.name,
            func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label("total"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_dt,
            Transaction.transaction_date <= end_dt,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )
    expense_categories = [
        {"category_id": str(r.id) if r.id else None, "category_name": r.name or "Uncategorized", "total": str(r.total)}
        for r in expense_by_cat.all()
    ]

    total_income = totals.total_income
    total_expenses = totals.total_expenses

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_income": str(total_income),
        "total_expenses": str(total_expenses),
        "net_profit": str(total_income - total_expenses),
        "income_by_category": income_categories,
        "expense_by_category": expense_categories,
    }


async def get_cashflow(
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    period: str,
    db: AsyncSession,
) -> dict:
    """Cashflow: inflows and outflows grouped by time period."""
    from datetime import datetime, timezone

    start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
    end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)

    # Fetch all transactions in range
    result = await db.execute(
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_dt,
            Transaction.transaction_date <= end_dt,
        )
        .order_by(Transaction.transaction_date)
    )
    transactions = list(result.scalars().all())

    # Group by period
    period_buckets: dict[str, dict] = {}
    for txn in transactions:
        txn_date = txn.transaction_date.date() if isinstance(txn.transaction_date, datetime) else txn.transaction_date
        if period == "daily":
            bucket_key = txn_date.isoformat()
        elif period == "weekly":
            week_start = txn_date - timedelta(days=txn_date.weekday())
            bucket_key = week_start.isoformat()
        else:  # monthly
            bucket_key = txn_date.strftime("%Y-%m")

        if bucket_key not in period_buckets:
            period_buckets[bucket_key] = {"period": bucket_key, "inflows": Decimal("0.00"), "outflows": Decimal("0.00")}

        if txn.type == "income":
            period_buckets[bucket_key]["inflows"] += txn.amount
        elif txn.type == "expense":
            period_buckets[bucket_key]["outflows"] += txn.amount

    periods_list = []
    total_inflows = Decimal("0.00")
    total_outflows = Decimal("0.00")
    for bucket in sorted(period_buckets.values(), key=lambda x: x["period"]):
        total_inflows += bucket["inflows"]
        total_outflows += bucket["outflows"]
        periods_list.append(
            {
                "period": bucket["period"],
                "inflows": str(bucket["inflows"]),
                "outflows": str(bucket["outflows"]),
                "net": str(bucket["inflows"] - bucket["outflows"]),
            }
        )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "period": period,
        "periods": periods_list,
        "total_inflows": str(total_inflows),
        "total_outflows": str(total_outflows),
        "net_cashflow": str(total_inflows - total_outflows),
    }


async def get_budget_report(
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    db: AsyncSession,
) -> dict:
    """Budget report: spending by category for a date range."""
    from datetime import datetime, timezone

    start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
    end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)

    result = await db.execute(
        select(
            Category.id,
            Category.name,
            func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label("spent"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_dt,
            Transaction.transaction_date <= end_dt,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )

    categories = []
    total_spent = Decimal("0.00")
    for row in result.all():
        total_spent += row.spent
        categories.append(
            {
                "category_id": str(row.id) if row.id else None,
                "category_name": row.name or "Uncategorized",
                "spent": str(row.spent),
                "transaction_count": row.transaction_count,
            }
        )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "categories": categories,
        "total_spent": str(total_spent),
    }


async def get_summary(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Dashboard summary: balances, totals, top categories, outstanding ledger."""
    # Account totals
    acc_result = await db.execute(
        select(
            func.coalesce(func.sum(Account.balance), Decimal("0.00")).label("total_balance"),
            func.count(Account.id).label("account_count"),
        ).where(Account.user_id == user_id, Account.is_active.is_(True))
    )
    acc = acc_result.one()

    # Transaction totals (all time)
    txn_result = await db.execute(
        select(
            func.coalesce(
                func.sum(case((Transaction.type == "income", Transaction.amount), else_=Decimal("0.00"))),
                Decimal("0.00"),
            ).label("total_income"),
            func.coalesce(
                func.sum(case((Transaction.type == "expense", Transaction.amount), else_=Decimal("0.00"))),
                Decimal("0.00"),
            ).label("total_expenses"),
            func.count(Transaction.id).label("transaction_count"),
        ).where(Transaction.user_id == user_id)
    )
    txn = txn_result.one()

    # Top expense categories (top 5)
    top_expense = await db.execute(
        select(
            Category.name,
            func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label("total"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(Transaction.user_id == user_id, Transaction.type == "expense")
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
    )
    top_expense_cats = [{"category_name": r.name or "Uncategorized", "total": str(r.total)} for r in top_expense.all()]

    # Top income categories (top 5)
    top_income = await db.execute(
        select(
            Category.name,
            func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label("total"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(Transaction.user_id == user_id, Transaction.type == "income")
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
    )
    top_income_cats = [{"category_name": r.name or "Uncategorized", "total": str(r.total)} for r in top_income.all()]

    # Outstanding ledger (receivables = debit unsettled, payables = credit unsettled)
    ledger_result = await db.execute(
        select(
            func.coalesce(
                func.sum(case((LedgerEntry.type == "debit", LedgerEntry.amount), else_=Decimal("0.00"))),
                Decimal("0.00"),
            ).label("receivables"),
            func.coalesce(
                func.sum(case((LedgerEntry.type == "credit", LedgerEntry.amount), else_=Decimal("0.00"))),
                Decimal("0.00"),
            ).label("payables"),
        ).where(
            LedgerEntry.user_id == user_id,
            LedgerEntry.is_settled.is_(False),
        )
    )
    ledger = ledger_result.one()

    return {
        "total_balance": str(acc.total_balance),
        "total_income": str(txn.total_income),
        "total_expenses": str(txn.total_expenses),
        "net_profit": str(txn.total_income - txn.total_expenses),
        "transaction_count": txn.transaction_count,
        "account_count": acc.account_count,
        "top_expense_categories": top_expense_cats,
        "top_income_categories": top_income_cats,
        "outstanding_receivables": str(ledger.receivables),
        "outstanding_payables": str(ledger.payables),
    }


async def export_report(
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    report_format: str,
    db: AsyncSession,
) -> dict:
    """Export transactions as CSV."""
    from datetime import datetime, timezone

    start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
    end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)

    result = await db.execute(
        select(
            Transaction.id,
            Transaction.type,
            Transaction.amount,
            Transaction.description,
            Transaction.transaction_date,
            Category.name.label("category_name"),
            Account.name.label("account_name"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .outerjoin(Account, Transaction.account_id == Account.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_dt,
            Transaction.transaction_date <= end_dt,
        )
        .order_by(Transaction.transaction_date.desc())
    )
    rows = result.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Type", "Amount", "Category", "Account", "Description"])
    for row in rows:
        writer.writerow(
            [
                str(row.id),
                row.transaction_date.strftime("%Y-%m-%d") if row.transaction_date else "",
                row.type,
                str(row.amount),
                row.category_name or "Uncategorized",
                row.account_name or "",
                row.description or "",
            ]
        )

    csv_data = output.getvalue()
    filename = f"transactions_{start_date}_{end_date}.csv"

    return {
        "format": "csv",
        "filename": filename,
        "content_type": "text/csv",
        "data": csv_data,
    }
