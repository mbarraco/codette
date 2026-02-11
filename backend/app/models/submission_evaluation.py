from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseMixin


class SubmissionEvaluation(BaseMixin, Base):
    __tablename__ = "submission_evaluations"

    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id"), nullable=False
    )
    success: Mapped[bool] = mapped_column(nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
