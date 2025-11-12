from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select

from ..db import get_session
from ..deps import get_current_user, require_admin
from ..models import MSConfig, ProbeConfig, User
from ..schemas import ProbeConfigOut
from ..services.ms_client import MSClient


router = APIRouter()


def _ms_ts_to_dt(value: Optional[int]) -> Optional[datetime]:
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(int(value) / 1000)
        except Exception:
            return None
    return None


@router.get("/", response_model=Optional[ProbeConfigOut])
def get_probe(
    project_ms_id: str = Query(..., description="Metersphere project id"),
    _: User = Depends(get_current_user),
    session=Depends(get_session),
):
    item = session.exec(
        select(ProbeConfig).where(ProbeConfig.project_ms_id == project_ms_id)
    ).first()
    if not item:
        return None
    return ProbeConfigOut.model_validate(item, from_attributes=True)


@router.post("/sync", response_model=Optional[ProbeConfigOut])
def sync_probe(
    payload: dict,
    __: User = Depends(require_admin),
    session=Depends(get_session),
):
    project_ms_id = payload.get("project_ms_id") or payload.get("projectId")
    if not project_ms_id:
        raise HTTPException(status_code=400, detail="project_ms_id is required")

    ms_cfg = session.exec(select(MSConfig).where(MSConfig.active == True)).first()  # noqa: E712
    if not ms_cfg:
        raise HTTPException(status_code=400, detail="Metersphere not configured")

    client = MSClient(base_url=ms_cfg.url, ak=ms_cfg.ak, sk=ms_cfg.sk)
    ms_payload = {
        "current": 1,
        "pageSize": 10,
        "sort": {},
        "keyword": "",
        "viewId": "all_data",
        "combineSearch": {
            "searchMode": "AND",
            "conditions": [
                {
                    "value": "拨测",
                    "operator": "EQUALS",
                    "customField": False,
                    "name": "name",
                    "customFieldType": "",
                }
            ],
        },
        "projectId": str(project_ms_id),
        "moduleIds": [],
        "filter": {},
    }

    resp = client.post("/api/scenario/page", json=ms_payload)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"MS error: {resp.text}")

    data = resp.json()
    if data.get("code") != 100200:
        raise HTTPException(status_code=400, detail=f"MS response error: {data}")

    items = data.get("data", {}).get("list", []) or []
    if not items:
        # No probe scenario found; clear existing if any
        existing = session.exec(
            select(ProbeConfig).where(ProbeConfig.project_ms_id == str(project_ms_id))
        ).first()
        if existing:
            session.delete(existing)
            session.commit()
        return None

    item = items[0]
    scenario_id = str(item.get("id"))

    probe = session.exec(select(ProbeConfig).where(ProbeConfig.scenario_id == scenario_id)).first()
    if probe is None:
        probe = ProbeConfig(project_ms_id=str(project_ms_id), scenario_id=scenario_id, name=item.get("name") or "")

    probe.project_ms_id = str(project_ms_id)
    probe.scenario_id = scenario_id
    probe.name = item.get("name") or ""
    probe.priority = item.get("priority")
    probe.status = item.get("status")
    probe.step_total = item.get("stepTotal")
    probe.request_pass_rate = item.get("requestPassRate")
    probe.last_report_status = item.get("lastReportStatus")
    probe.last_report_id = item.get("lastReportId")
    probe.num = item.get("num")
    probe.environment_name = item.get("environmentName")

    sched = item.get("scheduleConfig") or {}
    probe.schedule_enable = bool(sched.get("enable")) if sched is not None else None
    probe.schedule_cron = (sched.get("cron") if isinstance(sched, dict) else None) or None

    probe.next_trigger_time = _ms_ts_to_dt(item.get("nextTriggerTime"))
    probe.create_time = _ms_ts_to_dt(item.get("createTime"))
    probe.update_time = _ms_ts_to_dt(item.get("updateTime"))

    session.add(probe)
    session.commit()
    session.refresh(probe)

    return ProbeConfigOut.model_validate(probe, from_attributes=True)



