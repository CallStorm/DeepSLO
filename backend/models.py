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
    name: Optional[str] = None
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



class ProbeConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_ms_id: str = Field(index=True)
    scenario_id: str = Field(index=True)
    name: str = Field(sa_column=Column(String(255), nullable=False))
    priority: Optional[str] = None
    status: Optional[str] = None
    step_total: Optional[int] = None
    request_pass_rate: Optional[str] = None
    last_report_status: Optional[str] = None
    last_report_id: Optional[str] = None
    num: Optional[int] = None
    environment_name: Optional[str] = None
    schedule_enable: Optional[bool] = None
    schedule_cron: Optional[str] = None
    next_trigger_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    __table_args__ = (
        UniqueConstraint("scenario_id", name="uq_probe_scenario_id"),
    )

