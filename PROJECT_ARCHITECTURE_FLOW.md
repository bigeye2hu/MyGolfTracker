# MyGolfTracker 项目架构流程图

## 🏗️ 整体系统架构

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                MyGolfTracker 系统架构                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │   前端界面层     │    │   API网关层      │    │   业务逻辑层     │              │
│  │                │    │                │    │                │              │
│  │ • HTML/CSS/JS  │◄──►│ • FastAPI      │◄──►│ • 视频分析服务   │              │
│  │ • 视频播放器    │    │ • 路由管理      │    │ • 轨迹优化算法   │              │
│  │ • 数据可视化    │    │ • 请求处理      │    │ • 状态机管理     │              │
│  │ • 用户交互      │    │ • 响应格式化    │    │ • 策略管理器     │              │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘              │
│           │                       │                       │                    │
│           │                       │                       │                    │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │   数据存储层     │    │   检测引擎层     │    │   工具服务层     │              │
│  │                │    │                │    │                │              │
│  │ • 临时文件存储   │    │ • YOLOv8检测器  │    │ • FFmpeg处理    │              │
│  │ • 分析结果缓存   │    │ • 姿态检测器    │    │ • 文件管理服务   │              │
│  │ • 训练数据收集   │    │ • 杆头检测      │    │ • 日志服务      │              │
│  │ • 模型文件      │    │ • 置信度过滤    │    │ • 响应服务      │              │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔌 API接口总览

### 核心分析接口
| 接口 | 方法 | 路径 | 功能 | 输入 | 输出 |
|------|------|------|------|------|------|
| 视频分析 | POST | `/analyze` | 同步视频分析 | `file`, `handed` | 完整分析结果 |
| 异步视频分析 | POST | `/video` | 异步视频分析 | `file`, `resolution`, `confidence`, `iou`, `max_det`, `optimization_strategy` | 任务ID |
| 分析状态 | GET | `/video/status` | 查询分析进度 | `job_id` | 状态和结果 |
| 结果可视化 | GET | `/visualize/{result_id}` | 显示分析结果 | `result_id` | HTML页面 |

### 策略管理接口
| 接口 | 方法 | 路径 | 功能 | 输入 | 输出 |
|------|------|------|------|------|------|
| 获取策略列表 | GET | `/strategies` | 获取所有优化策略 | 无 | 策略列表 |
| 分类策略 | GET | `/strategies/{category}` | 获取分类策略 | `category` | 分类策略列表 |
| 策略测试 | GET | `/strategy-test` | 测试策略功能 | 无 | 测试结果 |

### 系统管理接口
| 接口 | 方法 | 路径 | 功能 | 输入 | 输出 |
|------|------|------|------|------|------|
| 健康检查 | GET | `/health` | 系统健康状态 | 无 | 状态信息 |
| 服务器测试 | GET | `/server-test` | 服务器功能测试 | 无 | 测试结果 |
| 支持格式 | GET | `/supported-formats` | 支持的视频格式 | 无 | 格式列表 |
| 转换指南 | GET | `/conversion-guide` | 视频转换指南 | 无 | 指南页面 |

### 训练数据接口
| 接口 | 方法 | 路径 | 功能 | 输入 | 输出 |
|------|------|------|------|------|------|
| 训练数据下载 | GET | `/training-data/zip/{job_id}` | 下载训练数据 | `job_id` | ZIP文件 |

## 🔄 数据处理流程

### 1. 视频上传与预处理
```
用户上传视频
    ↓
文件类型检查 (MP4, MOV, AVI)
    ↓
视频兼容性验证
    ↓
临时文件存储
    ↓
视频规格提取 (分辨率, 帧率, 时长)
```

### 2. 异步分析流程
```
POST /video
    ↓
生成任务ID (UUID)
    ↓
启动后台分析线程
    ↓
返回任务ID给前端
    ↓
前端轮询 GET /video/status
    ↓
返回分析进度和结果
```

### 3. 核心分析流程
```
视频帧提取 (FFmpeg)
    ↓
┌─────────────────┬─────────────────┐
│   YOLOv8检测    │   姿态检测      │
│                │                │
│ • 杆头检测      │ • MediaPipe     │
│ • 置信度过滤    │ • 关键点提取    │
│ • 坐标转换      │ • 姿态分析      │
└─────────────────┴─────────────────┘
    ↓
轨迹数据整合
    ↓
自动补齐算法处理
    ↓
挥杆状态机分析
    ↓
结果数据生成
```

