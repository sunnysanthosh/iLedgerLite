from typing import Literal

from pydantic import BaseModel, EmailStr


class EmailSendRequest(BaseModel):
    to_email: EmailStr
    to_name: str
    template: Literal["welcome", "invite"]
    context: dict = {}
