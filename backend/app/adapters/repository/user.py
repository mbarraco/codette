import uuid

from sqlalchemy.orm import Session

from app.models import User
from app.models.user import UserRole


class UserRepository:
    def get_by_uuid(self, db: Session, user_uuid: uuid.UUID) -> User | None:
        return (
            db.query(User)
            .filter(User.uuid == user_uuid, User.deleted_at.is_(None))
            .one_or_none()
        )

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return (
            db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .one_or_none()
        )

    def get_by_email(self, db: Session, email: str) -> User | None:
        return (
            db.query(User)
            .filter(User.email == email, User.deleted_at.is_(None))
            .one_or_none()
        )

    def create(
        self,
        db: Session,
        email: str,
        password_hash: str,
        role: UserRole,
    ) -> User:
        user = User(email=email, password_hash=password_hash, role=role)
        db.add(user)
        db.flush()
        return user

    def list_all(self, db: Session) -> list[User]:
        return list(
            db.query(User)
            .filter(User.deleted_at.is_(None))
            .order_by(User.created_at.desc())
            .all()
        )
