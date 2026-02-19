"""
LedgerLite Comprehensive Seed Data — Central Source of Truth

This module provides deterministic, realistic test data for all LedgerLite services.
It has ZERO dependencies on any service code (only stdlib + python-jose).

Usage:
    from shared.test_data import USERS, ACCOUNTS, TRANSACTIONS, make_access_token
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from jose import jwt

# ---------------------------------------------------------------------------
# Anchor date: all relative dates computed from here for determinism.
# In tests, ANCHOR_DATE = today; in SQL seeds, use NOW().
# ---------------------------------------------------------------------------
ANCHOR_DATE = date.today()

def _days_ago(n: int) -> datetime:
    """Return a timezone-aware datetime N days before ANCHOR_DATE at 10:00 UTC."""
    return datetime(
        ANCHOR_DATE.year, ANCHOR_DATE.month, ANCHOR_DATE.day,
        10, 0, 0, tzinfo=timezone.utc
    ) - timedelta(days=n)

def _date_ago(n: int) -> date:
    """Return a date N days before ANCHOR_DATE."""
    return ANCHOR_DATE - timedelta(days=n)

def _date_ahead(n: int) -> date:
    """Return a date N days after ANCHOR_DATE."""
    return ANCHOR_DATE + timedelta(days=n)

# ---------------------------------------------------------------------------
# JWT settings (must match service configs)
# ---------------------------------------------------------------------------
JWT_SECRET = "dev-secret-change-in-production"
JWT_ALGORITHM = "HS256"
BCRYPT_HASH = "$2b$12$vktf4/uFra5w.a5Vfs2zruxPOsKG.pAi.TerBws56jabdHu/B6zPa"  # Test@12345
RAW_PASSWORD = "Test@12345"

# ---------------------------------------------------------------------------
# Deterministic UUIDs
# ---------------------------------------------------------------------------

# Users: 00000000-0000-4000-a000-00000000000X
USER_PRIYA_ID    = "00000000-0000-4000-a000-000000000001"
USER_RAJESH_ID   = "00000000-0000-4000-a000-000000000002"
USER_ANITA_ID    = "00000000-0000-4000-a000-000000000003"
USER_VIKRAM_ID   = "00000000-0000-4000-a000-000000000004"
USER_MEENA_ID    = "00000000-0000-4000-a000-000000000005"
USER_ARJUN_ID    = "00000000-0000-4000-a000-000000000006"

# User Settings: 00000000-0000-4000-a100-00000000000X
SETTINGS_PRIYA_ID  = "00000000-0000-4000-a100-000000000001"
SETTINGS_RAJESH_ID = "00000000-0000-4000-a100-000000000002"
SETTINGS_ANITA_ID  = "00000000-0000-4000-a100-000000000003"
SETTINGS_VIKRAM_ID = "00000000-0000-4000-a100-000000000004"
SETTINGS_MEENA_ID  = "00000000-0000-4000-a100-000000000005"
SETTINGS_ARJUN_ID  = "00000000-0000-4000-a100-000000000006"

# Accounts: 00000000-0000-4000-b000-0000000000XX
ACCOUNT_PRIYA_CASH_ID       = "00000000-0000-4000-b000-000000000001"
ACCOUNT_PRIYA_SBI_ID        = "00000000-0000-4000-b000-000000000002"
ACCOUNT_PRIYA_HDFC_CC_ID    = "00000000-0000-4000-b000-000000000003"
ACCOUNT_RAJESH_SHOP_CASH_ID = "00000000-0000-4000-b000-000000000004"
ACCOUNT_RAJESH_ICICI_ID     = "00000000-0000-4000-b000-000000000005"
ACCOUNT_RAJESH_PAYTM_ID     = "00000000-0000-4000-b000-000000000006"
ACCOUNT_ANITA_CASH_ID       = "00000000-0000-4000-b000-000000000007"
ACCOUNT_ANITA_KOTAK_ID      = "00000000-0000-4000-b000-000000000008"
ACCOUNT_ANITA_LOAN_ID       = "00000000-0000-4000-b000-000000000009"
ACCOUNT_VIKRAM_CASH_ID      = "00000000-0000-4000-b000-000000000010"
ACCOUNT_MEENA_BANK_ID       = "00000000-0000-4000-b000-000000000011"
ACCOUNT_ARJUN_WALLET_ID     = "00000000-0000-4000-b000-000000000012"

# System Categories: 00000000-0000-4000-c100-0000000000XX (01-29)
CAT_SALARY_ID           = "00000000-0000-4000-c100-000000000001"
CAT_FREELANCE_ID        = "00000000-0000-4000-c100-000000000002"
CAT_BUSINESS_INCOME_ID  = "00000000-0000-4000-c100-000000000003"
CAT_INVESTMENT_ID       = "00000000-0000-4000-c100-000000000004"
CAT_RENTAL_INCOME_ID    = "00000000-0000-4000-c100-000000000005"
CAT_GIFT_RECEIVED_ID    = "00000000-0000-4000-c100-000000000006"
CAT_REFUND_ID           = "00000000-0000-4000-c100-000000000007"
CAT_OTHER_INCOME_ID     = "00000000-0000-4000-c100-000000000008"
CAT_FOOD_DINING_ID      = "00000000-0000-4000-c100-000000000009"
CAT_GROCERIES_ID        = "00000000-0000-4000-c100-000000000010"
CAT_TRANSPORT_ID        = "00000000-0000-4000-c100-000000000011"
CAT_FUEL_ID             = "00000000-0000-4000-c100-000000000012"
CAT_RENT_ID             = "00000000-0000-4000-c100-000000000013"
CAT_UTILITIES_ID        = "00000000-0000-4000-c100-000000000014"
CAT_MOBILE_INTERNET_ID  = "00000000-0000-4000-c100-000000000015"
CAT_SHOPPING_ID         = "00000000-0000-4000-c100-000000000016"
CAT_HEALTHCARE_ID       = "00000000-0000-4000-c100-000000000017"
CAT_EDUCATION_ID        = "00000000-0000-4000-c100-000000000018"
CAT_ENTERTAINMENT_ID    = "00000000-0000-4000-c100-000000000019"
CAT_TRAVEL_ID           = "00000000-0000-4000-c100-000000000020"
CAT_INSURANCE_ID        = "00000000-0000-4000-c100-000000000021"
CAT_EMI_LOAN_ID         = "00000000-0000-4000-c100-000000000022"
CAT_SUBSCRIPTION_ID     = "00000000-0000-4000-c100-000000000023"
CAT_GIFT_DONATION_ID    = "00000000-0000-4000-c100-000000000024"
CAT_TAXES_ID            = "00000000-0000-4000-c100-000000000025"
CAT_MAINTENANCE_ID      = "00000000-0000-4000-c100-000000000026"
CAT_SALARY_EXPENSE_ID   = "00000000-0000-4000-c100-000000000027"
CAT_SUPPLIER_PAYMENT_ID = "00000000-0000-4000-c100-000000000028"
CAT_OTHER_EXPENSE_ID    = "00000000-0000-4000-c100-000000000029"

# Custom Categories: 00000000-0000-4000-c000-00000000000X (01-08)
CAT_CUSTOM_TUITION_ID      = "00000000-0000-4000-c000-000000000001"  # U1 income
CAT_CUSTOM_PET_CARE_ID     = "00000000-0000-4000-c000-000000000002"  # U1 expense
CAT_CUSTOM_COUNTER_SALE_ID = "00000000-0000-4000-c000-000000000003"  # U2 income
CAT_CUSTOM_WHOLESALE_ID    = "00000000-0000-4000-c000-000000000004"  # U2 income
CAT_CUSTOM_PACKAGING_ID    = "00000000-0000-4000-c000-000000000005"  # U2 expense
CAT_CUSTOM_CATERING_ID     = "00000000-0000-4000-c000-000000000006"  # U3 income
CAT_CUSTOM_KITCHEN_ID      = "00000000-0000-4000-c000-000000000007"  # U3 expense
CAT_CUSTOM_COMMISSION_ID   = "00000000-0000-4000-c000-000000000008"  # U3 income

# Transactions: 00000000-0000-4000-d000-0000000000XX (01-55)
TXN_IDS = [f"00000000-0000-4000-d000-{str(i).zfill(12)}" for i in range(1, 56)]

# Customers: 00000000-0000-4000-e000-00000000000X (01-08)
CUST_SURESH_TEXTILES_ID  = "00000000-0000-4000-e000-000000000001"
CUST_LAKSHMI_STORES_ID   = "00000000-0000-4000-e000-000000000002"
CUST_MOHAMMED_TRADERS_ID = "00000000-0000-4000-e000-000000000003"
CUST_DEEPA_FASHIONS_ID   = "00000000-0000-4000-e000-000000000004"
CUST_RAMESH_SWEETS_ID    = "00000000-0000-4000-e000-000000000005"
CUST_KAVITHA_FLOWERS_ID  = "00000000-0000-4000-e000-000000000006"
CUST_PRAKASH_HARDWARE_ID = "00000000-0000-4000-e000-000000000007"
CUST_SUNITA_DAIRY_ID     = "00000000-0000-4000-e000-000000000008"

# Ledger Entries: 00000000-0000-4000-f000-0000000000XX (01-25)
LEDGER_IDS = [f"00000000-0000-4000-f000-{str(i).zfill(12)}" for i in range(1, 26)]

# Receipts: 00000000-0000-4000-f100-00000000000X (01-05)
RECEIPT_IDS = [f"00000000-0000-4000-f100-{str(i).zfill(12)}" for i in range(1, 6)]


# ===========================================================================
# DATA DICTIONARIES
# ===========================================================================

USERS = [
    {
        "id": USER_PRIYA_ID,
        "email": "priya.sharma@example.com",
        "password_hash": BCRYPT_HASH,
        "full_name": "Priya Sharma",
        "phone": "+919876543001",
        "is_active": True,
    },
    {
        "id": USER_RAJESH_ID,
        "email": "rajesh.kumar@example.com",
        "password_hash": BCRYPT_HASH,
        "full_name": "Rajesh Kumar",
        "phone": "+919876543002",
        "is_active": True,
    },
    {
        "id": USER_ANITA_ID,
        "email": "anita.patel@example.com",
        "password_hash": BCRYPT_HASH,
        "full_name": "Anita Patel",
        "phone": "+919876543003",
        "is_active": True,
    },
    {
        "id": USER_VIKRAM_ID,
        "email": "vikram.singh@example.com",
        "password_hash": BCRYPT_HASH,
        "full_name": "Vikram Singh",
        "phone": "+919876543004",
        "is_active": True,
    },
    {
        "id": USER_MEENA_ID,
        "email": "meena.reddy@example.com",
        "password_hash": BCRYPT_HASH,
        "full_name": "Meena Reddy",
        "phone": "+919876543005",
        "is_active": False,  # Inactive user edge case
    },
    {
        "id": USER_ARJUN_ID,
        "email": "arjun.nair@example.com",
        "password_hash": BCRYPT_HASH,
        "full_name": "Arjun Nair",
        "phone": None,  # No phone edge case
        "is_active": True,
    },
]

USER_SETTINGS = [
    {
        "id": SETTINGS_PRIYA_ID,
        "user_id": USER_PRIYA_ID,
        "account_type": "personal",
        "currency": "INR",
        "language": "en",
        "business_category": None,
        "notifications_enabled": True,
        "onboarding_completed": True,
    },
    {
        "id": SETTINGS_RAJESH_ID,
        "user_id": USER_RAJESH_ID,
        "account_type": "business",
        "currency": "INR",
        "language": "en",
        "business_category": "retail",
        "notifications_enabled": True,
        "onboarding_completed": True,
    },
    {
        "id": SETTINGS_ANITA_ID,
        "user_id": USER_ANITA_ID,
        "account_type": "both",
        "currency": "INR",
        "language": "en",
        "business_category": "food_services",
        "notifications_enabled": True,
        "onboarding_completed": True,
    },
    {
        "id": SETTINGS_VIKRAM_ID,
        "user_id": USER_VIKRAM_ID,
        "account_type": "personal",  # Default; onboarding not completed
        "currency": "INR",
        "language": "en",
        "business_category": None,
        "notifications_enabled": True,
        "onboarding_completed": False,  # Not onboarded edge case
    },
    {
        "id": SETTINGS_MEENA_ID,
        "user_id": USER_MEENA_ID,
        "account_type": "personal",
        "currency": "INR",
        "language": "en",
        "business_category": None,
        "notifications_enabled": False,
        "onboarding_completed": True,
    },
    {
        "id": SETTINGS_ARJUN_ID,
        "user_id": USER_ARJUN_ID,
        "account_type": "personal",
        "currency": "USD",  # USD user edge case
        "language": "en",
        "business_category": None,
        "notifications_enabled": True,
        "onboarding_completed": True,
    },
]

ACCOUNTS = [
    # Priya (U1) — 3 accounts
    {
        "id": ACCOUNT_PRIYA_CASH_ID,
        "user_id": USER_PRIYA_ID,
        "name": "Cash",
        "type": "cash",
        "currency": "INR",
        "balance": Decimal("15000.00"),
        "is_active": True,
    },
    {
        "id": ACCOUNT_PRIYA_SBI_ID,
        "user_id": USER_PRIYA_ID,
        "name": "SBI Savings",
        "type": "bank",
        "currency": "INR",
        "balance": Decimal("85000.50"),
        "is_active": True,
    },
    {
        "id": ACCOUNT_PRIYA_HDFC_CC_ID,
        "user_id": USER_PRIYA_ID,
        "name": "HDFC Credit Card",
        "type": "credit_card",
        "currency": "INR",
        "balance": Decimal("-12500.00"),  # Negative balance edge case
        "is_active": True,
    },
    # Rajesh (U2) — 3 accounts
    {
        "id": ACCOUNT_RAJESH_SHOP_CASH_ID,
        "user_id": USER_RAJESH_ID,
        "name": "Shop Cash Register",
        "type": "cash",
        "currency": "INR",
        "balance": Decimal("28000.00"),
        "is_active": True,
    },
    {
        "id": ACCOUNT_RAJESH_ICICI_ID,
        "user_id": USER_RAJESH_ID,
        "name": "ICICI Current Account",
        "type": "bank",
        "currency": "INR",
        "balance": Decimal("150000.00"),
        "is_active": True,
    },
    {
        "id": ACCOUNT_RAJESH_PAYTM_ID,
        "user_id": USER_RAJESH_ID,
        "name": "Paytm Wallet",
        "type": "wallet",
        "currency": "INR",
        "balance": Decimal("5000.00"),
        "is_active": True,
    },
    # Anita (U3) — 3 accounts
    {
        "id": ACCOUNT_ANITA_CASH_ID,
        "user_id": USER_ANITA_ID,
        "name": "Personal Cash",
        "type": "cash",
        "currency": "INR",
        "balance": Decimal("8000.00"),
        "is_active": True,
    },
    {
        "id": ACCOUNT_ANITA_KOTAK_ID,
        "user_id": USER_ANITA_ID,
        "name": "Kotak Business Account",
        "type": "bank",
        "currency": "INR",
        "balance": Decimal("45000.00"),
        "is_active": True,
    },
    {
        "id": ACCOUNT_ANITA_LOAN_ID,
        "user_id": USER_ANITA_ID,
        "name": "Home Loan",
        "type": "loan",
        "currency": "INR",
        "balance": Decimal("-500000.00"),  # Large negative balance
        "is_active": True,
    },
    # Vikram (U4) — 1 account
    {
        "id": ACCOUNT_VIKRAM_CASH_ID,
        "user_id": USER_VIKRAM_ID,
        "name": "Cash",
        "type": "cash",
        "currency": "INR",
        "balance": Decimal("3000.00"),
        "is_active": True,
    },
    # Meena (U5) — 1 account (inactive user)
    {
        "id": ACCOUNT_MEENA_BANK_ID,
        "user_id": USER_MEENA_ID,
        "name": "Canara Bank Savings",
        "type": "bank",
        "currency": "INR",
        "balance": Decimal("20000.00"),
        "is_active": False,  # Inactive account
    },
    # Arjun (U6) — 1 account (USD)
    {
        "id": ACCOUNT_ARJUN_WALLET_ID,
        "user_id": USER_ARJUN_ID,
        "name": "USD Wallet",
        "type": "wallet",
        "currency": "USD",  # Non-INR currency
        "balance": Decimal("500.00"),
        "is_active": True,
    },
]

# ---------------------------------------------------------------------------
# System Categories (29) — matches categories.sql but with deterministic UUIDs
# ---------------------------------------------------------------------------
SYSTEM_CATEGORIES = [
    # Income (8)
    {"id": CAT_SALARY_ID, "user_id": None, "name": "Salary", "type": "income", "icon": "briefcase", "is_system": True},
    {"id": CAT_FREELANCE_ID, "user_id": None, "name": "Freelance", "type": "income", "icon": "laptop", "is_system": True},
    {"id": CAT_BUSINESS_INCOME_ID, "user_id": None, "name": "Business Income", "type": "income", "icon": "store", "is_system": True},
    {"id": CAT_INVESTMENT_ID, "user_id": None, "name": "Investment Returns", "type": "income", "icon": "trending-up", "is_system": True},
    {"id": CAT_RENTAL_INCOME_ID, "user_id": None, "name": "Rental Income", "type": "income", "icon": "home", "is_system": True},
    {"id": CAT_GIFT_RECEIVED_ID, "user_id": None, "name": "Gift Received", "type": "income", "icon": "gift", "is_system": True},
    {"id": CAT_REFUND_ID, "user_id": None, "name": "Refund", "type": "income", "icon": "rotate-ccw", "is_system": True},
    {"id": CAT_OTHER_INCOME_ID, "user_id": None, "name": "Other Income", "type": "income", "icon": "plus-circle", "is_system": True},
    # Expense (21)
    {"id": CAT_FOOD_DINING_ID, "user_id": None, "name": "Food & Dining", "type": "expense", "icon": "utensils", "is_system": True},
    {"id": CAT_GROCERIES_ID, "user_id": None, "name": "Groceries", "type": "expense", "icon": "shopping-cart", "is_system": True},
    {"id": CAT_TRANSPORT_ID, "user_id": None, "name": "Transport", "type": "expense", "icon": "car", "is_system": True},
    {"id": CAT_FUEL_ID, "user_id": None, "name": "Fuel", "type": "expense", "icon": "fuel", "is_system": True},
    {"id": CAT_RENT_ID, "user_id": None, "name": "Rent", "type": "expense", "icon": "home", "is_system": True},
    {"id": CAT_UTILITIES_ID, "user_id": None, "name": "Utilities", "type": "expense", "icon": "zap", "is_system": True},
    {"id": CAT_MOBILE_INTERNET_ID, "user_id": None, "name": "Mobile & Internet", "type": "expense", "icon": "smartphone", "is_system": True},
    {"id": CAT_SHOPPING_ID, "user_id": None, "name": "Shopping", "type": "expense", "icon": "shopping-bag", "is_system": True},
    {"id": CAT_HEALTHCARE_ID, "user_id": None, "name": "Healthcare", "type": "expense", "icon": "heart", "is_system": True},
    {"id": CAT_EDUCATION_ID, "user_id": None, "name": "Education", "type": "expense", "icon": "book", "is_system": True},
    {"id": CAT_ENTERTAINMENT_ID, "user_id": None, "name": "Entertainment", "type": "expense", "icon": "film", "is_system": True},
    {"id": CAT_TRAVEL_ID, "user_id": None, "name": "Travel", "type": "expense", "icon": "map", "is_system": True},
    {"id": CAT_INSURANCE_ID, "user_id": None, "name": "Insurance", "type": "expense", "icon": "shield", "is_system": True},
    {"id": CAT_EMI_LOAN_ID, "user_id": None, "name": "EMI / Loan Payment", "type": "expense", "icon": "credit-card", "is_system": True},
    {"id": CAT_SUBSCRIPTION_ID, "user_id": None, "name": "Subscription", "type": "expense", "icon": "repeat", "is_system": True},
    {"id": CAT_GIFT_DONATION_ID, "user_id": None, "name": "Gift / Donation", "type": "expense", "icon": "gift", "is_system": True},
    {"id": CAT_TAXES_ID, "user_id": None, "name": "Taxes", "type": "expense", "icon": "file-text", "is_system": True},
    {"id": CAT_MAINTENANCE_ID, "user_id": None, "name": "Maintenance", "type": "expense", "icon": "tool", "is_system": True},
    {"id": CAT_SALARY_EXPENSE_ID, "user_id": None, "name": "Salary Expense", "type": "expense", "icon": "users", "is_system": True},
    {"id": CAT_SUPPLIER_PAYMENT_ID, "user_id": None, "name": "Supplier Payment", "type": "expense", "icon": "truck", "is_system": True},
    {"id": CAT_OTHER_EXPENSE_ID, "user_id": None, "name": "Other Expense", "type": "expense", "icon": "minus-circle", "is_system": True},
]

# Custom user-defined categories (8)
CUSTOM_CATEGORIES = [
    {"id": CAT_CUSTOM_TUITION_ID, "user_id": USER_PRIYA_ID, "name": "Tuition Income", "type": "income", "icon": "book", "is_system": False},
    {"id": CAT_CUSTOM_PET_CARE_ID, "user_id": USER_PRIYA_ID, "name": "Pet Care", "type": "expense", "icon": "heart", "is_system": False},
    {"id": CAT_CUSTOM_COUNTER_SALE_ID, "user_id": USER_RAJESH_ID, "name": "Counter Sale", "type": "income", "icon": "shopping-cart", "is_system": False},
    {"id": CAT_CUSTOM_WHOLESALE_ID, "user_id": USER_RAJESH_ID, "name": "Wholesale", "type": "income", "icon": "truck", "is_system": False},
    {"id": CAT_CUSTOM_PACKAGING_ID, "user_id": USER_RAJESH_ID, "name": "Packaging", "type": "expense", "icon": "box", "is_system": False},
    {"id": CAT_CUSTOM_CATERING_ID, "user_id": USER_ANITA_ID, "name": "Catering Income", "type": "income", "icon": "utensils", "is_system": False},
    {"id": CAT_CUSTOM_KITCHEN_ID, "user_id": USER_ANITA_ID, "name": "Kitchen Supplies", "type": "expense", "icon": "shopping-cart", "is_system": False},
    {"id": CAT_CUSTOM_COMMISSION_ID, "user_id": USER_ANITA_ID, "name": "Commission", "type": "income", "icon": "percent", "is_system": False},
]

ALL_CATEGORIES = SYSTEM_CATEGORIES + CUSTOM_CATEGORIES

# ---------------------------------------------------------------------------
# Transactions (55) — spanning 90 days
# ---------------------------------------------------------------------------
TRANSACTIONS = [
    # ===== Priya (U1): 20 transactions =====
    # Salary deposits (monthly)
    {"id": TXN_IDS[0], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_SBI_ID,
     "category_id": CAT_SALARY_ID, "type": "income", "amount": Decimal("65000.00"),
     "description": "Monthly salary - January", "transaction_date": _days_ago(60)},
    {"id": TXN_IDS[1], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_SBI_ID,
     "category_id": CAT_SALARY_ID, "type": "income", "amount": Decimal("65000.00"),
     "description": "Monthly salary - February", "transaction_date": _days_ago(30)},
    # Freelance
    {"id": TXN_IDS[2], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_SBI_ID,
     "category_id": CAT_FREELANCE_ID, "type": "income", "amount": Decimal("15000.00"),
     "description": "Website design project", "transaction_date": _days_ago(45)},
    {"id": TXN_IDS[3], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_CASH_ID,
     "category_id": CAT_CUSTOM_TUITION_ID, "type": "income", "amount": Decimal("5000.00"),
     "description": "Tuition classes - batch A", "transaction_date": _days_ago(20)},
    # Groceries
    {"id": TXN_IDS[4], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_CASH_ID,
     "category_id": CAT_GROCERIES_ID, "type": "expense", "amount": Decimal("3500.00"),
     "description": "Monthly groceries - BigBasket", "transaction_date": _days_ago(55)},
    {"id": TXN_IDS[5], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_CASH_ID,
     "category_id": CAT_GROCERIES_ID, "type": "expense", "amount": Decimal("2800.00"),
     "description": "Weekly vegetables & fruits", "transaction_date": _days_ago(25)},
    # Rent
    {"id": TXN_IDS[6], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_SBI_ID,
     "category_id": CAT_RENT_ID, "type": "expense", "amount": Decimal("18000.00"),
     "description": "Monthly rent - Jan", "transaction_date": _days_ago(58)},
    {"id": TXN_IDS[7], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_SBI_ID,
     "category_id": CAT_RENT_ID, "type": "expense", "amount": Decimal("18000.00"),
     "description": "Monthly rent - Feb", "transaction_date": _days_ago(28)},
    # Utilities
    {"id": TXN_IDS[8], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_SBI_ID,
     "category_id": CAT_UTILITIES_ID, "type": "expense", "amount": Decimal("2500.00"),
     "description": "Electricity bill", "transaction_date": _days_ago(50)},
    # Subscriptions
    {"id": TXN_IDS[9], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_HDFC_CC_ID,
     "category_id": CAT_SUBSCRIPTION_ID, "type": "expense", "amount": Decimal("499.00"),
     "description": "Netflix subscription", "transaction_date": _days_ago(40)},
    {"id": TXN_IDS[10], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_HDFC_CC_ID,
     "category_id": CAT_SUBSCRIPTION_ID, "type": "expense", "amount": Decimal("199.00"),
     "description": "Spotify premium", "transaction_date": _days_ago(40)},
    # Food & Dining
    {"id": TXN_IDS[11], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_CASH_ID,
     "category_id": CAT_FOOD_DINING_ID, "type": "expense", "amount": Decimal("1200.00"),
     "description": "Dinner at Barbeque Nation", "transaction_date": _days_ago(15)},
    # Transport
    {"id": TXN_IDS[12], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_CASH_ID,
     "category_id": CAT_TRANSPORT_ID, "type": "expense", "amount": Decimal("850.00"),
     "description": "Uber rides this week", "transaction_date": _days_ago(10)},
    # Shopping
    {"id": TXN_IDS[13], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_HDFC_CC_ID,
     "category_id": CAT_SHOPPING_ID, "type": "expense", "amount": Decimal("4500.00"),
     "description": "Amazon shopping", "transaction_date": _days_ago(35)},
    # Healthcare
    {"id": TXN_IDS[14], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_SBI_ID,
     "category_id": CAT_HEALTHCARE_ID, "type": "expense", "amount": Decimal("1500.00"),
     "description": "Doctor consultation", "transaction_date": _days_ago(22)},
    # Pet care (custom)
    {"id": TXN_IDS[15], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_CASH_ID,
     "category_id": CAT_CUSTOM_PET_CARE_ID, "type": "expense", "amount": Decimal("2000.00"),
     "description": "Vet visit for Luna", "transaction_date": _days_ago(18)},
    # Transfer between accounts
    {"id": TXN_IDS[16], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_SBI_ID,
     "category_id": None, "type": "transfer", "amount": Decimal("10000.00"),
     "description": "Transfer to cash", "transaction_date": _days_ago(12)},
    # Investment
    {"id": TXN_IDS[17], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_SBI_ID,
     "category_id": CAT_INVESTMENT_ID, "type": "income", "amount": Decimal("3200.00"),
     "description": "Mutual fund dividend", "transaction_date": _days_ago(8)},
    # Mobile
    {"id": TXN_IDS[18], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_SBI_ID,
     "category_id": CAT_MOBILE_INTERNET_ID, "type": "expense", "amount": Decimal("599.00"),
     "description": "Jio recharge", "transaction_date": _days_ago(5)},
    # Insurance
    {"id": TXN_IDS[19], "user_id": USER_PRIYA_ID, "account_id": ACCOUNT_PRIYA_SBI_ID,
     "category_id": CAT_INSURANCE_ID, "type": "expense", "amount": Decimal("5000.00"),
     "description": "LIC premium", "transaction_date": _days_ago(3)},

    # ===== Rajesh (U2): 18 transactions =====
    # Business income
    {"id": TXN_IDS[20], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_SHOP_CASH_ID,
     "category_id": CAT_CUSTOM_COUNTER_SALE_ID, "type": "income", "amount": Decimal("8500.00"),
     "description": "Daily counter sales", "transaction_date": _days_ago(85)},
    {"id": TXN_IDS[21], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_SHOP_CASH_ID,
     "category_id": CAT_CUSTOM_COUNTER_SALE_ID, "type": "income", "amount": Decimal("12000.00"),
     "description": "Weekend sales", "transaction_date": _days_ago(78)},
    {"id": TXN_IDS[22], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_ICICI_ID,
     "category_id": CAT_CUSTOM_WHOLESALE_ID, "type": "income", "amount": Decimal("45000.00"),
     "description": "Wholesale order - Suresh Textiles", "transaction_date": _days_ago(70)},
    {"id": TXN_IDS[23], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_ICICI_ID,
     "category_id": CAT_CUSTOM_WHOLESALE_ID, "type": "income", "amount": Decimal("32000.00"),
     "description": "Wholesale order - Lakshmi Stores", "transaction_date": _days_ago(55)},
    {"id": TXN_IDS[24], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_SHOP_CASH_ID,
     "category_id": CAT_CUSTOM_COUNTER_SALE_ID, "type": "income", "amount": Decimal("9500.00"),
     "description": "Counter sales - festive week", "transaction_date": _days_ago(42)},
    {"id": TXN_IDS[25], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_PAYTM_ID,
     "category_id": CAT_BUSINESS_INCOME_ID, "type": "income", "amount": Decimal("6000.00"),
     "description": "UPI payments collected", "transaction_date": _days_ago(30)},
    {"id": TXN_IDS[26], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_ICICI_ID,
     "category_id": CAT_CUSTOM_WHOLESALE_ID, "type": "income", "amount": Decimal("28000.00"),
     "description": "Wholesale order - Mohammed Traders", "transaction_date": _days_ago(20)},
    # Supplier payments
    {"id": TXN_IDS[27], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_ICICI_ID,
     "category_id": CAT_SUPPLIER_PAYMENT_ID, "type": "expense", "amount": Decimal("35000.00"),
     "description": "Supplier - Mumbai Fabrics", "transaction_date": _days_ago(65)},
    {"id": TXN_IDS[28], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_ICICI_ID,
     "category_id": CAT_SUPPLIER_PAYMENT_ID, "type": "expense", "amount": Decimal("22000.00"),
     "description": "Supplier - Surat Silk House", "transaction_date": _days_ago(40)},
    # Salary expense
    {"id": TXN_IDS[29], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_ICICI_ID,
     "category_id": CAT_SALARY_EXPENSE_ID, "type": "expense", "amount": Decimal("15000.00"),
     "description": "Staff salary - Ramu", "transaction_date": _days_ago(30)},
    {"id": TXN_IDS[30], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_ICICI_ID,
     "category_id": CAT_SALARY_EXPENSE_ID, "type": "expense", "amount": Decimal("12000.00"),
     "description": "Staff salary - Sita", "transaction_date": _days_ago(30)},
    # Rent
    {"id": TXN_IDS[31], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_ICICI_ID,
     "category_id": CAT_RENT_ID, "type": "expense", "amount": Decimal("25000.00"),
     "description": "Shop rent - January", "transaction_date": _days_ago(60)},
    {"id": TXN_IDS[32], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_ICICI_ID,
     "category_id": CAT_RENT_ID, "type": "expense", "amount": Decimal("25000.00"),
     "description": "Shop rent - February", "transaction_date": _days_ago(30)},
    # Packaging (custom)
    {"id": TXN_IDS[33], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_SHOP_CASH_ID,
     "category_id": CAT_CUSTOM_PACKAGING_ID, "type": "expense", "amount": Decimal("3500.00"),
     "description": "Packaging materials", "transaction_date": _days_ago(50)},
    # Maintenance
    {"id": TXN_IDS[34], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_SHOP_CASH_ID,
     "category_id": CAT_MAINTENANCE_ID, "type": "expense", "amount": Decimal("2000.00"),
     "description": "Shop AC repair", "transaction_date": _days_ago(25)},
    # Transfer
    {"id": TXN_IDS[35], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_SHOP_CASH_ID,
     "category_id": None, "type": "transfer", "amount": Decimal("20000.00"),
     "description": "Cash deposit to bank", "transaction_date": _days_ago(15)},
    # Taxes
    {"id": TXN_IDS[36], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_ICICI_ID,
     "category_id": CAT_TAXES_ID, "type": "expense", "amount": Decimal("8000.00"),
     "description": "GST payment Q3", "transaction_date": _days_ago(10)},
    # Utilities
    {"id": TXN_IDS[37], "user_id": USER_RAJESH_ID, "account_id": ACCOUNT_RAJESH_ICICI_ID,
     "category_id": CAT_UTILITIES_ID, "type": "expense", "amount": Decimal("4500.00"),
     "description": "Shop electricity bill", "transaction_date": _days_ago(5)},

    # ===== Anita (U3): 12 transactions =====
    # Catering income
    {"id": TXN_IDS[38], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_KOTAK_ID,
     "category_id": CAT_CUSTOM_CATERING_ID, "type": "income", "amount": Decimal("25000.00"),
     "description": "Wedding catering - Sharma family", "transaction_date": _days_ago(80)},
    {"id": TXN_IDS[39], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_KOTAK_ID,
     "category_id": CAT_CUSTOM_CATERING_ID, "type": "income", "amount": Decimal("18000.00"),
     "description": "Birthday party catering", "transaction_date": _days_ago(50)},
    {"id": TXN_IDS[40], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_CASH_ID,
     "category_id": CAT_CUSTOM_COMMISSION_ID, "type": "income", "amount": Decimal("3000.00"),
     "description": "Referral commission", "transaction_date": _days_ago(35)},
    {"id": TXN_IDS[41], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_KOTAK_ID,
     "category_id": CAT_CUSTOM_CATERING_ID, "type": "income", "amount": Decimal("35000.00"),
     "description": "Corporate event catering", "transaction_date": _days_ago(15)},
    # Kitchen supplies (custom)
    {"id": TXN_IDS[42], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_CASH_ID,
     "category_id": CAT_CUSTOM_KITCHEN_ID, "type": "expense", "amount": Decimal("8000.00"),
     "description": "Bulk spices & ingredients", "transaction_date": _days_ago(75)},
    {"id": TXN_IDS[43], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_CASH_ID,
     "category_id": CAT_CUSTOM_KITCHEN_ID, "type": "expense", "amount": Decimal("5500.00"),
     "description": "Cooking equipment", "transaction_date": _days_ago(45)},
    # Loan EMI
    {"id": TXN_IDS[44], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_KOTAK_ID,
     "category_id": CAT_EMI_LOAN_ID, "type": "expense", "amount": Decimal("22000.00"),
     "description": "Home loan EMI - Jan", "transaction_date": _days_ago(60)},
    {"id": TXN_IDS[45], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_KOTAK_ID,
     "category_id": CAT_EMI_LOAN_ID, "type": "expense", "amount": Decimal("22000.00"),
     "description": "Home loan EMI - Feb", "transaction_date": _days_ago(30)},
    # Groceries
    {"id": TXN_IDS[46], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_CASH_ID,
     "category_id": CAT_GROCERIES_ID, "type": "expense", "amount": Decimal("4000.00"),
     "description": "Monthly groceries", "transaction_date": _days_ago(25)},
    # Salary expense (staff)
    {"id": TXN_IDS[47], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_KOTAK_ID,
     "category_id": CAT_SALARY_EXPENSE_ID, "type": "expense", "amount": Decimal("10000.00"),
     "description": "Kitchen helper salary", "transaction_date": _days_ago(30)},
    # Utilities
    {"id": TXN_IDS[48], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_KOTAK_ID,
     "category_id": CAT_UTILITIES_ID, "type": "expense", "amount": Decimal("3500.00"),
     "description": "Gas cylinder + electricity", "transaction_date": _days_ago(20)},
    # Transfer
    {"id": TXN_IDS[49], "user_id": USER_ANITA_ID, "account_id": ACCOUNT_ANITA_KOTAK_ID,
     "category_id": None, "type": "transfer", "amount": Decimal("5000.00"),
     "description": "Business to personal cash", "transaction_date": _days_ago(10)},

    # ===== Vikram (U4): 3 transactions (not onboarded, minimal) =====
    {"id": TXN_IDS[50], "user_id": USER_VIKRAM_ID, "account_id": ACCOUNT_VIKRAM_CASH_ID,
     "category_id": CAT_OTHER_INCOME_ID, "type": "income", "amount": Decimal("5000.00"),
     "description": "Cash gift from uncle", "transaction_date": _days_ago(30)},
    {"id": TXN_IDS[51], "user_id": USER_VIKRAM_ID, "account_id": ACCOUNT_VIKRAM_CASH_ID,
     "category_id": CAT_FOOD_DINING_ID, "type": "expense", "amount": Decimal("800.00"),
     "description": "Lunch with friends", "transaction_date": _days_ago(20)},
    {"id": TXN_IDS[52], "user_id": USER_VIKRAM_ID, "account_id": ACCOUNT_VIKRAM_CASH_ID,
     "category_id": CAT_TRANSPORT_ID, "type": "expense", "amount": Decimal("200.00"),
     "description": "Auto rickshaw", "transaction_date": _days_ago(15)},

    # ===== Meena (U5): 2 transactions (inactive user, historical) =====
    {"id": TXN_IDS[53], "user_id": USER_MEENA_ID, "account_id": ACCOUNT_MEENA_BANK_ID,
     "category_id": CAT_SALARY_ID, "type": "income", "amount": Decimal("30000.00"),
     "description": "Last salary before deactivation", "transaction_date": _days_ago(90)},
    {"id": TXN_IDS[54], "user_id": USER_MEENA_ID, "account_id": ACCOUNT_MEENA_BANK_ID,
     "category_id": CAT_RENT_ID, "type": "expense", "amount": Decimal("10000.00"),
     "description": "Last rent payment", "transaction_date": _days_ago(88)},
]

# ---------------------------------------------------------------------------
# Customers (8) — for U2 (4) and U3 (4)
# ---------------------------------------------------------------------------
CUSTOMERS = [
    # Rajesh's customers
    {"id": CUST_SURESH_TEXTILES_ID, "user_id": USER_RAJESH_ID,
     "name": "Suresh Textiles", "phone": "+919800100001",
     "email": "suresh.textiles@example.com", "address": "12 Cloth Market, Ahmedabad"},
    {"id": CUST_LAKSHMI_STORES_ID, "user_id": USER_RAJESH_ID,
     "name": "Lakshmi Stores", "phone": "+919800100002",
     "email": "lakshmi.stores@example.com", "address": "45 MG Road, Pune"},
    {"id": CUST_MOHAMMED_TRADERS_ID, "user_id": USER_RAJESH_ID,
     "name": "Mohammed Traders", "phone": "+919800100003",
     "email": None, "address": "78 Station Road, Mumbai"},
    {"id": CUST_DEEPA_FASHIONS_ID, "user_id": USER_RAJESH_ID,
     "name": "Deepa Fashions", "phone": "+919800100004",
     "email": "deepa.fashions@example.com", "address": None},
    # Anita's customers
    {"id": CUST_RAMESH_SWEETS_ID, "user_id": USER_ANITA_ID,
     "name": "Ramesh Sweets & Snacks", "phone": "+919800200001",
     "email": "ramesh.sweets@example.com", "address": "22 Food Street, Chennai"},
    {"id": CUST_KAVITHA_FLOWERS_ID, "user_id": USER_ANITA_ID,
     "name": "Kavitha Flower Decorations", "phone": "+919800200002",
     "email": None, "address": "9 Temple Road, Coimbatore"},
    {"id": CUST_PRAKASH_HARDWARE_ID, "user_id": USER_ANITA_ID,
     "name": "Prakash Hardware", "phone": "+919800200003",
     "email": "prakash.hw@example.com", "address": "56 Industrial Area, Bangalore"},
    {"id": CUST_SUNITA_DAIRY_ID, "user_id": USER_ANITA_ID,
     "name": "Sunita Dairy Farm", "phone": "+919800200004",
     "email": "sunita.dairy@example.com", "address": None},
]

# ---------------------------------------------------------------------------
# Ledger Entries (25) — mix of debit/credit, settled/unsettled, overdue
# ---------------------------------------------------------------------------
LEDGER_ENTRIES = [
    # ===== Rajesh -> Suresh Textiles (5 entries) =====
    {"id": LEDGER_IDS[0], "user_id": USER_RAJESH_ID, "customer_id": CUST_SURESH_TEXTILES_ID,
     "type": "debit", "amount": Decimal("15000.00"), "description": "Fabric order #101",
     "due_date": _date_ago(30), "is_settled": True},
    {"id": LEDGER_IDS[1], "user_id": USER_RAJESH_ID, "customer_id": CUST_SURESH_TEXTILES_ID,
     "type": "credit", "amount": Decimal("15000.00"), "description": "Payment received - #101",
     "due_date": None, "is_settled": True},
    {"id": LEDGER_IDS[2], "user_id": USER_RAJESH_ID, "customer_id": CUST_SURESH_TEXTILES_ID,
     "type": "debit", "amount": Decimal("25000.00"), "description": "Fabric order #102",
     "due_date": _date_ago(5), "is_settled": False},  # OVERDUE
    {"id": LEDGER_IDS[3], "user_id": USER_RAJESH_ID, "customer_id": CUST_SURESH_TEXTILES_ID,
     "type": "credit", "amount": Decimal("10000.00"), "description": "Partial payment - #102",
     "due_date": None, "is_settled": False},
    {"id": LEDGER_IDS[4], "user_id": USER_RAJESH_ID, "customer_id": CUST_SURESH_TEXTILES_ID,
     "type": "debit", "amount": Decimal("8000.00"), "description": "Fabric order #103",
     "due_date": _date_ahead(15), "is_settled": False},  # Future due date
    # Outstanding for Suresh: unsettled debits(25000+8000) - unsettled credits(10000) = 23000

    # ===== Rajesh -> Lakshmi Stores (4 entries) =====
    {"id": LEDGER_IDS[5], "user_id": USER_RAJESH_ID, "customer_id": CUST_LAKSHMI_STORES_ID,
     "type": "debit", "amount": Decimal("12000.00"), "description": "Saree lot #50",
     "due_date": _date_ago(15), "is_settled": False},  # OVERDUE
    {"id": LEDGER_IDS[6], "user_id": USER_RAJESH_ID, "customer_id": CUST_LAKSHMI_STORES_ID,
     "type": "debit", "amount": Decimal("8000.00"), "description": "Saree lot #51",
     "due_date": _date_ahead(10), "is_settled": False},
    {"id": LEDGER_IDS[7], "user_id": USER_RAJESH_ID, "customer_id": CUST_LAKSHMI_STORES_ID,
     "type": "credit", "amount": Decimal("5000.00"), "description": "Advance payment",
     "due_date": None, "is_settled": False},
    {"id": LEDGER_IDS[8], "user_id": USER_RAJESH_ID, "customer_id": CUST_LAKSHMI_STORES_ID,
     "type": "debit", "amount": Decimal("3000.00"), "description": "Alterations",
     "due_date": None, "is_settled": True},
    # Outstanding for Lakshmi: unsettled debits(12000+8000) - unsettled credits(5000) = 15000

    # ===== Rajesh -> Mohammed Traders (3 entries) =====
    {"id": LEDGER_IDS[9], "user_id": USER_RAJESH_ID, "customer_id": CUST_MOHAMMED_TRADERS_ID,
     "type": "debit", "amount": Decimal("20000.00"), "description": "Bulk cotton order",
     "due_date": _date_ago(10), "is_settled": True},
    {"id": LEDGER_IDS[10], "user_id": USER_RAJESH_ID, "customer_id": CUST_MOHAMMED_TRADERS_ID,
     "type": "credit", "amount": Decimal("20000.00"), "description": "Full payment",
     "due_date": None, "is_settled": True},
    {"id": LEDGER_IDS[11], "user_id": USER_RAJESH_ID, "customer_id": CUST_MOHAMMED_TRADERS_ID,
     "type": "debit", "amount": Decimal("18000.00"), "description": "New silk order",
     "due_date": _date_ahead(30), "is_settled": False},
    # Outstanding for Mohammed: unsettled debits(18000) - unsettled credits(0) = 18000

    # ===== Rajesh -> Deepa Fashions (2 entries) =====
    {"id": LEDGER_IDS[12], "user_id": USER_RAJESH_ID, "customer_id": CUST_DEEPA_FASHIONS_ID,
     "type": "debit", "amount": Decimal("7500.00"), "description": "Designer collection",
     "due_date": _date_ago(3), "is_settled": False},  # OVERDUE
    {"id": LEDGER_IDS[13], "user_id": USER_RAJESH_ID, "customer_id": CUST_DEEPA_FASHIONS_ID,
     "type": "credit", "amount": Decimal("2500.00"), "description": "Part payment",
     "due_date": None, "is_settled": False},
    # Outstanding for Deepa: unsettled debits(7500) - unsettled credits(2500) = 5000

    # ===== Anita -> Ramesh Sweets (3 entries) =====
    {"id": LEDGER_IDS[14], "user_id": USER_ANITA_ID, "customer_id": CUST_RAMESH_SWEETS_ID,
     "type": "debit", "amount": Decimal("15000.00"), "description": "Diwali sweets catering",
     "due_date": _date_ago(20), "is_settled": True},
    {"id": LEDGER_IDS[15], "user_id": USER_ANITA_ID, "customer_id": CUST_RAMESH_SWEETS_ID,
     "type": "credit", "amount": Decimal("15000.00"), "description": "Full payment received",
     "due_date": None, "is_settled": True},
    {"id": LEDGER_IDS[16], "user_id": USER_ANITA_ID, "customer_id": CUST_RAMESH_SWEETS_ID,
     "type": "debit", "amount": Decimal("10000.00"), "description": "Republic Day order",
     "due_date": _date_ahead(5), "is_settled": False},
    # Outstanding for Ramesh: unsettled debits(10000) - unsettled credits(0) = 10000

    # ===== Anita -> Kavitha Flowers (3 entries) =====
    {"id": LEDGER_IDS[17], "user_id": USER_ANITA_ID, "customer_id": CUST_KAVITHA_FLOWERS_ID,
     "type": "debit", "amount": Decimal("8000.00"), "description": "Flower decoration supply",
     "due_date": _date_ago(7), "is_settled": False},  # OVERDUE
    {"id": LEDGER_IDS[18], "user_id": USER_ANITA_ID, "customer_id": CUST_KAVITHA_FLOWERS_ID,
     "type": "credit", "amount": Decimal("3000.00"), "description": "Partial payment",
     "due_date": None, "is_settled": False},
    {"id": LEDGER_IDS[19], "user_id": USER_ANITA_ID, "customer_id": CUST_KAVITHA_FLOWERS_ID,
     "type": "debit", "amount": Decimal("5000.00"), "description": "Temple event flowers",
     "due_date": _date_ahead(20), "is_settled": False},
    # Outstanding for Kavitha: unsettled debits(8000+5000) - unsettled credits(3000) = 10000

    # ===== Anita -> Prakash Hardware (3 entries) =====
    {"id": LEDGER_IDS[20], "user_id": USER_ANITA_ID, "customer_id": CUST_PRAKASH_HARDWARE_ID,
     "type": "debit", "amount": Decimal("12000.00"), "description": "Kitchen renovation supplies",
     "due_date": _date_ago(40), "is_settled": True},
    {"id": LEDGER_IDS[21], "user_id": USER_ANITA_ID, "customer_id": CUST_PRAKASH_HARDWARE_ID,
     "type": "credit", "amount": Decimal("12000.00"), "description": "Full payment",
     "due_date": None, "is_settled": True},
    {"id": LEDGER_IDS[22], "user_id": USER_ANITA_ID, "customer_id": CUST_PRAKASH_HARDWARE_ID,
     "type": "debit", "amount": Decimal("6000.00"), "description": "Utensils order",
     "due_date": _date_ahead(25), "is_settled": False},
    # Outstanding for Prakash: unsettled debits(6000) - unsettled credits(0) = 6000

    # ===== Anita -> Sunita Dairy (2 entries) =====
    {"id": LEDGER_IDS[23], "user_id": USER_ANITA_ID, "customer_id": CUST_SUNITA_DAIRY_ID,
     "type": "debit", "amount": Decimal("4500.00"), "description": "Monthly milk supply",
     "due_date": _date_ago(2), "is_settled": False},  # OVERDUE
    {"id": LEDGER_IDS[24], "user_id": USER_ANITA_ID, "customer_id": CUST_SUNITA_DAIRY_ID,
     "type": "credit", "amount": Decimal("2000.00"), "description": "Partial payment",
     "due_date": None, "is_settled": False},
    # Outstanding for Sunita: unsettled debits(4500) - unsettled credits(2000) = 2500
]

# ---------------------------------------------------------------------------
# Receipts (5)
# ---------------------------------------------------------------------------
RECEIPTS = [
    {"id": RECEIPT_IDS[0], "transaction_id": TXN_IDS[4],
     "file_url": "/receipts/priya_groceries_001.jpg", "ocr_text": "BigBasket Invoice #BB2024001 Total: Rs 3,500.00"},
    {"id": RECEIPT_IDS[1], "transaction_id": TXN_IDS[6],
     "file_url": "/receipts/priya_rent_jan.pdf", "ocr_text": "Rent Receipt January 2024 Amount: Rs 18,000"},
    {"id": RECEIPT_IDS[2], "transaction_id": TXN_IDS[27],
     "file_url": "/receipts/rajesh_supplier_mumbai.jpg", "ocr_text": "Mumbai Fabrics Tax Invoice GST: 18% Total: Rs 35,000.00"},
    {"id": RECEIPT_IDS[3], "transaction_id": TXN_IDS[38],
     "file_url": "/receipts/anita_catering_sharma.pdf", "ocr_text": "Catering Invoice - Sharma Wedding 250 guests Total: Rs 25,000"},
    {"id": RECEIPT_IDS[4], "transaction_id": TXN_IDS[44],
     "file_url": "/receipts/anita_emi_jan.pdf", "ocr_text": "Home Loan EMI Receipt Bank: Kotak EMI: Rs 22,000.00"},
]


# ===========================================================================
# HELPER FUNCTIONS
# ===========================================================================

def get_user(user_id: str) -> dict:
    """Get a user dict by ID."""
    return next(u for u in USERS if u["id"] == user_id)


def get_active_users() -> list[dict]:
    """Get all active users."""
    return [u for u in USERS if u["is_active"]]


def get_accounts_for_user(user_id: str) -> list[dict]:
    """Get all accounts belonging to a user."""
    return [a for a in ACCOUNTS if a["user_id"] == user_id]


def get_transactions_for_user(user_id: str) -> list[dict]:
    """Get all transactions belonging to a user."""
    return [t for t in TRANSACTIONS if t["user_id"] == user_id]


def get_customers_for_user(user_id: str) -> list[dict]:
    """Get all customers belonging to a user."""
    return [c for c in CUSTOMERS if c["user_id"] == user_id]


def get_ledger_entries_for_customer(customer_id: str) -> list[dict]:
    """Get all ledger entries for a customer."""
    return [e for e in LEDGER_ENTRIES if e["customer_id"] == customer_id]


def get_overdue_entries() -> list[dict]:
    """Get all unsettled entries with due_date in the past."""
    today = ANCHOR_DATE
    return [
        e for e in LEDGER_ENTRIES
        if not e["is_settled"] and e["due_date"] is not None and e["due_date"] < today
    ]


def get_outstanding_balance(customer_id: str) -> Decimal:
    """Calculate outstanding balance for a customer: sum(unsettled debits) - sum(unsettled credits)."""
    entries = get_ledger_entries_for_customer(customer_id)
    unsettled = [e for e in entries if not e["is_settled"]]
    debits = sum(e["amount"] for e in unsettled if e["type"] == "debit")
    credits = sum(e["amount"] for e in unsettled if e["type"] == "credit")
    return debits - credits


def get_settings_for_user(user_id: str) -> dict:
    """Get user settings by user_id."""
    return next(s for s in USER_SETTINGS if s["user_id"] == user_id)


# ===========================================================================
# TOKEN FACTORY — zero service dependencies (only python-jose)
# ===========================================================================

def make_access_token(user_id: str, secret: str = JWT_SECRET, algorithm: str = JWT_ALGORITHM) -> str:
    """Create a valid JWT access token for testing."""
    import uuid as _uuid
    now = int(datetime.now(timezone.utc).timestamp())
    payload = {
        "sub": user_id,
        "type": "access",
        "exp": now + 3600,
        "iat": now,
        "jti": str(_uuid.uuid4()),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def make_auth_headers(user_id: str, secret: str = JWT_SECRET) -> dict[str, str]:
    """Create Authorization headers for a user."""
    token = make_access_token(user_id, secret)
    return {"Authorization": f"Bearer {token}"}


# Convenient per-user header factories
def priya_headers() -> dict[str, str]:
    return make_auth_headers(USER_PRIYA_ID)

def rajesh_headers() -> dict[str, str]:
    return make_auth_headers(USER_RAJESH_ID)

def anita_headers() -> dict[str, str]:
    return make_auth_headers(USER_ANITA_ID)

def vikram_headers() -> dict[str, str]:
    return make_auth_headers(USER_VIKRAM_ID)

def meena_headers() -> dict[str, str]:
    return make_auth_headers(USER_MEENA_ID)

def arjun_headers() -> dict[str, str]:
    return make_auth_headers(USER_ARJUN_ID)
