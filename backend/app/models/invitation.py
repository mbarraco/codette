from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseMixin
from .user import UserRole


class Invitation(BaseMixin, Base):
    __tablename__ = "invitations"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    used_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
