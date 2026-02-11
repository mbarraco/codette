from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseMixin


class Run(BaseMixin, Base):
    __tablename__ = "runs"

    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id"), nullable=False
    )
    execution_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(default="queued", nullable=False)
    runner_output_uri: Mapped[str | None] = mapped_column(nullable=True)
    grader_output_uri: Mapped[str | None] = mapped_column(nullable=True)
