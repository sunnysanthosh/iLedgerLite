from fastapi import APIRouter
from schemas.email import EmailSendRequest
from services.email_service import send_email

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/send", status_code=204, include_in_schema=False)
async def send_email_endpoint(data: EmailSendRequest):
    """Internal endpoint — no auth. Called by auth-service and user-service."""
    await send_email(data.to_email, data.to_name, data.template, data.context)
