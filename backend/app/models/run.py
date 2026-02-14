from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseMixin


class Run(BaseMixin, Base):
    __tablename__ = "runs"

    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id"), nullable=False
    )
    execution_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(default="queued", nullable=False)
    failure_stage: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    runner_output_uri: Mapped[str | None] = mapped_column(nullable=True)
    grader_output_uri: Mapped[str | None] = mapped_column(nullable=True)

    submission: Mapped["Submission"] = relationship(  # noqa: F821
        back_populates="runs", lazy="noload"
    )
