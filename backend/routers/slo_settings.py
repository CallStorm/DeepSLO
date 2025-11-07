from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..db import get_session
from ..deps import get_current_user
from ..models import SLOConfig, User
from ..schemas import SLOConfigCreate, SLOConfigOut, SLOConfigUpdate


router = APIRouter()


def calculate_max_downtime_minutes(period_type: str, target: float) -> float:
    """计算允许最大中断时间（分钟）
    
    Args:
        period_type: "monthly" 或 "yearly"
        target: SLO目标值，如0.9999表示99.99%
    
    Returns:
        允许最大中断时间（分钟）
    """
    if period_type == "monthly":
        # 月度：30天 = 30 * 24 * 60 = 43200分钟
        total_minutes = 30 * 24 * 60
    elif period_type == "yearly":
        # 年度：365天 = 365 * 24 * 60 = 525600分钟
        total_minutes = 365 * 24 * 60
    else:
        raise ValueError(f"Invalid period_type: {period_type}")
    
    # 允许中断时间 = 总时间 * (1 - SLO目标)
    max_downtime = total_minutes * (1 - target)
    return round(max_downtime, 2)


@router.get("/", response_model=List[SLOConfigOut])
def list_slo_configs(_: User = Depends(get_current_user), session=Depends(get_session)):
    """获取所有SLO配置"""
    configs = session.exec(select(SLOConfig)).all()
    return [SLOConfigOut(**c.model_dump()) for c in configs]  # type: ignore[arg-type]


@router.post("/", response_model=SLOConfigOut)
def create_slo_config(data: SLOConfigCreate, _: User = Depends(get_current_user), session=Depends(get_session)):
    """创建SLO配置
    
    年度和月度各自最多只能创建一条
    """
    # 验证period_type
    if data.period_type not in ["monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="period_type must be 'monthly' or 'yearly'")
    
    # 验证target范围（0到1之间）
    if not 0 < data.target < 1:
        raise HTTPException(status_code=400, detail="target must be between 0 and 1")
    
    # 检查是否已存在相同类型的配置
    existing = session.exec(
        select(SLOConfig).where(SLOConfig.period_type == data.period_type)
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"{'月度' if data.period_type == 'monthly' else '年度'}SLO配置已存在，请先删除或更新现有配置"
        )
    
    # 计算允许最大中断时间
    max_downtime_minutes = calculate_max_downtime_minutes(data.period_type, data.target)
    
    # 创建配置
    config = SLOConfig(
        period_type=data.period_type,
        target=data.target,
        metric_type=data.metric_type,
        max_downtime_minutes=max_downtime_minutes,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return SLOConfigOut(**config.model_dump())  # type: ignore[arg-type]


@router.put("/{config_id}", response_model=SLOConfigOut)
def update_slo_config(
    config_id: int,
    data: SLOConfigUpdate,
    _: User = Depends(get_current_user),
    session=Depends(get_session)
):
    """更新SLO配置"""
    config = session.get(SLOConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="SLO配置不存在")
    
    # 如果更新target，需要重新计算max_downtime_minutes
    if data.target is not None:
        if not 0 < data.target < 1:
            raise HTTPException(status_code=400, detail="target must be between 0 and 1")
        config.target = data.target
        config.max_downtime_minutes = calculate_max_downtime_minutes(config.period_type, data.target)
        config.updated_at = datetime.now()
    
    session.add(config)
    session.commit()
    session.refresh(config)
    return SLOConfigOut(**config.model_dump())  # type: ignore[arg-type]


@router.delete("/{config_id}")
def delete_slo_config(config_id: int, _: User = Depends(get_current_user), session=Depends(get_session)):
    """删除SLO配置"""
    config = session.get(SLOConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="SLO配置不存在")
    session.delete(config)
    session.commit()
    return {"ok": True}


@router.get("/calculate-downtime")
def calculate_downtime(period_type: str, target: float):
    """计算允许最大中断时间（用于前端实时显示）"""
    if period_type not in ["monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="period_type must be 'monthly' or 'yearly'")
    if not 0 < target < 1:
        raise HTTPException(status_code=400, detail="target must be between 0 and 1")
    
    max_downtime = calculate_max_downtime_minutes(period_type, target)
    return {
        "period_type": period_type,
        "target": target,
        "max_downtime_minutes": max_downtime,
    }

