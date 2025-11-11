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



class ProbeSyncConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_ms_id: str = Field(sa_column=Column(String(64), nullable=False))
    enabled: bool = True
    # initial sync start datetime. If null, defaults to related probe's create_time
    start_time: Optional[datetime] = None
    # interval seconds between sync runs
    interval_seconds: int = 300
    # pointer: last synced start datetime
    last_synced_start: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_status: Optional[str] = Field(default=None, sa_column=Column(String(32), nullable=True))
    last_error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    __table_args__ = (
        UniqueConstraint("project_ms_id", name="uq_probe_sync_project"),
    )


class ProbeResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_ms_id: str = Field(sa_column=Column(String(64), nullable=False))
    report_id: str = Field(sa_column=Column(String(64), nullable=False))
    name: str = Field(sa_column=Column(String(255), nullable=False))
    start_time: datetime
    end_time: datetime
    request_duration_ms: Optional[int] = None
    status: Optional[str] = Field(default=None, sa_column=Column(String(32), nullable=True))
    error_count: Optional[int] = None
    success_count: Optional[int] = None
    is_valid: bool = True
    reason_label: Optional[str] = None
    created_at: Optional[datetime] = None

    __table_args__ = (
        UniqueConstraint("report_id", name="uq_probe_result_report_id"),
    )


class SLOConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # 类型：monthly（月度）或 yearly（年度）
    period_type: str = Field(sa_column=Column(String(20), nullable=False))
    # 项目ID（来自Metersphere，用于区分项目）
    project_ms_id: str = Field(sa_column=Column(String(64), nullable=False, index=True))
    # SLO目标值，如0.9999表示99.99%
    target: float = Field(nullable=False)
    # 允许最大中断时间（分钟），根据period_type和target计算
    max_downtime_minutes: float = Field(nullable=False)
    # 指标类型，默认为拨测（probe）
    metric_type: str = Field(default="probe", sa_column=Column(String(20), nullable=False))
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    __table_args__ = (
        UniqueConstraint("project_ms_id", "period_type", name="uq_slo_config_project_period"),
    )


class SLORecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # 项目ID
    project_ms_id: str = Field(sa_column=Column(String(64), nullable=False, index=True))
    # 周期类型：monthly（月度）或 yearly（年度）
    period_type: str = Field(sa_column=Column(String(20), nullable=False))
    # 周期值：月度如 "2025-11"，年度如 "2025"
    period_value: str = Field(sa_column=Column(String(20), nullable=False, index=True))
    # 累计中断时间（秒）
    total_downtime_seconds: float = Field(default=0.0, nullable=False)
    # SLO达成率（0-1之间）
    achievement_rate: float = Field(default=1.0, nullable=False)
    # 误差预算消耗率（0-1之间）
    error_budget_consumption: float = Field(default=0.0, nullable=False)
    # 最后计算时间
    calculated_at: Optional[datetime] = None
    # 创建时间
    created_at: Optional[datetime] = None
    # 更新时间
    updated_at: Optional[datetime] = None

    __table_args__ = (
        UniqueConstraint("project_ms_id", "period_type", "period_value", name="uq_slo_record"),
    )