"""
SLO分析API路由
"""
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select, func, and_
import json

from ..db import get_session
from ..deps import get_current_user
from ..models import (
    User, Project, SLORecord, SLOConfig, ProbeResult
)
from ..services.slo_calculator import calculate_slo_for_period
from ..services.ai_service import stream_ai_analysis


class ChatRequest(BaseModel):
    message: Optional[str] = None


router = APIRouter()


@router.get("/data")
def get_slo_analysis_data(
    project_ms_id: str = Query(..., description="项目ID"),
    _: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    获取SLO分析数据
    包括：SLO配置、当前SLO值、有效拨测数量
    """
    # 验证项目是否存在
    project = session.exec(
        select(Project).where(Project.ms_id == project_ms_id)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取当前月和当前年（使用UTC时间）
    now = datetime.utcnow()
    current_month = f"{now.year}-{now.month:02d}"
    current_year = str(now.year)
    
    # 获取或计算当前月的SLO
    monthly_record = session.exec(
        select(SLORecord).where(
            SLORecord.project_ms_id == project.ms_id,
            SLORecord.period_type == "monthly",
            SLORecord.period_value == current_month
        )
    ).first()
    
    if not monthly_record:
        monthly_record = calculate_slo_for_period(
            session, project.ms_id, "monthly", current_month
        )
    
    # 获取或计算当前年的SLO
    yearly_record = session.exec(
        select(SLORecord).where(
            SLORecord.project_ms_id == project.ms_id,
            SLORecord.period_type == "yearly",
            SLORecord.period_value == current_year
        )
    ).first()
    
    if not yearly_record:
        yearly_record = calculate_slo_for_period(
            session, project.ms_id, "yearly", current_year
        )
    
    # 获取SLO配置
    monthly_config = session.exec(
        select(SLOConfig).where(
            SLOConfig.project_ms_id == project_ms_id,
            SLOConfig.period_type == "monthly"
        )
    ).first()
    
    yearly_config = session.exec(
        select(SLOConfig).where(
            SLOConfig.project_ms_id == project_ms_id,
            SLOConfig.period_type == "yearly"
        )
    ).first()
    
    # 获取当年有效拨测数量（is_valid=1，start_time范围是当年）
    # 使用UTC时间创建日期对象（数据库存储的是UTC时间）
    year_start = datetime(now.year, 1, 1)
    year_end = datetime(now.year + 1, 1, 1)
    
    valid_probe_count = session.exec(
        select(func.count(ProbeResult.id)).where(
            ProbeResult.project_ms_id == project_ms_id,
            ProbeResult.is_valid == True,  # noqa: E712
            ProbeResult.start_time >= year_start,
            ProbeResult.start_time < year_end
        )
    ).one()
    
    # 获取有效拨测列表（只获取name和reason_label）
    valid_probes = session.exec(
        select(ProbeResult).where(
            ProbeResult.project_ms_id == project_ms_id,
            ProbeResult.is_valid == True,  # noqa: E712
            ProbeResult.start_time >= year_start,
            ProbeResult.start_time < year_end
        ).order_by(ProbeResult.start_time.desc())
    ).all()
    
    # 构建响应
    return {
        "project": {
            "ms_id": project.ms_id,
            "ms_name": project.ms_name,
        },
        "slo_config": {
            "monthly": {
                "target": monthly_config.target if monthly_config else None,
                "max_downtime_minutes": monthly_config.max_downtime_minutes if monthly_config else None,
            } if monthly_config else None,
            "yearly": {
                "target": yearly_config.target if yearly_config else None,
                "max_downtime_minutes": yearly_config.max_downtime_minutes if yearly_config else None,
            } if yearly_config else None,
        },
        "slo_current": {
            "monthly": {
                "period_value": current_month,
                "achievement_rate": monthly_record.achievement_rate if monthly_record else 1.0,
                "error_budget_consumption": monthly_record.error_budget_consumption if monthly_record else 0.0,
                "total_downtime_seconds": monthly_record.total_downtime_seconds if monthly_record else 0.0,
            } if monthly_record else None,
            "yearly": {
                "period_value": current_year,
                "achievement_rate": yearly_record.achievement_rate if yearly_record else 1.0,
                "error_budget_consumption": yearly_record.error_budget_consumption if yearly_record else 0.0,
                "total_downtime_seconds": yearly_record.total_downtime_seconds if yearly_record else 0.0,
            } if yearly_record else None,
        },
        "valid_probe_count": valid_probe_count,
        "valid_probes": [
            {"name": probe.name, "reason_label": probe.reason_label}
            for probe in valid_probes
        ],
    }


@router.post("/chat")
def chat_analysis(
    project_ms_id: str = Query(..., description="项目ID"),
    request: ChatRequest = Body(...),
    _: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    流式调用AI模型进行SLO分析
    """
    # 获取SLO分析数据
    analysis_data = get_slo_analysis_data(project_ms_id, _, session)
    
    # 构建prompt
    prompt = build_analysis_prompt(analysis_data, request.message)
    
    # 流式调用AI模型
    return StreamingResponse(
        stream_ai_analysis(session, prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


def build_analysis_prompt(analysis_data: dict, user_message: Optional[str] = None) -> str:
    """
    构建分析prompt
    """
    project = analysis_data["project"]
    slo_config = analysis_data["slo_config"]
    slo_current = analysis_data["slo_current"]
    valid_probes = analysis_data["valid_probes"]
    valid_probe_count = analysis_data["valid_probe_count"]
    
    prompt = f"""你是一位SLO（Service Level Objective）分析专家。请基于以下项目数据进行分析，并给出结构化的分析报告和改进建议。

## 项目信息
- 项目名称: {project['ms_name']}
- 项目ID: {project['ms_id']}

## SLO配置
"""
    
    if slo_config["monthly"]:
        monthly_target = slo_config["monthly"]["target"]
        prompt += f"- 月度SLO目标: {monthly_target:.4%} (可用性 {monthly_target*100:.2f}%)\n"
        prompt += f"- 月度最大允许中断时间: {slo_config['monthly']['max_downtime_minutes']:.2f} 分钟\n"
    
    if slo_config["yearly"]:
        yearly_target = slo_config["yearly"]["target"]
        prompt += f"- 年度SLO目标: {yearly_target:.4%} (可用性 {yearly_target*100:.2f}%)\n"
        prompt += f"- 年度最大允许中断时间: {slo_config['yearly']['max_downtime_minutes']:.2f} 分钟\n"
    
    prompt += "\n## 当前SLO状态\n"
    
    if slo_current["monthly"]:
        monthly = slo_current["monthly"]
        achievement_rate = monthly["achievement_rate"]
        error_budget = monthly["error_budget_consumption"]
        downtime = monthly["total_downtime_seconds"]
        prompt += f"### 月度SLO ({monthly['period_value']})\n"
        prompt += f"- 当前达成率: {achievement_rate:.4%} ({achievement_rate*100:.2f}%)\n"
        prompt += f"- 误差预算消耗率: {error_budget:.4%} ({error_budget*100:.2f}%)\n"
        prompt += f"- 累计中断时间: {downtime:.2f} 秒 ({downtime/60:.2f} 分钟)\n"
        if slo_config["monthly"]:
            target = slo_config["monthly"]["target"]
            if achievement_rate < target:
                prompt += f"- ⚠️ 状态: 未达标 (目标: {target:.4%}, 实际: {achievement_rate:.4%})\n"
            else:
                prompt += f"- ✅ 状态: 达标 (目标: {target:.4%}, 实际: {achievement_rate:.4%})\n"
    
    if slo_current["yearly"]:
        yearly = slo_current["yearly"]
        achievement_rate = yearly["achievement_rate"]
        error_budget = yearly["error_budget_consumption"]
        downtime = yearly["total_downtime_seconds"]
        prompt += f"\n### 年度SLO ({yearly['period_value']})\n"
        prompt += f"- 当前达成率: {achievement_rate:.4%} ({achievement_rate*100:.2f}%)\n"
        prompt += f"- 误差预算消耗率: {error_budget:.4%} ({error_budget*100:.2f}%)\n"
        prompt += f"- 累计中断时间: {downtime:.2f} 秒 ({downtime/60:.2f} 分钟)\n"
        if slo_config["yearly"]:
            target = slo_config["yearly"]["target"]
            if achievement_rate < target:
                prompt += f"- ⚠️ 状态: 未达标 (目标: {target:.4%}, 实际: {achievement_rate:.4%})\n"
            else:
                prompt += f"- ✅ 状态: 达标 (目标: {target:.4%}, 实际: {achievement_rate:.4%})\n"
    
    prompt += f"\n## 有效拨测数据（当年）\n"
    prompt += f"- 有效拨测数量: {valid_probe_count}\n"
    
    if valid_probes:
        prompt += f"\n### 拨测失败记录详情\n"
        # 统计reason_label的分布
        reason_stats = {}
        for probe in valid_probes:
            reason = probe["reason_label"] or "未知原因"
            reason_stats[reason] = reason_stats.get(reason, 0) + 1
        
        prompt += "失败原因统计:\n"
        for reason, count in sorted(reason_stats.items(), key=lambda x: x[1], reverse=True):
            prompt += f"- {reason}: {count} 次\n"
        
        prompt += "\n最近失败记录:\n"
        for i, probe in enumerate(valid_probes[:10], 1):  # 只显示最近10条
            prompt += f"{i}. {probe['name']} - 原因: {probe['reason_label'] or '未知'}\n"
    
    prompt += "\n## 分析任务\n"
    if user_message:
        prompt += f"用户问题: {user_message}\n\n"
    else:
        prompt += "请进行全面的SLO分析，包括以下内容：\n"
    
    prompt += """
请按照以下结构化格式输出分析报告：

## 一、问题分析

### 1.1 当前状态评估
- 描述当前SLO达成情况
- 分析误差预算消耗情况
- 评估风险等级（低/中/高）

### 1.2 问题识别
- 列出发现的主要问题
- 分析问题的影响和严重程度
- 识别问题出现的模式和趋势

### 1.3 根本原因分析
- 分析失败原因分布
- 识别导致SLO未达标的主要原因
- 分析问题发生的规律和特征

## 二、改进建议

### 2.1 短期改进措施（1-2周内）
- 列出可以快速实施的改进措施
- 说明每项措施的具体做法和预期效果
- 优先级排序

### 2.2 中期优化方案（1-3个月）
- 提出系统性的优化方案
- 说明实施步骤和时间安排
- 预期收益和风险控制

### 2.3 长期规划建议（3个月以上）
- 提出架构和流程优化建议
- 说明如何建立SLO监控和预警机制
- 建议建立持续改进机制

## 三、风险预警

### 3.1 当前风险
- 评估当前存在的风险
- 说明风险的严重程度和影响范围

### 3.2 预防措施
- 提出风险预防措施
- 建议设置预警阈值
- 建议建立应急响应机制

## 四、总结

### 4.1 关键发现
- 总结分析的关键发现
- 突出最重要的问题和建议

### 4.2 行动建议
- 列出优先执行的行动项
- 建议责任人和时间节点

---

请确保输出内容专业、准确、 actionable（可执行的）。使用清晰的结构和格式，便于理解和实施。
"""
    
    return prompt

