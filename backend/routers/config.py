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
    return [MSConfigOut.model_validate(i, from_attributes=True) for i in items]


@router.post("/metersphere", response_model=MSConfigOut)
def create_ms_config(data: MSConfigCreate, _: User = Depends(require_admin), session=Depends(get_session)):
    """Create or update the single Metersphere config. Always active and unique."""
    existing = session.exec(select(MSConfig)).first()
    if existing:
        existing.url = data.url
        existing.ak = data.ak
        existing.sk = data.sk
        existing.active = True
        session.add(existing)
        session.commit()
        session.refresh(existing)
        # Optionally clean up any stray extra rows
        extras = session.exec(select(MSConfig).where(MSConfig.id != existing.id)).all()
        for extra in extras:
            session.delete(extra)
        session.commit()
        return MSConfigOut.model_validate(existing, from_attributes=True)

    cfg = MSConfig(**data.model_dump(), active=True)
    session.add(cfg)
    session.commit()
    session.refresh(cfg)
    return MSConfigOut.model_validate(cfg, from_attributes=True)


@router.put("/metersphere", response_model=MSConfigOut)
def upsert_ms_config(data: MSConfigCreate, _: User = Depends(require_admin), session=Depends(get_session)):
    """Upsert the single Metersphere config. Always active and unique."""
    return create_ms_config(data, _, session)  # reuse logic


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


