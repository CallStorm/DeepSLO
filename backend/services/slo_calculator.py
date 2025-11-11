"""
SLO计算服务
用于计算SLO达成率、误差预算消耗等指标
"""
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlmodel import Session, select

from ..models import ProbeResult, ProbeConfig, SLOConfig, SLORecord, Project

try:
    from croniter import croniter
    HAS_CRONITER = True
except ImportError:
    HAS_CRONITER = False


def parse_cron_interval(cron_expr: str) -> Optional[float]:
    """
    解析cron表达式，计算执行间隔（秒）
    
    Args:
        cron_expr: cron表达式，格式为 Quartz cron (秒 分 时 日 月 周 [年])
    
    Returns:
        间隔时间（秒），如果无法解析则返回None
    """
    if not cron_expr:
        return None
    
    # 先尝试简单的模式匹配（不依赖croniter）
    parts = cron_expr.strip().split()
    if len(parts) >= 6:
        # Quartz格式: 秒 分 时 日 月 周
        sec, min_part, hour, dom, mon, dow = parts[:6]
        
        # 每N分钟: 0 */N * * * ?
        if sec == '0' and min_part.startswith('*/'):
            try:
                minutes = int(min_part[2:])
                return minutes * 60
            except ValueError:
                pass
        
        # 每N小时: 0 0 */N * * ?
        if sec == '0' and min_part in ('0', '00') and hour.startswith('*/'):
            try:
                hours = int(hour[2:])
                return hours * 3600
            except ValueError:
                pass
        
        # 每N秒: */N * * * * ?
        if sec.startswith('*/') and min_part == '*' and hour == '*' and dom == '*' and mon == '*':
            try:
                seconds = int(sec[2:])
                return seconds
            except ValueError:
                pass
    
    # 如果croniter可用，尝试使用它进行精确计算
    if HAS_CRONITER:
        try:
            base_time = datetime.now()
            iter1 = croniter(cron_expr, base_time)
            next_time1 = iter1.get_next(datetime)
            next_time2 = iter1.get_next(datetime)
            
            # 计算两次执行的时间差（秒）
            interval = (next_time2 - next_time1).total_seconds()
            return interval
        except Exception:
            pass
    
    return None


def calculate_downtime_for_project(
    session: Session,
    project_ms_id: str,
    start_time: datetime,
    end_time: datetime
) -> float:
    """
    计算项目在指定时间段内的累计中断时间（秒）
    
    规则：
    1. 连续两次拨测失败（is_valid=1），记录一次中断时间
    2. 中断时间 = 两次失败的start_time的时间差（秒）
    3. 判断连续两次失败的标准：两次的时间间隔等于probeconfig里的schedule_cron表达式表示的间隔
    
    Args:
        session: 数据库会话
        project_ms_id: 项目ID
        start_time: 开始时间
        end_time: 结束时间
    
    Returns:
        累计中断时间（秒）
    """
    # 获取项目的拨测配置
    probe_configs = session.exec(
        select(ProbeConfig).where(ProbeConfig.project_ms_id == project_ms_id)
    ).all()
    
    if not probe_configs:
        return 0.0
    
    # 获取时间段内的所有失败拨测结果（is_valid=1表示失败）
    failed_results = session.exec(
        select(ProbeResult)
        .where(
            ProbeResult.project_ms_id == project_ms_id,
            ProbeResult.is_valid == True,  # noqa: E712
            ProbeResult.start_time >= start_time,
            ProbeResult.start_time < end_time
        )
        .order_by(ProbeResult.start_time.asc())
    ).all()
    
    if len(failed_results) < 2:
        return 0.0
    
    # 获取项目的拨测配置（使用第一个配置的schedule_cron）
    # 对于一个项目，通常只有一个拨测配置
    expected_interval = 300.0  # 默认5分钟
    if probe_configs:
        probe_config = probe_configs[0]  # 使用第一个配置
        if probe_config.schedule_cron:
            parsed_interval = parse_cron_interval(probe_config.schedule_cron)
            if parsed_interval is not None:
                expected_interval = parsed_interval
    
    total_downtime = 0.0
    
    # 直接处理所有失败结果（已按时间排序）
    i = 0
    while i < len(failed_results) - 1:
        current = failed_results[i]
        next_result = failed_results[i + 1]
        
        # 计算两次失败的时间间隔
        time_diff = (next_result.start_time - current.start_time).total_seconds()
        
        # 判断是否为连续失败（时间间隔在期望间隔的±10%范围内）
        tolerance = expected_interval * 0.1
        if abs(time_diff - expected_interval) <= tolerance:
            # 连续失败，记录中断时间
            total_downtime += time_diff
            i += 2  # 跳过下一项，因为已经计算过了
        else:
            i += 1
    
    return total_downtime


