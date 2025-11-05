from sqlmodel import SQLModel, Session
from .db import engine
from .models import User
from .security import get_password_hash


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def ensure_admin_user() -> None:
    with Session(engine) as session:
        admin = session.get(User, 1)
        if admin is not None:
            return
        admin = User(
            id=1,
            name="Administrator",
            username="admin",
            email="admin@example.com",
            project_id=None,
            is_active=True,
            is_admin=True,
            hashed_password=get_password_hash("admin"),
        )
        session.add(admin)
        session.commit()


