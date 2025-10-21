# Windows本地GPU部署指南

## 🎯 适用场景
- 本地Windows系统
- 已安装Docker Desktop
- NVIDIA GPU（如RTX 5090）
- 用于本地开发和测试

## ✅ 前置要求

### 1. NVIDIA驱动和CUDA
确保已安装最新的NVIDIA驱动：
```powershell
# 在PowerShell中检查
nvidia-smi
```
应该能看到GPU信息和CUDA版本

### 2. Docker Desktop设置
1. 打开Docker Desktop
2. 进入 Settings → General
3. 确保勾选 "Use the WSL 2 based engine"
4. 进入 Settings → Resources → WSL Integration
5. 启用你的WSL2发行版（如Ubuntu）

### 3. NVIDIA Container Toolkit（WSL2中安装）
在WSL2 Ubuntu中执行：
```bash
# 添加NVIDIA包仓库
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# 安装NVIDIA Container Toolkit
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# 重启Docker服务
sudo service docker restart
```

## 🚀 部署步骤

### 方法一：使用Docker Compose（推荐）

1. **打开PowerShell，进入项目目录**
```powershell
cd D:\MyGolfTracker  # 改为你的项目路径
```

2. **检查GPU支持**
```powershell
# 测试Docker能否使用GPU
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

3. **构建并启动GPU服务**
```powershell
# 使用GPU版本的docker-compose
docker-compose -f docker-compose.gpu.yml build
docker-compose -f docker-compose.gpu.yml up -d
```

4. **查看日志**
```powershell
docker-compose -f docker-compose.gpu.yml logs -f
```

5. **访问服务**
浏览器打开：http://localhost:5005/analyze/server-test

### 方法二：直接运行（不使用Docker）

1. **安装Python 3.9-3.10**
从 https://www.python.org/downloads/ 下载安装

2. **安装CUDA Toolkit 11.8**
从 https://developer.nvidia.com/cuda-11-8-0-download-archive 下载安装

3. **创建虚拟环境**
```powershell
cd D:\MyGolfTracker
python -m venv venv
.\venv\Scripts\Activate.ps1
```

4. **安装GPU版本的PyTorch**
```powershell
pip install torch==2.1.0+cu118 torchvision==0.16.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
```

5. **安装其他依赖**
```powershell
pip install -r requirements.txt
```

6. **启动服务**
```powershell
$env:MODEL_PATH="data/best.pt"
uvicorn app.main:app --host 0.0.0.0 --port 5005 --reload
```

7. **访问服务**
浏览器打开：http://localhost:5005/analyze/server-test

## 🔧 Windows专用配置调整

### 修改docker-compose.gpu.yml（如需要）

创建 `docker-compose.gpu.windows.yml`：

```yaml
version: "3.9"
services:
  golftracker:
    build:
      context: .
      dockerfile: Dockerfile.gpu
    container_name: golftracker-service-gpu
    ports:
      - "5005:5005"
    environment:
      - MODEL_PATH=data/best.pt
      - SERVICE_PORT=5005
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

使用此配置：
```powershell
docker-compose -f docker-compose.gpu.windows.yml up -d
```

## 🎮 验证GPU是否工作

1. **进入容器检查**
```powershell
docker exec -it golftracker-service-gpu nvidia-smi
```

2. **检查PyTorch能否使用GPU**
```powershell
docker exec -it golftracker-service-gpu python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

应该显示：
```
CUDA available: True
GPU: NVIDIA GeForce RTX 5090
```

## 📊 性能对比

| 处理方式 | CPU (云服务器) | GPU (RTX 5090) |
|---------|---------------|----------------|
| 视频分析速度 | ~30秒/视频 | ~3-5秒/视频 |
| 并发处理 | 1-2个 | 10+个 |
| 检测精度 | 同等 | 同等 |
| 内存占用 | ~2GB | ~4GB |

## 🐛 常见问题

### 问题1: Docker无法识别GPU
**解决方案：**
1. 确保NVIDIA驱动已安装
2. 在WSL2中安装nvidia-docker2
3. 重启Docker Desktop
4. 测试：`docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi`

### 问题2: 端口5005已被占用
**解决方案：**
```powershell
# 查找占用端口的进程
netstat -ano | findstr :5005

# 结束进程（使用进程ID）
taskkill /PID <进程ID> /F

# 或者修改端口
# 在docker-compose.gpu.yml中改为 "5006:5005"
```

### 问题3: 内存不足
**解决方案：**
1. 打开Docker Desktop → Settings → Resources
2. 增加Memory限制到16GB
3. 增加Swap到4GB

### 问题4: WSL2错误
**解决方案：**
```powershell
# 更新WSL2
wsl --update

# 设置WSL2为默认版本
wsl --set-default-version 2

# 重启WSL
wsl --shutdown
```

## 🔐 防火墙设置

如需从局域网其他设备访问：

1. **打开Windows Defender防火墙**
2. **高级设置 → 入站规则 → 新建规则**
3. **选择端口 → TCP → 特定本地端口：5005**
4. **允许连接 → 应用**

然后可以通过局域网IP访问：
```
http://192.168.x.x:5005/analyze/server-test
```

## 📝 快速启动脚本

创建 `start_windows.ps1`：

```powershell
# Windows PowerShell启动脚本
Write-Host "🚀 启动GolfTracker GPU服务..." -ForegroundColor Green

# 检查Docker是否运行
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker未运行，请先启动Docker Desktop" -ForegroundColor Red
    exit 1
}

# 检查GPU
Write-Host "🎮 检查GPU状态..." -ForegroundColor Cyan
nvidia-smi

# 启动服务
Write-Host "🔨 构建并启动服务..." -ForegroundColor Cyan
docker-compose -f docker-compose.gpu.yml up -d --build

# 等待服务启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host "📊 检查服务状态..." -ForegroundColor Cyan
docker-compose -f docker-compose.gpu.yml ps

# 显示日志
Write-Host "📝 最新日志：" -ForegroundColor Cyan
docker-compose -f docker-compose.gpu.yml logs --tail=20

Write-Host "`n✅ 服务已启动！" -ForegroundColor Green
Write-Host "🌐 访问地址: http://localhost:5005/analyze/server-test" -ForegroundColor Green
Write-Host "🔍 健康检查: http://localhost:5005/health" -ForegroundColor Green

# 自动打开浏览器
Start-Process "http://localhost:5005/analyze/server-test"
```

创建 `stop_windows.ps1`：

```powershell
# Windows PowerShell停止脚本
Write-Host "🛑 停止GolfTracker GPU服务..." -ForegroundColor Yellow

docker-compose -f docker-compose.gpu.yml down

Write-Host "✅ 服务已停止" -ForegroundColor Green
```

使用方式：
```powershell
# 启动
.\start_windows.ps1

# 停止
.\stop_windows.ps1
```

## 🎯 下一步

1. 访问测试页面上传视频测试
2. 查看GPU利用率：`nvidia-smi -l 1`
3. 监控容器日志：`docker-compose -f docker-compose.gpu.yml logs -f`
4. 性能调优：调整batch size和推理分辨率

## 📞 技术支持

遇到问题？
1. 查看日志：`docker-compose -f docker-compose.gpu.yml logs`
2. 重启服务：`docker-compose -f docker-compose.gpu.yml restart`
3. 完全重建：`docker-compose -f docker-compose.gpu.yml down -v && docker-compose -f docker-compose.gpu.yml up -d --build`

