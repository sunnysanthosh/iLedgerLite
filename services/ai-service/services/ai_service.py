"""AI service: rule-based categorization, statistical insights, mock OCR."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from models.category import Category
from models.transaction import Transaction
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Keyword → category mapping for rule-based categorization
# ---------------------------------------------------------------------------
KEYWORD_MAP: dict[str, str] = {
    # Income
    "salary": "Salary",
    "paycheck": "Salary",
    "freelance": "Freelance",
    "consulting": "Freelance",
    "interest": "Interest",
    "dividend": "Investments",
    "refund": "Refund",
    "rental income": "Rental Income",
    "rent received": "Rental Income",
    "gift received": "Gifts Received",
    # Expense
    "grocery": "Groceries",
    "groceries": "Groceries",
    "vegetable": "Groceries",
    "supermarket": "Groceries",
    "bigbasket": "Groceries",
    "zepto": "Groceries",
    "rent": "Rent",
    "house rent": "Rent",
    "electricity": "Utilities",
    "water bill": "Utilities",
    "gas bill": "Utilities",
    "internet": "Utilities",
    "wifi": "Utilities",
    "mobile recharge": "Utilities",
    "uber": "Transport",
    "ola": "Transport",
    "petrol": "Transport",
    "diesel": "Transport",
    "metro": "Transport",
    "bus": "Transport",
    "auto": "Transport",
    "train": "Transport",
    "flight": "Transport",
    "restaurant": "Food & Dining",
    "zomato": "Food & Dining",
    "swiggy": "Food & Dining",
    "cafe": "Food & Dining",
    "coffee": "Food & Dining",
    "tea": "Food & Dining",
    "lunch": "Food & Dining",
    "dinner": "Food & Dining",
    "breakfast": "Food & Dining",
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "myntra": "Shopping",
    "shopping": "Shopping",
    "clothes": "Shopping",
    "hospital": "Healthcare",
    "doctor": "Healthcare",
    "medicine": "Healthcare",
    "pharmacy": "Healthcare",
    "medical": "Healthcare",
    "school": "Education",
    "college": "Education",
    "tuition": "Education",
    "course": "Education",
    "udemy": "Education",
    "movie": "Entertainment",
    "netflix": "Entertainment",
    "spotify": "Entertainment",
    "hotstar": "Entertainment",
    "emi": "EMI & Loans",
    "loan": "EMI & Loans",
    "insurance": "Insurance",
    "lic": "Insurance",
    "tax": "Taxes",
    "gst": "Taxes",
    "donation": "Charity",
    "charity": "Charity",
    "gift": "Gifts & Donations",
}


async def categorize_transaction(
    db: AsyncSession,
    user_id: uuid.UUID,
    description: str,
    amount: Decimal,
    txn_type: str,
) -> list[dict]:
    """Return ranked category predictions based on keyword matching."""
    desc_lower = description.lower()

    # Score categories by keyword match
    scored: dict[str, float] = {}
    for keyword, cat_name in KEYWORD_MAP.items():
        if keyword in desc_lower:
            # Longer keyword matches get higher confidence
            score = len(keyword) / max(len(desc_lower), 1)
            if cat_name not in scored or score > scored[cat_name]:
                scored[cat_name] = score

    # If no keyword match, suggest generic categories
    if not scored:
        if txn_type == "income":
            scored = {"Salary": 0.3, "Freelance": 0.2, "Other Income": 0.15}
        else:
            scored = {"Shopping": 0.3, "Food & Dining": 0.2, "Utilities": 0.15}

    # Look up actual category IDs from DB
    cat_names = list(scored.keys())
    result = await db.execute(
        select(Category).where(
            Category.name.in_(cat_names),
            (Category.user_id == user_id) | (Category.user_id.is_(None)),
        )
    )
    categories = {c.name: c for c in result.scalars().all()}

    # Build sorted predictions
    predictions = []
    for name, confidence in sorted(scored.items(), key=lambda x: -x[1]):
        cat = categories.get(name)
        predictions.append(
            {
                "category_id": cat.id if cat else None,
                "category_name": name,
                "confidence": round(min(confidence + 0.3, 0.95), 2),
            }
        )

    return predictions[:5]


async def get_spending_insights(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> dict:
    """Compute spending anomalies, trends, and top categories for the user."""
    now = datetime.now(timezone.utc)
    last_30 = now - timedelta(days=30)
    prev_30 = last_30 - timedelta(days=30)

    # Last 30 days by category
    last_30_query = (
        select(
            Category.name,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= last_30,
        )
        .group_by(Category.name)
    )
    last_30_result = await db.execute(last_30_query)
    last_30_data = {row.name: row.total for row in last_30_result}

    # Previous 30 days by category
    prev_30_query = (
        select(
            Category.name,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= prev_30,
            Transaction.transaction_date < last_30,
        )
        .group_by(Category.name)
    )
    prev_30_result = await db.execute(prev_30_query)
    prev_30_data = {row.name: row.total for row in prev_30_result}

    # Anomalies: categories where spending deviated significantly
    anomalies = []
    for cat_name, current in last_30_data.items():
        previous = prev_30_data.get(cat_name, Decimal("0"))
        if previous > 0:
            deviation = float((current - previous) / previous)
            if abs(deviation) > 0.5:  # >50% change
                anomalies.append(
                    {
                        "category_name": cat_name,
                        "current_amount": str(current),
                        "average_amount": str(previous),
                        "deviation": round(deviation, 2),
                    }
                )

    # Trends
    trends = []
    all_cats = set(last_30_data.keys()) | set(prev_30_data.keys())
    for cat_name in all_cats:
        current = last_30_data.get(cat_name, Decimal("0"))
        previous = prev_30_data.get(cat_name, Decimal("0"))
        if current > previous:
            trend = "increasing"
        elif current < previous:
            trend = "decreasing"
        else:
            trend = "stable"
        trends.append(
            {
                "category_name": cat_name,
                "trend": trend,
                "last_30_days": str(current),
                "previous_30_days": str(previous),
            }
        )

    # Top categories (last 30 days)
    top_categories = sorted(
        [{"name": k, "amount": str(v)} for k, v in last_30_data.items()],
        key=lambda x: Decimal(x["amount"]),
        reverse=True,
    )[:5]

    # Totals
    income_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == "income",
            Transaction.transaction_date >= last_30,
        )
    )
    total_income = income_result.scalar()

    expense_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= last_30,
        )
    )
    total_expense = expense_result.scalar()

    return {
        "anomalies": anomalies,
        "trends": trends,
        "top_categories": top_categories,
        "total_income_30d": str(total_income),
        "total_expense_30d": str(total_expense),
    }


def mock_ocr(image_base64: str, filename: str | None) -> dict:
    """Return mock OCR extraction — stub for future real implementation."""
    return {
        "merchant": "Star Bazaar Supermarket",
        "amount": "1249.00",
        "date": "2025-01-15",
        "items": [
            {"name": "Rice 5kg", "amount": "450.00"},
            {"name": "Oil 1L", "amount": "185.00"},
            {"name": "Vegetables", "amount": "320.00"},
            {"name": "Dairy", "amount": "294.00"},
        ],
        "raw_text": "STAR BAZAAR SUPERMARKET\nDate: 15-Jan-2025\nRice 5kg  450.00\nOil 1L  185.00\nVegetables  320.00\nDairy  294.00\nTOTAL  1249.00",
        "confidence": 0.85,
    }
