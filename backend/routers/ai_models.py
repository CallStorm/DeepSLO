from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..db import get_session
from ..deps import require_admin, get_current_user
from ..models import AIModel, User
from ..schemas import AIModelCreate, AIModelUpdate, AIModelOut


router = APIRouter()


@router.get("/", response_model=List[AIModelOut])
def list_models(_: User = Depends(get_current_user), session=Depends(get_session)):
    models = session.exec(select(AIModel)).all()
    return [AIModelOut(**m.model_dump()) for m in models]  # type: ignore[arg-type]


@router.post("/", response_model=AIModelOut)
def create_model(data: AIModelCreate, _: User = Depends(require_admin), session=Depends(get_session)):
    if data.is_default:
        session.exec(select(AIModel)).all()
        for m in session.exec(select(AIModel)).all():
            if m.is_default:
                m.is_default = False
                session.add(m)
    model = AIModel(**data.model_dump())
    session.add(model)
    session.commit()
    session.refresh(model)
    return AIModelOut(**model.model_dump())  # type: ignore[arg-type]


@router.put("/{model_id}", response_model=AIModelOut)
def update_model(model_id: int, data: AIModelUpdate, _: User = Depends(require_admin), session=Depends(get_session)):
    model = session.get(AIModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    update = data.model_dump(exclude_unset=True)
    if update.get("is_default"):
        for m in session.exec(select(AIModel)).all():
            if m.is_default:
                m.is_default = False
                session.add(m)
    for k, v in update.items():
        setattr(model, k, v)
    session.add(model)
    session.commit()
    session.refresh(model)
    return AIModelOut(**model.model_dump())  # type: ignore[arg-type]


@router.post("/{model_id}/set-default")
def set_default_model(model_id: int, _: User = Depends(require_admin), session=Depends(get_session)):
    model = session.get(AIModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    for m in session.exec(select(AIModel)).all():
        m.is_default = m.id == model_id
        session.add(m)
    session.commit()
    return {"ok": True}


@router.delete("/{model_id}")
def delete_model(model_id: int, _: User = Depends(require_admin), session=Depends(get_session)):
    model = session.get(AIModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    session.delete(model)
    session.commit()
    return {"ok": True}


