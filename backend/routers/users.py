from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..db import get_session
from ..deps import require_admin
from ..models import User
from ..schemas import UserCreate, UserOut, UserUpdate
from ..security import get_password_hash


router = APIRouter()


@router.get("/", response_model=List[UserOut])
def list_users(_: User = Depends(require_admin), session=Depends(get_session)):
    users = session.exec(select(User)).all()
    return [UserOut(**u.model_dump()) for u in users]  # type: ignore[arg-type]


@router.post("/", response_model=UserOut)
def create_user(data: UserCreate, _: User = Depends(require_admin), session=Depends(get_session)):
    user = User(
        name=data.name,
        username=data.username,
        email=data.email,
        project_id=data.project_id,
        is_active=data.is_active,
        is_admin=data.is_admin,
        hashed_password=get_password_hash(data.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserOut(**user.model_dump())  # type: ignore[arg-type]


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, _: User = Depends(require_admin), session=Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        user.hashed_password = get_password_hash(update_data.pop("password"))
    for k, v in update_data.items():
        setattr(user, k, v)
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserOut(**user.model_dump())  # type: ignore[arg-type]


@router.delete("/{user_id}")
def delete_user(user_id: int, _: User = Depends(require_admin), session=Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok": True}