def calculate_slo_for_period(
    session: Session,
    project_ms_id: str,
    period_type: str,
    period_value: str
) -> Optional[SLORecord]:
    """
    计算指定周期内的SLO
    
    Args:
        session: 数据库会话
        project_ms_id: 项目ID
        period_type: 周期类型（"monthly" 或 "yearly"）
        period_value: 周期值（月度如 "2025-11"，年度如 "2025"）
    
    Returns:
        SLORecord对象
    """
    # 解析周期值，确定开始和结束时间
    if period_type == "monthly":
        # 月度：2025-11 -> 2025-11-01 00:00:00 到 2025-12-01 00:00:00
        try:
            year, month = period_value.split('-')
            year = int(year)
            month = int(month)
            start_time = datetime(year, month, 1)
            if month == 12:
                end_time = datetime(year + 1, 1, 1)
            else:
                end_time = datetime(year, month + 1, 1)
        except ValueError:
            return None
    elif period_type == "yearly":
        # 年度：2025 -> 2025-01-01 00:00:00 到 2026-01-01 00:00:00
        try:
            year = int(period_value)
            start_time = datetime(year, 1, 1)
            end_time = datetime(year + 1, 1, 1)
        except ValueError:
            return None
    else:
        return None
    
    # 获取SLO配置（按项目+周期）
    slo_config = session.exec(
        select(SLOConfig).where(
            SLOConfig.project_ms_id == project_ms_id,
            SLOConfig.period_type == period_type
        )
    ).first()
    
    if not slo_config:
        return None
    
    # 计算累计中断时间（只计算到当前时间）
    now = datetime.now()
    calc_end_time = min(end_time, now)
    total_downtime_seconds = calculate_downtime_for_project(
        session, project_ms_id, start_time, calc_end_time
    )
    
    # 计算周期总时间（秒）
    # 如果周期还没结束，使用已过去的时间
    if period_type == "monthly":
        if now < end_time:
            # 当前周期，使用已过去的时间
            elapsed_seconds = (now - start_time).total_seconds()
            total_seconds = max(elapsed_seconds, 1.0)  # 避免除以0
        else:
            # 已完成的周期，使用完整30天
            total_seconds = 30 * 24 * 60 * 60
    else:  # yearly
        if now < end_time:
            # 当前周期，使用已过去的时间
            elapsed_seconds = (now - start_time).total_seconds()
            total_seconds = max(elapsed_seconds, 1.0)  # 避免除以0
        else:
            # 已完成的周期，使用完整365天
            total_seconds = 365 * 24 * 60 * 60
    
    # 计算SLO达成率
    # 可用时间 = 总时间 - 中断时间
    available_seconds = total_seconds - total_downtime_seconds
    achievement_rate = available_seconds / total_seconds if total_seconds > 0 else 1.0
    
    # 计算误差预算消耗率
    # 误差预算 = 总时间 * (1 - SLO目标)
    error_budget_seconds = total_seconds * (1 - slo_config.target)
    if error_budget_seconds > 0:
        error_budget_consumption = total_downtime_seconds / error_budget_seconds
    else:
        error_budget_consumption = 0.0
    
    # 限制在0-1范围内
    error_budget_consumption = min(1.0, max(0.0, error_budget_consumption))
    
    # 查找或创建SLORecord
    slo_record = session.exec(
        select(SLORecord).where(
            SLORecord.project_ms_id == project_ms_id,
            SLORecord.period_type == period_type,
            SLORecord.period_value == period_value
        )
    ).first()
    
    now = datetime.now()
    if slo_record:
        # 更新现有记录
        slo_record.total_downtime_seconds = total_downtime_seconds
        slo_record.achievement_rate = achievement_rate
        slo_record.error_budget_consumption = error_budget_consumption
        slo_record.calculated_at = now
        slo_record.updated_at = now
    else:
        # 创建新记录
        slo_record = SLORecord(
            project_ms_id=project_ms_id,
            period_type=period_type,
            period_value=period_value,
            total_downtime_seconds=total_downtime_seconds,
            achievement_rate=achievement_rate,
            error_budget_consumption=error_budget_consumption,
            calculated_at=now,
            created_at=now,
            updated_at=now
        )
        session.add(slo_record)
    
    session.commit()
    session.refresh(slo_record)
    return slo_record


def calculate_all_projects_slo(session: Session) -> None:
    """
    计算所有项目的SLO（当前月和当前年）
    """
    projects = session.exec(select(Project)).all()
    now = datetime.now()
    
    # 当前月
    current_month = f"{now.year}-{now.month:02d}"
    # 当前年
    current_year = str(now.year)
    
    for project in projects:
        # 计算月度SLO
        try:
            calculate_slo_for_period(
                session, project.ms_id, "monthly", current_month
            )
        except Exception as e:
            print(f"Error calculating monthly SLO for project {project.ms_id}: {e}")
        
        # 计算年度SLO
        try:
            calculate_slo_for_period(
                session, project.ms_id, "yearly", current_year
            )
        except Exception as e:
            print(f"Error calculating yearly SLO for project {project.ms_id}: {e}")

