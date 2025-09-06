"""
任务管理服务
统一管理所有任务状态和结果
"""
from typing import Dict, Any, Optional
import uuid
import time
from datetime import datetime


class TaskManager:
    """任务管理服务"""
    
    def __init__(self):
        self.job_store: Dict[str, Dict] = {}
        self.analysis_results: Dict[str, Dict[str, Any]] = {}
        self.conversion_jobs: Dict[str, Dict] = {}
    
    def create_job(self, job_type: str = "analysis", **kwargs) -> str:
        """创建新任务"""
        job_id = str(uuid.uuid4())
        self.job_store[job_id] = {
            "id": job_id,
            "type": job_type,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            **kwargs
        }
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return self.job_store.get(job_id)
    
    def update_job_status(self, job_id: str, status: str, progress: int = None, **kwargs) -> bool:
        """更新任务状态"""
        if job_id not in self.job_store:
            return False
        
        self.job_store[job_id]["status"] = status
        self.job_store[job_id]["updated_at"] = datetime.now().isoformat()
        
        if progress is not None:
            self.job_store[job_id]["progress"] = progress
        
        # 更新其他字段
        for key, value in kwargs.items():
            self.job_store[job_id][key] = value
        
        return True
    
    def set_job_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """设置任务结果"""
        if job_id not in self.job_store:
            return False
        
        self.job_store[job_id]["result"] = result
        self.job_store[job_id]["status"] = "done"
        self.job_store[job_id]["completed_at"] = datetime.now().isoformat()
        
        # 同时保存到分析结果中
        self.analysis_results[job_id] = result
        
        return True
    
    def set_job_error(self, job_id: str, error: str) -> bool:
        """设置任务错误"""
        if job_id not in self.job_store:
            return False
        
        self.job_store[job_id]["error"] = error
        self.job_store[job_id]["status"] = "error"
        self.job_store[job_id]["error_at"] = datetime.now().isoformat()
        
        return True
    
    def get_analysis_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取分析结果"""
        return self.analysis_results.get(job_id)
    
    def list_jobs(self, status: str = None) -> Dict[str, Dict[str, Any]]:
        """列出任务"""
        if status is None:
            return self.job_store.copy()
        
        return {
            job_id: job for job_id, job in self.job_store.items()
            if job.get("status") == status
        }
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """清理旧任务"""
        current_time = time.time()
        cleaned_count = 0
        
        jobs_to_remove = []
        for job_id, job in self.job_store.items():
            created_at = job.get("created_at")
            if created_at:
                try:
                    # 解析ISO格式时间
                    created_timestamp = datetime.fromisoformat(created_at).timestamp()
                    if current_time - created_timestamp > max_age_hours * 3600:
                        jobs_to_remove.append(job_id)
                except:
                    # 如果时间格式不正确，也清理掉
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.job_store[job_id]
            self.analysis_results.pop(job_id, None)
            cleaned_count += 1
        
        return cleaned_count


# 全局任务管理器实例
task_manager = TaskManager()
