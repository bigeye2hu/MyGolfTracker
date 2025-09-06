# GolfTracker 架构文档

## 项目概述

GolfTracker 是一个基于 FastAPI 的高尔夫挥杆视频分析系统，使用 YOLOv8 进行杆头检测，提供轨迹优化和挥杆状态分析功能。

## 架构设计

### 整体架构

```
app/
├── config/              # 配置管理
│   ├── __init__.py
│   └── settings.py      # 统一配置管理
├── services/            # 服务层
│   ├── html_generator.py      # HTML生成服务
│   ├── video_analysis.py      # 视频分析服务
│   ├── video_processing.py    # 视频处理服务
│   ├── task_manager.py        # 任务管理服务
│   ├── file_service.py        # 文件服务
│   ├── logging_service.py     # 日志服务
│   └── response_service.py    # 响应服务
├── utils/               # 工具函数层
│   ├── helpers.py             # 辅助函数
│   └── error_handlers.py      # 错误处理工具
└── routes/              # 路由层
    └── analyze.py             # 主路由文件
```

### 服务层设计

#### 1. 配置管理 (config/)
- **settings.py**: 统一管理所有配置项
- **功能**: 服务器配置、视频分析配置、轨迹优化配置等

#### 2. 核心服务 (services/)

##### 任务管理服务 (task_manager.py)
- **功能**: 统一管理任务状态和结果
- **主要方法**:
  - `create_job()`: 创建新任务
  - `update_job_status()`: 更新任务状态
  - `set_job_result()`: 设置任务结果
  - `get_analysis_result()`: 获取分析结果

##### 文件服务 (file_service.py)
- **功能**: 统一管理文件操作
- **主要方法**:
  - `save_uploaded_file()`: 保存上传文件
  - `get_video_info()`: 获取视频信息
  - `extract_frame()`: 提取视频帧
  - `is_supported_format()`: 检查文件格式

##### 视频处理服务 (video_processing.py)
- **功能**: 核心视频分析逻辑
- **主要方法**:
  - `analyze_video()`: 分析视频
  - `clean_trajectory()`: 清理轨迹数据
  - `safe_float()`: 安全浮点数转换

##### HTML生成服务 (html_generator.py)
- **功能**: 生成分析结果页面
- **主要方法**:
  - `generate_training_data_html()`: 生成训练数据页面
  - `generate_failure_frames_html()`: 生成失败帧页面

##### 日志服务 (logging_service.py)
- **功能**: 统一日志记录
- **主要方法**:
  - `info()`, `warning()`, `error()`, `debug()`: 各级别日志
  - `log_api_request()`: API请求日志
  - `log_video_analysis()`: 视频分析日志

##### 响应服务 (response_service.py)
- **功能**: 统一API响应格式
- **主要方法**:
  - `success()`: 成功响应
  - `error()`: 错误响应
  - `html_response()`: HTML响应
  - `job_response()`: 任务响应

#### 3. 工具函数 (utils/)

##### 辅助函数 (helpers.py)
- **功能**: 通用辅助函数
- **主要函数**:
  - `get_mp_landmark_names()`: MediaPipe关键点名称
  - `calculate_trajectory_distance()`: 轨迹距离计算
  - `clean_json_data()`: JSON数据清理
  - `check_video_compatibility()`: 视频兼容性检查

##### 错误处理 (error_handlers.py)
- **功能**: 统一错误处理
- **主要装饰器**:
  - `@handle_api_errors`: API错误处理
  - `@handle_sync_errors`: 同步函数错误处理
  - `validate_required_params()`: 参数验证
  - `validate_file_upload()`: 文件上传验证

## 数据流

### 视频分析流程

1. **文件上传** → 文件服务验证格式和大小
2. **任务创建** → 任务管理服务创建分析任务
3. **视频处理** → 视频处理服务执行分析
4. **结果存储** → 任务管理服务存储结果
5. **页面生成** → HTML生成服务创建结果页面

### 错误处理流程

1. **异常捕获** → 错误处理装饰器捕获异常
2. **日志记录** → 日志服务记录错误详情
3. **响应生成** → 响应服务生成错误响应
4. **用户通知** → 返回友好的错误信息

## 配置管理

### 服务器配置
```python
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 5005,
    "max_concurrent_conversions": 3,
    "default_server_load": "normal"
}
```

### 视频分析配置
```python
VIDEO_ANALYSIS_CONFIG = {
    "default_resolution": "480",
    "default_confidence": "0.01",
    "default_iou": "0.7",
    "default_max_det": "10",
    "supported_formats": ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'],
    "max_file_size": 100 * 1024 * 1024,  # 100MB
    "jpeg_quality": 90
}
```

## 部署说明

### 环境要求
- Python 3.9+
- FastAPI
- OpenCV
- YOLOv8
- 其他依赖见 requirements.txt

### 启动命令
```bash
# 开发环境
uvicorn app.main:app --host 0.0.0.0 --port 5005 --reload

# 生产环境
uvicorn app.main:app --host 0.0.0.0 --port 5005
```

## 维护说明

### 日志文件
- 应用日志: `golftracker.log`
- 错误日志: 包含在应用日志中

### 配置修改
- 修改 `app/config/settings.py` 中的配置项
- 重启服务使配置生效

### 服务扩展
- 新增服务: 在 `app/services/` 目录下创建新服务
- 服务注册: 在 `app/routes/analyze.py` 中导入和使用

## 性能优化

### 已实现的优化
1. **服务层分离**: 提高代码可维护性
2. **配置统一管理**: 减少硬编码
3. **错误处理统一**: 提高系统稳定性
4. **日志记录完善**: 便于问题排查

### 建议的进一步优化
1. **数据库集成**: 替换内存存储
2. **缓存机制**: 提高响应速度
3. **异步处理**: 提高并发能力
4. **监控告警**: 实时监控系统状态
