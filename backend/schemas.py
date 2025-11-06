from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserBase(BaseModel):
    name: str
    username: str
    email: Optional[EmailStr] = None
    project_id: Optional[int] = None
    is_active: bool = True
    is_admin: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    project_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: int


class ProjectOut(BaseModel):
    id: int
    ms_name: str
    ms_description: Optional[str] = None
    ms_createtime: Optional[datetime] = None
    ms_id: str


class AIModelBase(BaseModel):
    name: Optional[str] = None
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_default: bool = False


class AIModelCreate(AIModelBase):
    pass


class AIModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_default: Optional[bool] = None


class AIModelOut(AIModelBase):
    id: int


class MSConfigBase(BaseModel):
    url: str
    ak: str
    sk: str
    active: bool = True


class MSConfigCreate(MSConfigBase):
    pass


class MSConfigOut(MSConfigBase):
    id: int



class ProbeConfigOut(BaseModel):
    id: int
    project_ms_id: str
    scenario_id: str
    name: str
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

