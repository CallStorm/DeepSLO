from datetime import datetime, timedelta, timezone
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select

from db import get_session
from deps import get_current_user, require_admin
from models import ProbeSyncConfig, ProbeResult, MSConfig, ProbeConfig
from schemas import (
    ProbeSyncConfigCreate,
    ProbeSyncConfigUpdate,
    ProbeSyncConfigOut,
    PaginatedProbeResults,
    ProbeResultOut,
)
from services.ms_client import MSClient


router = APIRouter()


def _now_ms() -> int:
    return int(round(time.time() * 1000))


def _dt_now() -> datetime:
    return datetime.utcnow()


@router.get("/sync-config", response_model=Optional[ProbeSyncConfigOut])
def get_sync_config(
    project_ms_id: str = Query(..., description="Metersphere project id"),
    _: str = Depends(get_current_user),
    session=Depends(get_session),
):
    item = session.exec(select(ProbeSyncConfig).where(ProbeSyncConfig.project_ms_id == project_ms_id)).first()
    if not item:
        return None
    return ProbeSyncConfigOut(
        id=item.id,  # type: ignore[arg-type]
        project_ms_id=item.project_ms_id,
        enabled=item.enabled,
        start_time=item.start_time,
        interval_seconds=item.interval_seconds,
        last_synced_start=item.last_synced_start,
        last_run_at=item.last_run_at,
        last_status=item.last_status,
        last_error=item.last_error,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post("/sync-config", response_model=ProbeSyncConfigOut)
def upsert_sync_config(
    payload: ProbeSyncConfigCreate,
    __: str = Depends(require_admin),
    session=Depends(get_session),
):
    cfg = session.exec(select(ProbeSyncConfig).where(ProbeSyncConfig.project_ms_id == payload.project_ms_id)).first()
    now = _dt_now()
    # 确保start_time是naive UTC datetime（如果有时区信息，转换为UTC）
    start_time_utc = payload.start_time
    if start_time_utc is not None:
        if start_time_utc.tzinfo is not None:
            # 有时区信息，转换为UTC naive datetime
            start_time_utc = start_time_utc.astimezone(timezone.utc).replace(tzinfo=None)
    if cfg is None:
        cfg = ProbeSyncConfig(
            project_ms_id=payload.project_ms_id,
            enabled=payload.enabled,
            start_time=start_time_utc,
            interval_seconds=payload.interval_seconds,
            created_at=now,
            updated_at=now,
        )
    else:
        cfg.enabled = payload.enabled
        cfg.start_time = start_time_utc
        cfg.interval_seconds = payload.interval_seconds
        cfg.updated_at = now
    session.add(cfg)
    session.commit()
    session.refresh(cfg)
    return ProbeSyncConfigOut(
        id=cfg.id,  # type: ignore[arg-type]
        project_ms_id=cfg.project_ms_id,
        enabled=cfg.enabled,
        start_time=cfg.start_time,
        interval_seconds=cfg.interval_seconds,
        last_synced_start=cfg.last_synced_start,
        last_run_at=cfg.last_run_at,
        last_status=cfg.last_status,
        last_error=cfg.last_error,
        created_at=cfg.created_at,
        updated_at=cfg.updated_at,
    )


@router.patch("/sync-config", response_model=ProbeSyncConfigOut)
def update_sync_config(
    project_ms_id: str = Query(...),
    payload: ProbeSyncConfigUpdate = None,
    __: str = Depends(require_admin),
    session=Depends(get_session),
):
    cfg = session.exec(select(ProbeSyncConfig).where(ProbeSyncConfig.project_ms_id == project_ms_id)).first()
    if cfg is None:
        raise HTTPException(status_code=404, detail="Sync config not found")
    if payload is None:
        payload = ProbeSyncConfigUpdate()
    if payload.enabled is not None:
        cfg.enabled = payload.enabled
    if payload.start_time is not None:
        # 确保start_time是naive UTC datetime（如果有时区信息，转换为UTC）
        start_time_utc = payload.start_time
        if start_time_utc.tzinfo is not None:
            start_time_utc = start_time_utc.astimezone(timezone.utc).replace(tzinfo=None)
        cfg.start_time = start_time_utc
    if payload.interval_seconds is not None:
        cfg.interval_seconds = payload.interval_seconds
    cfg.updated_at = _dt_now()
    session.add(cfg)
    session.commit()
    session.refresh(cfg)
    return ProbeSyncConfigOut(
        id=cfg.id,  # type: ignore[arg-type]
        project_ms_id=cfg.project_ms_id,
        enabled=cfg.enabled,
        start_time=cfg.start_time,
        interval_seconds=cfg.interval_seconds,
        last_synced_start=cfg.last_synced_start,
        last_run_at=cfg.last_run_at,
        last_status=cfg.last_status,
        last_error=cfg.last_error,
        created_at=cfg.created_at,
        updated_at=cfg.updated_at,
    )


def _ensure_ms_client(session) -> MSClient:
    ms_cfg = session.exec(select(MSConfig).where(MSConfig.active == True)).first()  # noqa: E712
    if not ms_cfg:
        raise HTTPException(status_code=400, detail="Metersphere not configured")
    return MSClient(base_url=ms_cfg.url, ak=ms_cfg.ak, sk=ms_cfg.sk)


@router.post("/sync/run-now")
def run_sync_now(
    project_ms_id: str,
    __: str = Depends(require_admin),
    session=Depends(get_session),
):
    client = _ensure_ms_client(session)
    cfg = session.exec(select(ProbeSyncConfig).where(ProbeSyncConfig.project_ms_id == project_ms_id)).first()
    if cfg is None:
        raise HTTPException(status_code=404, detail="Sync config not found")

    # determine start
    start_dt = cfg.last_synced_start or cfg.start_time
    if start_dt is None:
        probe = session.exec(select(ProbeConfig).where(ProbeConfig.project_ms_id == project_ms_id)).first()
        if probe and probe.create_time:
            start_dt = probe.create_time
        else:
            start_dt = datetime.utcfromtimestamp((_now_ms() - 3600 * 1000) / 1000)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = _now_ms() + 1

    try:
        total_saved = _sync_window(session, client, project_ms_id, start_ms, end_ms)
        cfg.last_run_at = _dt_now()
        cfg.last_status = "SUCCESS"
        # update pointer to latest record startTime + 1ms if any saved
        latest = session.exec(
            select(ProbeResult)
            .where(ProbeResult.project_ms_id == project_ms_id)
            .order_by(ProbeResult.start_time.desc())
        ).first()
        if latest:
            cfg.last_synced_start = latest.start_time + timedelta(milliseconds=1)
        cfg.last_error = None
        cfg.updated_at = _dt_now()
        session.add(cfg)
        session.commit()
        return {"saved": total_saved, "start": start_ms, "end": end_ms}
    except Exception as e:  # noqa: BLE001
        cfg.last_run_at = _dt_now()
        cfg.last_status = "ERROR"
        cfg.last_error = str(e)
        cfg.updated_at = _dt_now()
        session.add(cfg)
        session.commit()
        raise


def _sync_window(session, client: MSClient, project_ms_id: str, start_ms: int, end_ms: int) -> int:
    page = 1
    page_size = 100
    saved = 0
    max_pages = 200
    while page <= max_pages:
        data = client.fetch_scenario_reports(project_id=project_ms_id, start_time_ms=start_ms, end_time_ms=end_ms, page=page, page_size=page_size)
        if data.get("code") != 100200:
            raise RuntimeError(f"MS response error: {data}")
        page_list = (data.get("data") or {}).get("list") or []
        total = (data.get("data") or {}).get("total") or 0
        for item in page_list:
            _upsert_result(session, project_ms_id, item)
            saved += 1
        if page * page_size >= int(total):
            break
        page += 1
    return saved


def _upsert_result(session, project_ms_id: str, item: dict) -> None:
    report_id = str(item.get("id"))
    name = item.get("name") or ""
    start_time_ms = int(item.get("startTime") or 0)
    end_time_ms = int(item.get("endTime") or 0)
    request_duration_ms = item.get("requestDuration")
    status = item.get("status")
    error_count = item.get("errorCount")
    success_count = item.get("successCount")

    rec = session.exec(select(ProbeResult).where(ProbeResult.report_id == report_id)).first()
    if rec is None:
        rec = ProbeResult(
            project_ms_id=str(project_ms_id),
            report_id=report_id,
            name=name,
            start_time=datetime.utcfromtimestamp(start_time_ms / 1000),
            end_time=datetime.utcfromtimestamp(end_time_ms / 1000),
            request_duration_ms=request_duration_ms,
            status=status,
            error_count=error_count,
            success_count=success_count,
            created_at=_dt_now(),
        )
    else:
        rec.project_ms_id = str(project_ms_id)
        rec.name = name
        rec.start_time = datetime.utcfromtimestamp(start_time_ms / 1000)
        rec.end_time = datetime.utcfromtimestamp(end_time_ms / 1000)
        rec.request_duration_ms = request_duration_ms
        rec.status = status
        rec.error_count = error_count
        rec.success_count = success_count
    session.add(rec)
    session.commit()


@router.get("/results", response_model=PaginatedProbeResults)
def list_results(
    project_ms_id: str = Query(...),
    status: Optional[str] = Query(None),
    is_valid: Optional[bool] = Query(None),
    current: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=1000),
    _: str = Depends(get_current_user),
    session=Depends(get_session),
):
    stmt = select(ProbeResult).where(ProbeResult.project_ms_id == project_ms_id)
    if status:
        stmt = stmt.where(ProbeResult.status == status)
    if is_valid is not None:
        stmt = stmt.where(ProbeResult.is_valid == is_valid)
    total = len(session.exec(stmt).all())
    stmt = stmt.order_by(ProbeResult.start_time.desc()).offset((current - 1) * pageSize).limit(pageSize)
    rows = session.exec(stmt).all()
    items = [ProbeResultOut.model_validate(r, from_attributes=True) for r in rows]
    return {"list": items, "total": total, "pageSize": pageSize, "current": current}


@router.patch("/results/{result_id}", response_model=ProbeResultOut)
def update_result_reason(
    result_id: int,
    reason_label: Optional[str] = None,
    is_valid: Optional[bool] = None,
    __: str = Depends(get_current_user),
    session=Depends(get_session),
):
    rec = session.get(ProbeResult, result_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Result not found")
    rec.reason_label = reason_label
    if is_valid is not None:
        rec.is_valid = is_valid
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return ProbeResultOut.model_validate(rec, from_attributes=True)


