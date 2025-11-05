import os
from typing import Iterator
from sqlmodel import Session, create_engine


MYSQL_USER = os.getenv("MYSQL_USER", "deepslo")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "deepslo")
MYSQL_HOST = os.getenv("MYSQL_HOST", "10.72.2.49")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "deepslo")

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    "?charset=utf8mb4"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


