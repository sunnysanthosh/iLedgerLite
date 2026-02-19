import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


# --- Categorize ---

class CategorizeRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0)
    type: str = Field(default="expense", pattern="^(income|expense)$")


class CategoryPrediction(BaseModel):
    category_id: uuid.UUID | None = None
    category_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class CategorizeResponse(BaseModel):
    predictions: list[CategoryPrediction]


# --- Insights ---

class SpendingAnomaly(BaseModel):
    category_name: str
    current_amount: str
    average_amount: str
    deviation: float


class SpendingTrend(BaseModel):
    category_name: str
    trend: str  # "increasing", "decreasing", "stable"
    last_30_days: str
    previous_30_days: str


class InsightsResponse(BaseModel):
    anomalies: list[SpendingAnomaly]
    trends: list[SpendingTrend]
    top_categories: list[dict]
    total_income_30d: str
    total_expense_30d: str


# --- OCR ---

class OcrRequest(BaseModel):
    image_base64: str = Field(..., min_length=1)
    filename: str | None = None


class OcrResponse(BaseModel):
    merchant: str
    amount: str
    date: str
    items: list[dict]
    raw_text: str
    confidence: float
