from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..db import get_session
from ..deps import get_current_user, require_admin
from ..models import Project, MSConfig, User
from ..schemas import ProjectOut
from ..services.ms_client import MSClient


router = APIRouter()


@router.get("/", response_model=List[ProjectOut])
def list_projects(_: User = Depends(get_current_user), session=Depends(get_session)):
    projects = session.exec(select(Project)).all()
    return [ProjectOut(**p.model_dump()) for p in projects]  # type: ignore[arg-type]


@router.post("/sync")
def sync_projects(_: User = Depends(require_admin), session=Depends(get_session)):
    ms_cfg = session.exec(select(MSConfig).where(MSConfig.active == True)).first()  # noqa: E712
    if not ms_cfg:
        raise HTTPException(status_code=400, detail="Metersphere not configured")

    client = MSClient(base_url=ms_cfg.url, ak=ms_cfg.ak, sk=ms_cfg.sk)
    payload = {
        "current": 1,
        "pageSize": 100,
        "sort": {},
        "keyword": "",
        "viewId": "",
        "combineSearch": {"searchMode": "AND", "conditions": []},
        "filter": {},
    }
    resp = client.post("/system/project/page", json=payload)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"MS error: {resp.text}")

    data = resp.json()
    if data.get("code") != 100200:
        raise HTTPException(status_code=400, detail=f"MS response error: {data}")

    items = data.get("data", {}).get("list", [])
    upserted = 0
    for item in items:
        ms_id = str(item.get("id"))
        proj = session.exec(select(Project).where(Project.ms_id == ms_id)).first()
        ms_name = item.get("name") or ""
        ms_description = item.get("description") or None
        create_ts = item.get("createTime")
        ms_createtime = None
        if isinstance(create_ts, (int, float)):
            try:
                ms_createtime = datetime.fromtimestamp(int(create_ts) / 1000)
            except Exception:
                ms_createtime = None

        if proj is None:
            proj = Project(ms_id=ms_id, ms_name=ms_name)
        proj.ms_name = ms_name
        proj.ms_description = ms_description
        proj.ms_createtime = ms_createtime

        session.add(proj)
        upserted += 1

    session.commit()
    return {"ok": True, "count": upserted}


