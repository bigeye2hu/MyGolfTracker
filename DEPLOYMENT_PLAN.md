# 🚀 MyGolfTracker 服务器部署方案

## 📋 **项目概述**

**MyGolfTracker** 是一个基于 YOLOv8 的高尔夫挥杆分析服务，提供：
- 🎯 自动杆头检测（YOLOv8 模型）
- 🏌️ 挥杆轨迹分析
- 📊 挥杆阶段识别
- 🔄 与 iOS 应用的数据兼容

## 🖥️ **服务器信息**

```
服务器地址: root@143.244.211.22
密码: 27Yk*a-k#R￼
项目路径: /www/wwwroot/golf_golftracker
```

## 🏗️ **技术架构**

### 后端框架
- **FastAPI**: 高性能 Python Web 框架
- **Uvicorn**: ASGI 服务器
- **Python 3.10**: 运行环境

### 核心模块
```
MyGolfTracker/
├── app/                    # FastAPI 应用
│   ├── main.py            # 主应用入口
│   └── routes/            # API 路由
│       ├── analyze.py     # 视频分析接口
│       └── health.py      # 健康检查接口
├── detector/               # 检测模块
│   ├── yolov8_detector.py # YOLOv8 杆头检测
│   └── pose_detector.py   # MediaPipe 姿态检测
├── analyzer/               # 分析模块
│   ├── swing_analyzer.py  # 挥杆分析
│   ├── trajectory_optimizer.py # 轨迹优化
│   ├── ffmpeg.py          # 视频处理
│   └── config.py          # 配置管理
├── data/                   # 模型数据
│   └── ClubDetection_1000P_50R.pt # YOLOv8 模型
└── scripts/                # 部署脚本
    ├── start_service.sh    # 启动服务
    └── stop_service.sh     # 停止服务
```

### 依赖包
- **YOLOv8**: 杆头检测模型
- **MediaPipe**: 人体姿态检测
- **OpenCV**: 图像处理
- **FFmpeg**: 视频处理
- **NumPy/SciPy**: 数值计算

## 🐳 **部署方案**

### 方案一：Docker 部署（推荐）

#### 优势
- 环境一致性好
- 依赖管理简单
- 部署快速
- 易于回滚

#### 部署步骤

1. **准备部署包**
```bash
# 在本地创建部署包
tar -czf MyGolfTracker_deployment.tar.gz \
    app/ analyzer/ detector/ data/ \
    Dockerfile docker-compose.yml requirements.txt \
    scripts/ README.md
```

2. **上传到服务器**
```bash
scp MyGolfTracker_deployment.tar.gz root@143.244.211.22:/tmp/
```

3. **服务器部署**
```bash
# SSH 到服务器
ssh root@143.244.211.22

# 解压部署包
cd /tmp
tar -xzf MyGolfTracker_deployment.tar.gz

# 移动到项目目录
rm -rf /www/wwwroot/golf_golftracker
mkdir -p /www/wwwroot/golf_golftracker
cp -r * /www/wwwroot/golf_golftracker/

# 启动服务
cd /www/wwwroot/golf_golftracker
chmod +x scripts/*.sh
./scripts/start_service.sh
```

### 方案二：直接部署

#### 优势
- 资源占用少
- 启动速度快
- 调试方便

#### 部署步骤

1. **服务器环境准备**
```bash
# 安装 Python 3.10
apt update
apt install -y python3.10 python3.10-venv python3.10-pip

# 安装系统依赖
apt install -y ffmpeg libgl1
```

2. **项目部署**
```bash
# 创建虚拟环境
cd /www/wwwroot/golf_golftracker
python3.10 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 5005 --workers 2
```

## 🔧 **配置说明**

### 环境变量
```bash
# 服务配置
PORT=5005
HOST=0.0.0.0
WORKERS=2

# 模型路径
MODEL_PATH=/app/data/ClubDetection_1000P_50R.pt

# 日志级别
LOG_LEVEL=INFO
```

### 端口配置
- **主服务**: 5005
- **健康检查**: 5005/health
- **分析接口**: 5005/analyze

## 📱 **iOS 应用兼容性**

### 数据格式要求
```json
{
  "pose_result": {
    "handed": "right",           // 必须：惯用手
    "poses_count": 1,           // 必须：姿态数量
    "poses": [...],             // 姿态数据
    "club_trajectory": [...]    // 杆头轨迹
  }
}
```

### 关键字段
- `handed`: 惯用手（left/right）
- `poses_count`: 检测到的姿态数量
- `poses`: MediaPipe 姿态数据数组
- `club_trajectory`: 优化后的杆头轨迹

## 🚀 **快速部署命令**

### 一键部署脚本
```bash
#!/bin/bash
# deploy.sh

echo "🚀 开始部署 MyGolfTracker..."

# 1. 创建部署包
tar -czf MyGolfTracker_deployment.tar.gz \
    app/ analyzer/ detector/ data/ \
    Dockerfile docker-compose.yml requirements.txt \
    scripts/ README.md

# 2. 上传到服务器
scp MyGolfTracker_deployment.tar.gz root@143.244.211.22:/tmp/

# 3. 远程部署
sshpass -p '27Yk*a-k#R￼' ssh -o StrictHostKeyChecking=no root@143.244.211.22 << 'EOF'
cd /tmp
tar -xzf MyGolfTracker_deployment.tar.gz
rm -rf /www/wwwroot/golf_golftracker
mkdir -p /www/wwwroot/golf_golftracker
cp -r * /www/wwwroot/golf_golftracker/
cd /www/wwwroot/golf_golftracker
chmod +x scripts/*.sh
./scripts/start_service.sh
EOF

echo "✅ 部署完成！"
```

## 🔍 **验证部署**

### 健康检查
```bash
curl http://143.244.211.22:5005/health
```

### 服务状态
```bash
# Docker 方式
docker ps | grep golftracker

# 直接部署方式
ps aux | grep uvicorn
```

### 日志查看
```bash
# Docker 方式
docker-compose logs -f

# 直接部署方式
tail -f /var/log/golftracker.log
```

## 🛠️ **故障排除**

### 常见问题

1. **端口被占用**
```bash
# 检查端口占用
netstat -tlnp | grep 5005
# 杀死进程
kill -9 <PID>
```

2. **模型加载失败**
```bash
# 检查模型文件权限
ls -la data/ClubDetection_1000P_50R.pt
# 重新下载模型
```

3. **依赖安装失败**
```bash
# 清理缓存
pip cache purge
# 重新安装
pip install -r requirements.txt --no-cache-dir
```

### 回滚方案
```bash
# 停止当前服务
./scripts/stop_service.sh

# 恢复备份
cp -r backup/* /www/wwwroot/golf_golftracker/

# 重启服务
./scripts/start_service.sh
```

## 📞 **技术支持**

- **部署问题**: 检查日志和配置
- **性能问题**: 监控资源使用
- **兼容性问题**: 验证数据格式

---

**部署完成后，服务将在 `http://143.244.211.22:5005` 上运行**