### 4. 自动补齐算法流程
```
原始轨迹数据 (100帧)
    ↓
识别有效检测点 (非None, 非零坐标)
    ↓
查找缺失帧间隔 (最大10帧)
    ↓
线性插值填补
    ↓
生成补齐后轨迹
    ↓
创建right_frame_detections
    ↓
标记补齐帧 (is_filled: true)
```

## 🎯 前端模块架构

### 核心模块
```
main.js (主控制器)
├── upload-module.js (文件上传)
├── video-player-module.js (视频播放)
├── results-module.js (结果显示)
├── trajectory-module.js (轨迹管理)
├── frame-analysis-module.js (帧分析)
├── dual-player-module.js (双画面对比)
├── swing-visualization-module.js (挥杆可视化)
└── json-output-module.js (JSON输出)
```

### 数据流
```
用户上传视频
    ↓
upload-module.js 处理上传
    ↓
启动异步分析 (POST /video)
    ↓
轮询分析状态 (GET /video/status)
    ↓
分析完成，更新各模块显示
    ├── video-player-module.js (动态视频分析)
    ├── trajectory-module.js (轨迹信息)
    ├── frame-analysis-module.js (帧分析)
    ├── dual-player-module.js (双画面对比)
    └── results-module.js (统计信息)
```

## 🔧 配置管理

### 环境配置
```python
# app/config/settings.py
VIDEO_ANALYSIS_CONFIG = {
    "default_resolution": "640×640",
    "default_confidence": "0.01", 
    "default_iou": "0.7",
    "default_max_det": "10",
    "default_optimization_strategy": "auto_fill"
}

SERVER_CONFIG = {
    "max_concurrent_conversions": 2,
    "default_server_load": "normal"
}
```

### 模型配置
```python
# analyzer/config.py
MODEL_PATH = os.getenv("MODEL_PATH", "data/best.pt")
```

## 📊 数据格式

### 输入数据
- **视频文件**: MP4, MOV, AVI格式
- **参数**: 分辨率, 置信度, IoU阈值, 最大检测数, 优化策略

### 输出数据
```json
{
  "job_id": "uuid",
  "status": "completed|processing|failed",
  "result": {
    "basic_info": {
      "num_frames": 100,
      "video_spec": {...}
    },
    "frame_detections": [...],      // 原始检测数据
    "right_frame_detections": [...], // 补齐后数据
    "club_head_trajectory": [...],   // 优化后轨迹
    "original_trajectory": [...],    // 原始轨迹
    "swing_states": [...],           // 挥杆状态
    "detection_stats": {...}         // 检测统计
  }
}
```

## 🚀 部署架构

### Docker部署
```yaml
# docker-compose.yml
services:
  golftracker:
    build: .
    ports:
      - "5005:5005"
    environment:
      - MODEL_PATH=data/best.pt
    volumes:
      - ./data:/app/data
      - ./static:/app/static
```

### 本地开发
```bash
# 启动命令
source venv/bin/activate
export MODEL_PATH="data/best.pt"
uvicorn app.main:app --host 0.0.0.0 --port 5005 --reload
```

## 🔍 关键算法

### 1. 自动补齐算法
- **输入**: 原始轨迹数据 (包含None值)
- **处理**: 线性插值填补缺失帧
- **输出**: 100%检测率的完整轨迹

### 2. 挥杆状态机
- **状态**: Address → Backswing → Transition → Downswing → Impact → Followthrough → Finish
- **触发**: 基于轨迹特征和时序分析

### 3. 轨迹优化
- **策略**: 自动补齐算法 (唯一策略)
- **参数**: 最大间隔10帧
- **效果**: 提升检测连续性

## 📈 性能指标

- **检测率**: 90% → 100% (补齐后)
- **处理速度**: ~3秒/100帧视频
- **内存使用**: <2GB
- **并发处理**: 最多2个任务
- **支持格式**: MP4, MOV, AVI

## 🔒 安全考虑

- 临时文件自动清理
- 文件大小限制
- 并发任务限制
- 错误处理和日志记录
- 资源监控和清理

---

*此文档展示了MyGolfTracker项目的完整架构，包括所有接口、数据流程和系统组件。*


