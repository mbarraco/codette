import uuid as _uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseMixin


class Submission(BaseMixin, Base):
    __tablename__ = "submissions"

    artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), nullable=False)

    problem: Mapped["Problem"] = relationship(lazy="noload")  # noqa: F821
    runs: Mapped[list["Run"]] = relationship(back_populates="submission", lazy="noload")  # noqa: F821
    queue_entries: Mapped[list["SubmissionQueue"]] = relationship(  # noqa: F821
        back_populates="submission", lazy="noload"
    )
    evaluations: Mapped[list["SubmissionEvaluation"]] = relationship(  # noqa: F821
        back_populates="submission", lazy="noload"
    )

    @property
    def problem_uuid(self) -> _uuid.UUID:
        return self.problem.uuid
