"""
SLO大屏API路由
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, and_, or_

from ..db import get_session
from ..deps import get_current_user
from ..models import (
    User, Project, SLORecord, SLOConfig, ProbeResult, 
    ProbeConfig
)
from ..schemas import ProjectOut
from ..services.slo_calculator import calculate_slo_for_period


router = APIRouter()


def get_global_status(monthly_record: Optional[SLORecord], yearly_record: Optional[SLORecord], 
                      monthly_config: Optional[SLOConfig], yearly_config: Optional[SLOConfig]) -> str:
    """
    计算全局状态：绿色（健康）、黄色（有风险）、红色（不健康）
    """
    if not monthly_record and not yearly_record:
        return "green"
    
    # 检查是否超标（红色）
    if monthly_record and monthly_config:
        if monthly_record.achievement_rate < monthly_config.target:
            return "red"
        if monthly_record.error_budget_consumption >= 1.0:
            return "red"
    
    if yearly_record and yearly_config:
        if yearly_record.achievement_rate < yearly_config.target:
            return "red"
        if yearly_record.error_budget_consumption >= 1.0:
            return "red"
    
    # 检查是否有风险（黄色）
    # 误差预算消耗超过80%认为有风险
    if monthly_record and monthly_record.error_budget_consumption > 0.8:
        return "yellow"
    if yearly_record and yearly_record.error_budget_consumption > 0.8:
        return "yellow"
    
    # 检查误差预算消耗速度
    if monthly_record and monthly_config:
        # 计算剩余时间比例
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            month_end = datetime(now.year + 1, 1, 1)
        else:
            month_end = datetime(now.year, now.month + 1, 1)
        
        elapsed = (now - month_start).total_seconds()
        total = (month_end - month_start).total_seconds()
        time_ratio = elapsed / total if total > 0 else 1.0
        
        # 如果误差预算消耗速度超过时间进度，认为有风险
        if monthly_record.error_budget_consumption > time_ratio * 1.2:  # 允许20%的缓冲
            return "yellow"
    
    if yearly_record and yearly_config:
        now = datetime.now()
        year_start = datetime(now.year, 1, 1)
        year_end = datetime(now.year + 1, 1, 1)
        
        elapsed = (now - year_start).total_seconds()
        total = (year_end - year_start).total_seconds()
        time_ratio = elapsed / total if total > 0 else 1.0
        
        if yearly_record.error_budget_consumption > time_ratio * 1.2:
            return "yellow"
    
    return "green"


@router.get("/dashboard")
def get_slo_dashboard(
    project_ms_id: str = Query(..., description="项目ID"),
    _: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    获取SLO大屏数据
    """
    # 验证项目是否存在（通过ms_id查找）
    project = session.exec(
        select(Project).where(Project.ms_id == project_ms_id)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取当前月和当前年
    now = datetime.now()
    current_month = f"{now.year}-{now.month:02d}"
    current_year = str(now.year)
    
    # 计算或获取当前月的SLO
    monthly_record = session.exec(
        select(SLORecord).where(
            SLORecord.project_ms_id == project.ms_id,
            SLORecord.period_type == "monthly",
            SLORecord.period_value == current_month
        )
    ).first()
    
    # 如果不存在，尝试计算
    if not monthly_record:
        monthly_record = calculate_slo_for_period(
            session, project.ms_id, "monthly", current_month
        )
    
    # 计算或获取当前年的SLO
    yearly_record = session.exec(
        select(SLORecord).where(
            SLORecord.project_ms_id == project.ms_id,
            SLORecord.period_type == "yearly",
            SLORecord.period_value == current_year
        )
    ).first()
    
    # 如果不存在，尝试计算
    if not yearly_record:
        yearly_record = calculate_slo_for_period(
            session, project.ms_id, "yearly", current_year
        )
    
    # 获取SLO配置
    monthly_config = session.exec(
        select(SLOConfig).where(SLOConfig.period_type == "monthly")
    ).first()
    
    yearly_config = session.exec(
        select(SLOConfig).where(SLOConfig.period_type == "yearly")
    ).first()
    
    # 计算全局状态
    global_status = get_global_status(
        monthly_record, yearly_record, monthly_config, yearly_config
    )
    
    # 计算剩余时间
    def get_remaining_time(period_type: str, period_value: str) -> dict:
        if period_type == "monthly":
            year, month = period_value.split('-')
            year, month = int(year), int(month)
            period_start = datetime(year, month, 1)
            if month == 12:
                period_end = datetime(year + 1, 1, 1)
            else:
                period_end = datetime(year, month + 1, 1)
        else:  # yearly
            year = int(period_value)
            period_start = datetime(year, 1, 1)
            period_end = datetime(year + 1, 1, 1)
        
        remaining = period_end - now
        if remaining.total_seconds() <= 0:
            return {"days": 0, "hours": 0, "minutes": 0}
        
        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        
        return {"days": days, "hours": hours, "minutes": minutes}
    
    monthly_remaining = get_remaining_time("monthly", current_month)
    yearly_remaining = get_remaining_time("yearly", current_year)
    
    # 构建响应
    result = {
        "project": {
            "ms_id": project.ms_id,
            "ms_name": project.ms_name,
        },
        "last_updated": now.isoformat(),
        "global_status": global_status,
        "monthly": {
            "period_value": current_month,
            "target": monthly_config.target if monthly_config else None,
            "achievement_rate": monthly_record.achievement_rate if monthly_record else 1.0,
            "error_budget_consumption": monthly_record.error_budget_consumption if monthly_record else 0.0,
            "remaining_budget": 1.0 - (monthly_record.error_budget_consumption if monthly_record else 0.0),
            "remaining_time": monthly_remaining,
            "total_downtime_seconds": monthly_record.total_downtime_seconds if monthly_record else 0.0,
        },
        "yearly": {
            "period_value": current_year,
            "target": yearly_config.target if yearly_config else None,
            "achievement_rate": yearly_record.achievement_rate if yearly_record else 1.0,
            "error_budget_consumption": yearly_record.error_budget_consumption if yearly_record else 0.0,
            "remaining_budget": 1.0 - (yearly_record.error_budget_consumption if yearly_record else 0.0),
            "remaining_time": yearly_remaining,
            "total_downtime_seconds": yearly_record.total_downtime_seconds if yearly_record else 0.0,
        },
    }
    
    return result


@router.get("/trend")
def get_slo_trend(
    project_ms_id: str = Query(..., description="项目ID"),
    period_type: str = Query("monthly", description="周期类型：monthly"),
    months: int = Query(12, ge=1, le=24, description="查询月份数"),
    _: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    获取SLO趋势数据（仅支持月度）
    """
    if period_type != "monthly":
        raise HTTPException(status_code=400, detail="目前只支持月度趋势查询")
    
    # 获取最近N个月的数据
    now = datetime.now()
    trends = []
    
    for i in range(months - 1, -1, -1):
        # 计算月份
        target_date = now - timedelta(days=30 * i)
        month_value = f"{target_date.year}-{target_date.month:02d}"
        
        # 获取或计算SLO记录
        record = session.exec(
            select(SLORecord).where(
                SLORecord.project_ms_id == project_ms_id,
                SLORecord.period_type == "monthly",
                SLORecord.period_value == month_value
            )
        ).first()
        
        if not record:
            record = calculate_slo_for_period(
                session, project_ms_id, "monthly", month_value
            )
        
        # 获取配置
        config = session.exec(
            select(SLOConfig).where(SLOConfig.period_type == "monthly")
        ).first()
        
        if record:
            trends.append({
                "period": month_value,
                "achievement_rate": record.achievement_rate,
                "target": config.target if config else None,
                "error_budget_consumption": record.error_budget_consumption,
            })
        else:
            # 如果没有数据，使用默认值
            trends.append({
                "period": month_value,
                "achievement_rate": 1.0,
                "target": config.target if config else None,
                "error_budget_consumption": 0.0,
            })
    
    return {"trends": trends}


@router.get("/events")
def get_slo_events(
    project_ms_id: str = Query(..., description="项目ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current: int = Query(1, ge=1, description="当前页"),
    pageSize: int = Query(20, ge=1, le=100, description="每页大小"),
    _: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    获取SLO异常事件列表（拨测失败记录）
    """
    # 默认查询最近7天
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(days=7)
    
    # 查询失败记录（is_valid=1表示失败）
    query = select(ProbeResult).where(
        ProbeResult.project_ms_id == project_ms_id,
        ProbeResult.is_valid == True,  # noqa: E712
        ProbeResult.start_time >= start_time,
        ProbeResult.start_time <= end_time
    ).order_by(ProbeResult.start_time.desc())
    
    # 计算总数
    count_query = select(func.count()).select_from(
        select(ProbeResult).where(
            ProbeResult.project_ms_id == project_ms_id,
            ProbeResult.is_valid == True,  # noqa: E712
            ProbeResult.start_time >= start_time,
            ProbeResult.start_time <= end_time
        ).subquery()
    )
    total = session.exec(count_query).one()
    
    # 分页查询
    offset = (current - 1) * pageSize
    results = session.exec(query.offset(offset).limit(pageSize)).all()
    
    events = []
    for result in results:
        events.append({
            "id": result.id,
            "name": result.name,
            "start_time": result.start_time.isoformat(),
            "reason_label": result.reason_label,
            "status": result.status,
        })
    
    return {
        "list": events,
        "total": total,
        "current": current,
        "pageSize": pageSize,
    }

