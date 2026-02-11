from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseMixin


class SubmissionQueue(BaseMixin, Base):
    __tablename__ = "submission_queue"

    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id"), nullable=False
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    attempt_count: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
