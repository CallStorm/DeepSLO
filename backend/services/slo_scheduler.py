"""
SLO计算定时任务
定期计算所有项目的SLO
"""
import threading
import time
from datetime import datetime, timedelta
from sqlmodel import Session

from ..db import get_session
from .slo_calculator import calculate_all_projects_slo


def _run_slo_calculation() -> None:
    """执行SLO计算任务"""
    session: Session = next(get_session())
    try:
        calculate_all_projects_slo(session)
    except Exception as e:
        print(f"Error in SLO calculation: {e}")
    finally:
        session.close()


def start_slo_scheduler(interval_hours: int = 1) -> None:
    """
    启动SLO计算定时任务
    
    Args:
        interval_hours: 计算间隔（小时），默认1小时
    """
    def _loop() -> None:
        while True:
            try:
                _run_slo_calculation()
            except Exception as e:
                print(f"Error in SLO scheduler loop: {e}")
            
            # 等待指定时间后再次执行
            time.sleep(interval_hours * 3600)
    
    # 在后台线程中启动
    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    print(f"SLO scheduler started with interval: {interval_hours} hour(s)")

