# GolfTracker - 高尔夫挥杆分析系统

一个基于YOLOv8的高尔夫挥杆视频分析系统，能够检测杆头位置并生成轨迹数据。

## 🏌️ 功能特性

- **智能杆头检测**：基于YOLOv8深度学习模型，精确检测高尔夫杆头位置
- **轨迹分析**：生成杆头运动轨迹，支持多种优化算法
- **实时处理**：支持视频上传和实时分析
- **Web界面**：现代化的Web界面，支持视频播放和结果可视化
- **API接口**：RESTful API，支持与iOS客户端集成
- **Docker部署**：支持Docker容器化部署

## 📁 项目结构

```
MyGolfTracker/
├── analyzer/                 # 分析模块
│   ├── config.py            # 配置文件
│   ├── ffmpeg.py            # 视频处理
│   ├── swing_analyzer.py    # 挥杆分析器
│   ├── trajectory_optimizer.py  # 轨迹优化器
│   └── fast_motion_optimizer.py # 快速移动优化器
├── app/                     # FastAPI应用
│   ├── main.py             # 主应用入口
│   └── routes/             # 路由模块
│       ├── analyze.py      # 分析路由
│       └── health.py       # 健康检查
├── detector/               # 检测模块
│   ├── yolov8_detector.py  # YOLOv8检测器
│   └── pose_detector.py    # 姿态检测器
├── static/                 # 静态资源
│   ├── css/               # 样式文件
│   └── js/                # JavaScript模块
├── data/                   # 数据文件
│   └── best.pt             # YOLOv8模型文件 (5000张图片训练)
├── scripts/                # 脚本文件
│   ├── start_service.sh   # 启动服务
│   ├── stop_service.sh    # 停止服务
│   └── test_local.sh      # 本地测试
├── Dockerfile             # Docker配置
├── docker-compose.yml     # Docker Compose配置
├── requirements.txt       # Python依赖
└── README.md             # 项目说明
```

## 🚀 快速开始

### 本地开发

1. **克隆项目**
```bash
git clone <repository-url>
cd MyGolfTracker
```

2. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **启动服务**
```bash
export MODEL_PATH="data/best.pt"
uvicorn app.main:app --host 0.0.0.0 --port 5005 --reload
```

5. **访问测试页面**
```
http://localhost:5005/analyze/server-test
```

### Docker部署

1. **构建镜像**
```bash
docker-compose build
```

2. **启动服务**
```bash
docker-compose up -d
```

3. **访问服务**
```
http://localhost:5005
```

## 🔧 配置说明

### 检测参数优化

- **置信度阈值**：0.05（提高检测率）
- **推理分辨率**：640x640（平衡精度和性能）
- **检测策略**：优先使用杆头检测，智能回退到杆身
- **模型版本**：best.pt (5000张图片训练，109MB)
- **检测率**：>95% (新模型优化后)

### 轨迹优化

- **标准优化**：Savitzky-Golay滤波 + 线性插值
- **快速移动优化**：自适应平滑 + 运动预测
- **三线对比**：原始数据、标准优化、快速移动优化

## 📊 API接口

### 视频分析
```http
POST /analyze/video
Content-Type: multipart/form-data

参数：
- video: 视频文件
```

### 分析状态
```http
GET /analyze/video/status?job_id={job_id}
```

### 健康检查
```http
GET /health
```

## 🎯 检测逻辑

1. **优先检测杆头**：只要检测到杆头（ID=1），无论置信度多低都优先使用
2. **智能回退**：只有在完全没有杆头检测时，才考虑杆身（置信度>0.1）
3. **避免误检**：严格拒绝手部检测，确保轨迹准确性

## 🔍 技术栈

- **后端**：FastAPI + Python 3.9
- **AI模型**：YOLOv8 (Ultralytics)
- **视频处理**：OpenCV + FFmpeg
- **前端**：HTML5 + CSS3 + JavaScript (ES6+)
- **部署**：Docker + Docker Compose
- **数据优化**：NumPy + SciPy

## 📈 性能优化

- **CPU增强模式**：多线程并行处理
- **内存优化**：智能缓存和垃圾回收
- **网络优化**：Gzip压缩和CDN加速
- **检测优化**：降低置信度阈值，提高检测率

## 🐛 故障排除

### 常见问题

1. **JSON序列化错误**
   - 原因：轨迹数据包含NaN或无穷大值
   - 解决：已添加safe_float函数处理

2. **检测率低**
   - 原因：置信度阈值过高
   - 解决：已降低到0.05，优先使用杆头检测

3. **502错误**
   - 原因：处理超时或资源不足
   - 解决：使用后台任务+轮询机制

## 📝 更新日志

### v1.6 (最新)
- ✅ 修复JSON序列化错误
- ✅ 优化检测逻辑，提高杆头检测率
- ✅ 添加快速移动优化算法
- ✅ 完善Web界面和用户体验
- ✅ 支持三线对比显示

### v1.5
- ✅ 实现背景任务和轮询机制
- ✅ 添加CPU优化配置
- ✅ 修复坐标系统一致性

### v1.0
- ✅ 基础YOLOv8检测功能
- ✅ Web界面和API接口
- ✅ Docker部署支持

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 微信联系

---

**GolfTracker** - 让高尔夫挥杆分析更智能、更精准！ 🏌️‍♂️