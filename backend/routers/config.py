from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..db import get_session
from ..deps import require_admin
from ..models import MSConfig, User
from ..schemas import MSConfigCreate, MSConfigOut


router = APIRouter()


@router.get("/metersphere", response_model=List[MSConfigOut])
def list_ms_configs(_: User = Depends(require_admin), session=Depends(get_session)):
    items = session.exec(select(MSConfig)).all()
    return [MSConfigOut(**i.model_dump()) for i in items]  # type: ignore[arg-type]


@router.post("/metersphere", response_model=MSConfigOut)
def create_ms_config(data: MSConfigCreate, _: User = Depends(require_admin), session=Depends(get_session)):
    cfg = MSConfig(**data.model_dump())
    session.add(cfg)
    session.commit()
    session.refresh(cfg)
    return MSConfigOut(**cfg.model_dump())  # type: ignore[arg-type]


@router.post("/metersphere/{config_id}/activate")
def activate_ms_config(config_id: int, _: User = Depends(require_admin), session=Depends(get_session)):
    cfg = session.get(MSConfig, config_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="Config not found")
    for c in session.exec(select(MSConfig)).all():
        c.active = c.id == config_id
        session.add(c)
    session.commit()
    return {"ok": True}


