import uuid as _uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BaseMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[_uuid.UUID] = mapped_column(
        unique=True, nullable=False, default=_uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
