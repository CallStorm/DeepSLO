from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, String, UniqueConstraint


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String(100), nullable=False))
    username: str = Field(sa_column=Column(String(100), unique=True, nullable=False))
    hashed_password: str
    email: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    is_active: bool = True
    is_admin: bool = False


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ms_name: str = Field(index=True)
    ms_description: Optional[str] = None
    ms_createtime: Optional[datetime] = None
    ms_id: str = Field(index=True)

    __table_args__ = (
        UniqueConstraint("ms_id", name="uq_project_ms_id"),
    )


class AIModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_default: bool = False


class MSConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    ak: str
    sk: str
    active: bool = True


