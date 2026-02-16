from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class InvitationCreate(BaseModel):
    email: EmailStr
    role: UserRole


class InvitationResponse(BaseModel):
    uuid: UUID
    email: str
    role: UserRole
    used_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
