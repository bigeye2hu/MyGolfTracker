"""
监控数据存储模块
"""
import time
from typing import Dict, List, Any

# 存储历史数据的内存缓存
metrics_history: Dict[str, List[Any]] = {
    "requests": [],
    "response_times": [],
    "system_stats": [],
    "gpu_stats": []
}

def add_request_metric(request_info: Dict[str, Any]) -> None:
    """添加请求指标"""
    metrics_history["requests"].append(request_info)
    
    # 只保留最近1小时的数据
    current_time = time.time()
    metrics_history["requests"] = [
        req for req in metrics_history["requests"] 
        if current_time - req["timestamp"] < 3600
    ]

def get_metrics_history() -> Dict[str, List[Any]]:
    """获取指标历史数据"""
    return metrics_history
