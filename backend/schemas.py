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


