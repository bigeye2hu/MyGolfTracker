# GolfTracker - 高尔夫挥杆分析系统

一个基于YOLOv8的高尔夫挥杆视频分析系统，能够检测杆头位置并生成轨迹数据。

## 🏌️ 功能特性

- **智能杆头检测**：基于YOLOv8深度学习模型，精确检测高尔夫杆头位置
- **轨迹分析**：生成杆头运动轨迹，支持多种优化算法
- **实时处理**：支持视频上传和实时分析
- **Web界面**：现代化的Web界面，支持视频播放和结果可视化
- **API接口**：RESTful API，支持与iOS客户端集成
- **GPU加速**：支持NVIDIA GPU加速，处理速度提升6-10倍

## 🚀 快速开始

### WSL部署（推荐）

**适用于 Windows + WSL2 + NVIDIA GPU**

```bash
# 1. 克隆项目
cd ~
mkdir -p projects && cd projects
git clone https://github.com/bigeye2hu/MyGolfTracker.git
cd MyGolfTracker

# 2. 安装Git LFS并拉取模型文件
sudo apt install -y git-lfs
git lfs install
git lfs pull

# 3. 启动GPU服务
docker-compose -f docker-compose.gpu.yml up -d --build
```

**详细步骤：** 查看 [CLONE_TO_WSL.md](CLONE_TO_WSL.md)

### 本地开发

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
export MODEL_PATH="data/best.pt"
uvicorn app.main:app --host 0.0.0.0 --port 5005 --reload
```

### 访问服务

```
http://localhost:5005/analyze/server-test
```

## 📁 项目结构

```
MyGolfTracker/
├── app/                     # FastAPI应用
│   ├── main.py             # 主应用入口
│   ├── routes/             # 路由模块
│   └── services/           # 业务服务
├── analyzer/               # 分析模块
│   ├── swing_analyzer.py   # 挥杆分析器
│   └── trajectory_optimizer.py  # 轨迹优化器
├── detector/               # 检测模块
│   ├── yolov8_detector.py  # CPU检测器
│   └── yolov8_detector_gpu.py  # GPU检测器
├── static/                 # 静态资源
├── data/                   # 模型文件
│   └── best.pt             # YOLOv8模型 (114MB)
├── scripts/                # 脚本文件
├── docker-compose.gpu.yml  # GPU Docker配置
└── requirements.txt        # Python依赖
```

## 🔧 技术栈

- **后端**：FastAPI + Python 3.9+
- **AI模型**：YOLOv8 (Ultralytics)
- **视频处理**：OpenCV + FFmpeg
- **前端**：HTML5 + JavaScript (ES6+)
- **部署**：Docker + Docker Compose
- **GPU**：CUDA 11.8 + PyTorch

## 📊 API端点

### 主要接口

- `POST /analyze/video` - 视频分析（异步）
- `GET /analyze/video/status?job_id={id}` - 查询分析状态
- `POST /analyze/analyze` - 快速分析（同步）
- `GET /health` - 健康检查
- `GET /analyze/server-test` - Web测试页面

**详细API文档：** 查看 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🎮 GPU加速

支持NVIDIA GPU加速，使用RTX系列显卡可获得：
- **处理速度提升**：6-10倍
- **并发处理能力**：10+个视频同时处理
- **实时分析**：支持准实时视频分析

### GPU环境要求
- NVIDIA驱动
- CUDA 11.8+
- Docker + NVIDIA Container Toolkit
- 8GB+ GPU显存（推荐）

## 📖 文档

- [CLONE_TO_WSL.md](CLONE_TO_WSL.md) - WSL克隆快速指南
- [WSL_DEPLOYMENT_GUIDE.md](WSL_DEPLOYMENT_GUIDE.md) - WSL详细部署指南
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API接口文档
- [ARCHITECTURE.md](ARCHITECTURE.md) - 系统架构说明
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 项目总结
- [STRATEGY_MANAGEMENT.md](STRATEGY_MANAGEMENT.md) - 策略管理

## 🛠️ 开发工具

### 快速脚本

```bash
# WSL环境
./start_wsl.sh      # 启动服务
./stop_wsl.sh       # 停止服务
./check_wsl.sh      # 检查状态

# 部署脚本
./deploy_gpu.sh     # GPU版本部署
./deploy_aliyun.sh  # 阿里云部署
```

## 🔍 性能指标

| 指标 | CPU模式 | GPU模式 (RTX 5090) |
|------|---------|-------------------|
| 分析速度 | ~30秒/视频 | ~3-5秒/视频 |
| 并发数 | 2个 | 10+个 |
| 检测率 | >95% | >95% |
| 内存占用 | ~2GB | ~4GB |

## 🐛 故障排除

### 常见问题

1. **模型文件缺失**
   ```bash
   git lfs pull
   ```

2. **GPU未识别**
   ```bash
   nvidia-smi  # 检查GPU
   docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
   ```

3. **端口占用**
   ```bash
   # 修改 docker-compose.gpu.yml 中的端口
   # 改为 "5006:5005"
   ```

更多问题查看 [WSL_DEPLOYMENT_GUIDE.md](WSL_DEPLOYMENT_GUIDE.md#故障排除)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证

## 📞 联系方式

- GitHub: [@bigeye2hu](https://github.com/bigeye2hu)
- 项目仓库: https://github.com/bigeye2hu/MyGolfTracker

---

**GolfTracker** - 让高尔夫挥杆分析更智能、更精准！ 🏌️‍♂️
