"""
监控数据持久化模块
将监控数据保存到本地文件，支持最多10天的历史数据
"""
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class MetricsPersistence:
    def __init__(self, data_dir: str = "/tmp/metrics", retention_days: int = 10):
        """
        初始化监控数据持久化
        
        Args:
            data_dir: 数据存储目录
            retention_days: 数据保留天数
        """
        self.data_dir = data_dir
        self.retention_days = retention_days
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """确保数据目录存在"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            logger.info(f"监控数据目录已创建: {self.data_dir}")
        except Exception as e:
            logger.error(f"创建监控数据目录失败: {e}")
    
    def get_daily_file_path(self, date_str: str = None) -> str:
        """
        获取指定日期的数据文件路径
        
        Args:
            date_str: 日期字符串 (YYYY-MM-DD)，默认为今天
            
        Returns:
            文件路径
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        filename = f"metrics_{date_str}.json"
        return os.path.join(self.data_dir, filename)
    
    def save_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """
        保存监控数据到文件
        
        Args:
            metrics_data: 监控数据字典
            
        Returns:
            是否保存成功
        """
        try:
            # 添加时间戳
            metrics_data["saved_at"] = time.time()
            metrics_data["saved_date"] = datetime.now().strftime("%Y-%m-%d")
            
            file_path = self.get_daily_file_path()
            
            # 读取现有数据
            existing_data = self.load_daily_metrics()
            
            # 添加新数据点
            if "data_points" not in existing_data:
                existing_data["data_points"] = []
            
            existing_data["data_points"].append(metrics_data)
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"监控数据已保存到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存监控数据失败: {e}")
            return False
    
    def load_daily_metrics(self, date_str: str = None) -> Dict[str, Any]:
        """
        加载指定日期的监控数据
        
        Args:
            date_str: 日期字符串，默认为今天
            
        Returns:
            监控数据字典
        """
        try:
            file_path = self.get_daily_file_path(date_str)
            
            if not os.path.exists(file_path):
                return {"data_points": []}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"加载监控数据失败: {e}")
            return {"data_points": []}
    
    def load_historical_metrics(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        加载历史监控数据
        
        Args:
            days: 加载最近几天的数据
            
        Returns:
            历史数据列表
        """
        all_data = []
        
        try:
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                
                daily_data = self.load_daily_metrics(date_str)
                if daily_data.get("data_points"):
                    all_data.extend(daily_data["data_points"])
            
            # 按时间戳排序
            all_data.sort(key=lambda x: x.get("saved_at", 0))
            
        except Exception as e:
            logger.error(f"加载历史监控数据失败: {e}")
        
        return all_data
    
    def cleanup_old_data(self):
        """清理超过保留期的旧数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for filename in os.listdir(self.data_dir):
                if filename.startswith("metrics_") and filename.endswith(".json"):
                    # 提取日期
                    date_str = filename.replace("metrics_", "").replace(".json", "")
                    
                    try:
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        
                        if file_date < cutoff_date:
                            file_path = os.path.join(self.data_dir, filename)
                            os.remove(file_path)
                            logger.info(f"已删除过期监控数据文件: {filename}")
                            
                    except ValueError:
                        # 日期格式不正确，跳过
                        continue
                        
        except Exception as e:
            logger.error(f"清理旧监控数据失败: {e}")
    
    def get_metrics_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        获取监控数据摘要
        
        Args:
            days: 统计最近几天的数据
            
        Returns:
            数据摘要
        """
        try:
            historical_data = self.load_historical_metrics(days)
            
            if not historical_data:
                return {
                    "total_data_points": 0,
                    "date_range": "无数据",
                    "avg_gpu_usage": 0,
                    "total_requests": 0,
                    "avg_response_time": 0
                }
            
            # 计算统计信息
            gpu_usages = []
            response_times = []
            total_requests = 0
            
            for data_point in historical_data:
                if "gpu_info" in data_point and "utilization" in data_point["gpu_info"]:
                    gpu_usages.append(data_point["gpu_info"]["utilization"])
                
                if "avg_response_time" in data_point:
                    response_times.append(data_point["avg_response_time"])
                
                if "total_requests" in data_point:
                    total_requests = max(total_requests, data_point["total_requests"])
            
            # 计算平均值
            avg_gpu_usage = sum(gpu_usages) / len(gpu_usages) if gpu_usages else 0
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # 日期范围
            start_date = datetime.fromtimestamp(historical_data[0]["saved_at"]).strftime("%Y-%m-%d")
            end_date = datetime.fromtimestamp(historical_data[-1]["saved_at"]).strftime("%Y-%m-%d")
            
            return {
                "total_data_points": len(historical_data),
                "date_range": f"{start_date} 到 {end_date}",
                "avg_gpu_usage": round(avg_gpu_usage, 2),
                "total_requests": total_requests,
                "avg_response_time": round(avg_response_time, 2),
                "retention_days": self.retention_days,
                "data_directory": self.data_dir
            }
            
        except Exception as e:
            logger.error(f"获取监控数据摘要失败: {e}")
            return {"error": str(e)}

# 全局实例
metrics_persistence = MetricsPersistence(
    data_dir="/mnt/d/metrics",  # 对应D盘
    retention_days=10
)
