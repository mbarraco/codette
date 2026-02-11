from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseMixin


class Problem(BaseMixin, Base):
    __tablename__ = "problems"

    statement: Mapped[str] = mapped_column(Text, nullable=False)
    hints: Mapped[str | None] = mapped_column(Text, nullable=True)
    examples: Mapped[str | None] = mapped_column(Text, nullable=True)
