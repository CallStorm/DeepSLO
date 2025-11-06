import threading
import time
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from ..db import engine
from ..models import ProbeSyncConfig, ProbeResult, MSConfig, ProbeConfig
from .ms_client import MSClient


def _now_ms() -> int:
    return int(round(time.time() * 1000))


def _dt_now() -> datetime:
    return datetime.utcnow()


def _ensure_client(session: Session) -> Optional[MSClient]:
    ms_cfg = session.exec(select(MSConfig).where(MSConfig.active == True)).first()  # noqa: E712
    if not ms_cfg:
        return None
    return MSClient(base_url=ms_cfg.url, ak=ms_cfg.ak, sk=ms_cfg.sk)


def _upsert_result(session: Session, project_ms_id: str, item: dict) -> None:
    report_id = str(item.get("id"))
    rec = session.exec(select(ProbeResult).where(ProbeResult.report_id == report_id)).first()
    payload = dict(
        project_ms_id=str(project_ms_id),
        report_id=report_id,
        name=item.get("name") or "",
        start_time=datetime.utcfromtimestamp(int(item.get("startTime") or 0) / 1000),
        end_time=datetime.utcfromtimestamp(int(item.get("endTime") or 0) / 1000),
        request_duration_ms=item.get("requestDuration"),
        status=item.get("status"),
        error_count=item.get("errorCount"),
        success_count=item.get("successCount"),
    )
    if rec is None:
        rec = ProbeResult(**payload, created_at=_dt_now())
    else:
        for k, v in payload.items():
            setattr(rec, k, v)
    session.add(rec)
    session.commit()


def _sync_window(session: Session, client: MSClient, project_ms_id: str, start_ms: int, end_ms: int) -> int:
    page = 1
    page_size = 100
    saved = 0
    while True:
        data = client.fetch_scenario_reports(project_id=project_ms_id, start_time_ms=start_ms, end_time_ms=end_ms, page=page, page_size=page_size)
        if data.get("code") != 100200:
            raise RuntimeError(f"MS response error: {data}")
        d = data.get("data") or {}
        page_list = d.get("list") or []
        total = int(d.get("total") or 0)
        for item in page_list:
            _upsert_result(session, project_ms_id, item)
            saved += 1
        if page * page_size >= total:
            break
        page += 1
    return saved


def _run_once(session: Session) -> None:
    client = _ensure_client(session)
    if client is None:
        return
    now = _dt_now()
    configs = session.exec(select(ProbeSyncConfig).where(ProbeSyncConfig.enabled == True)).all()  # noqa: E712
    for cfg in configs:
        due = False
        if cfg.last_run_at is None:
            due = True
        else:
            due = now - cfg.last_run_at >= timedelta(seconds=cfg.interval_seconds)
        if not due:
            continue

        start_dt = cfg.last_synced_start or cfg.start_time
        if start_dt is None:
            probe = session.exec(select(ProbeConfig).where(ProbeConfig.project_ms_id == cfg.project_ms_id)).first()
            if probe and probe.create_time:
                start_dt = probe.create_time
            else:
                start_dt = datetime.utcfromtimestamp((_now_ms() - 3600 * 1000) / 1000)
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = _now_ms() + 1
        try:
            _ = _sync_window(session, client, cfg.project_ms_id, start_ms, end_ms)
            cfg.last_run_at = _dt_now()
            cfg.last_status = "SUCCESS"
            latest = session.exec(
                select(ProbeResult)
                .where(ProbeResult.project_ms_id == cfg.project_ms_id)
                .order_by(ProbeResult.start_time.desc())
            ).first()
            if latest:
                cfg.last_synced_start = latest.start_time + timedelta(milliseconds=1)
            cfg.last_error = None
            cfg.updated_at = _dt_now()
            session.add(cfg)
            session.commit()
        except Exception as e:  # noqa: BLE001
            cfg.last_run_at = _dt_now()
            cfg.last_status = "ERROR"
            cfg.last_error = str(e)
            cfg.updated_at = _dt_now()
            session.add(cfg)
            session.commit()


def start_background_sync_loop(interval_seconds: int = 30) -> None:
    def _loop() -> None:
        while True:
            try:
                with Session(engine) as session:
                    _run_once(session)
            except Exception:
                pass
            time.sleep(interval_seconds)

    t = threading.Thread(target=_loop, name="probe-sync-runner", daemon=True)
    t.start()


