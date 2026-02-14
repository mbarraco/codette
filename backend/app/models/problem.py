from datetime import datetime

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseMixin


class Problem(BaseMixin, Base):
    __tablename__ = "problems"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    hints: Mapped[str | None] = mapped_column(Text, nullable=True)
    examples: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_cases: Mapped[list[dict] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    function_signature: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
