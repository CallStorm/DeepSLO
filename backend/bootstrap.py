from sqlmodel import SQLModel, Session
from sqlalchemy import text
from .db import engine, MYSQL_DB
from .models import User
from .security import get_password_hash


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_ai_model_name_column()


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



def _ensure_ai_model_name_column() -> None:
    """Ensure AIModel table has the optional 'name' column (MySQL)."""
    with engine.connect() as conn:
        # Check column existence via information_schema
        check_sql = text(
            """
            SELECT 1
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :schema
              AND TABLE_NAME = 'aimodel'
              AND COLUMN_NAME = 'name'
            LIMIT 1
            """
        )
        exists = conn.execute(check_sql, {"schema": MYSQL_DB}).scalar()
        if not exists:
            conn.execute(text("ALTER TABLE `aimodel` ADD COLUMN `name` VARCHAR(255) NULL"))
            conn.commit()

