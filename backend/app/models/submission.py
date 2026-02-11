from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseMixin


class Submission(BaseMixin, Base):
    __tablename__ = "submissions"

    artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), nullable=False)
