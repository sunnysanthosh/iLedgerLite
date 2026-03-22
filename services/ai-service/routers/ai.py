from db import get_db
from fastapi import APIRouter, Depends
from models.org import OrgMembership
from models.user import User
from schemas.ai import CategorizeRequest, CategorizeResponse, InsightsResponse, OcrRequest, OcrResponse
from services.ai_service import categorize_transaction, get_spending_insights, mock_ocr
from services.security import get_current_user, get_org_member
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/categorize", response_model=CategorizeResponse)
async def categorize(
    body: CategorizeRequest,
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    predictions = await categorize_transaction(
        db=db,
        org_id=membership.org_id,
        description=body.description,
        amount=body.amount,
        txn_type=body.type,
    )
    return {"predictions": predictions}


@router.get("/insights", response_model=InsightsResponse)
async def insights(
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    result = await get_spending_insights(db=db, org_id=membership.org_id)
    return result


@router.post("/ocr", response_model=OcrResponse)
async def ocr(
    body: OcrRequest,
    current_user: User = Depends(get_current_user),
):
    result = mock_ocr(image_base64=body.image_base64, filename=body.filename)
    return result
