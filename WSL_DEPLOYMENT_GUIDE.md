# 🐧 WSL Ubuntu GPU部署指南

## 🎯 适用场景
- Windows 11/10 + WSL2 Ubuntu
- NVIDIA GPU (RTX 5090)
- Docker Desktop for Windows
- 从GitHub克隆项目

---

## ✅ 前置准备

### 1. 确认WSL2已安装
在Windows PowerShell（管理员）中：
```powershell
# 检查WSL版本
wsl --list --verbose

# 如果需要更新WSL2
wsl --update
wsl --set-default-version 2
```

### 2. 确认Docker Desktop配置
1. 打开Docker Desktop
2. Settings → General → 勾选 "Use the WSL 2 based engine"
3. Settings → Resources → WSL Integration
4. 启用你的Ubuntu发行版

### 3. 在WSL Ubuntu中安装必要工具
打开WSL Ubuntu终端：
```bash
# 更新包管理器
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y git curl wget build-essential

# 检查Docker是否可用
docker --version
docker-compose --version
```

---

## 🚀 快速部署（5步）

### 步骤1：克隆项目

在WSL Ubuntu中：
```bash
# 进入项目目录（建议放在Linux文件系统中，性能更好）
cd ~
mkdir -p projects
cd projects

# 克隆项目
git clone https://github.com/bigeye2hu/MyGolfTracker.git
cd MyGolfTracker

# 如果模型文件使用Git LFS，需要安装并拉取
sudo apt install -y git-lfs
git lfs install
git lfs pull
```

**重要提示：** 
- ✅ 推荐放在Linux路径：`/home/用户名/projects/`（性能好）
- ❌ 避免放在Windows路径：`/mnt/c/` 或 `/mnt/d/`（性能差）

### 步骤2：安装NVIDIA Container Toolkit

```bash
# 添加NVIDIA包仓库
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 安装
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 配置Docker运行时
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker 2>/dev/null || true

# 验证GPU支持
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

如果看到GPU信息，说明配置成功！

### 步骤3：检查项目文件

```bash
cd ~/projects/MyGolfTracker

# 查看项目结构
ls -la

# 确认关键文件存在
ls -la data/best.pt  # 模型文件
ls -la docker-compose.gpu.yml  # GPU配置
```

### 步骤4：构建并启动服务

```bash
# 使用GPU版本的Docker Compose
docker-compose -f docker-compose.gpu.yml build

# 启动服务
docker-compose -f docker-compose.gpu.yml up -d

# 查看日志
docker-compose -f docker-compose.gpu.yml logs -f
```

### 步骤5：访问服务

在Windows浏览器中访问：
```
http://localhost:5005/analyze/server-test
```

或者从局域网其他设备访问：
```
http://你的Windows-IP:5005/analyze/server-test
```

---

## 🛠️ WSL专用脚本

### 创建启动脚本

```bash
cd ~/projects/MyGolfTracker

# 创建启动脚本
cat > start_wsl.sh << 'EOF'
#!/bin/bash

echo "🚀 启动GolfTracker GPU服务 (WSL)"

# 检查Docker
if ! docker ps >/dev/null 2>&1; then
    echo "❌ Docker未运行，请启动Docker Desktop"
    exit 1
fi

# 检查GPU
echo "🎮 检查GPU状态..."
nvidia-smi

# 启动服务
echo "🔨 构建并启动服务..."
docker-compose -f docker-compose.gpu.yml up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查状态
echo "📊 服务状态:"
docker-compose -f docker-compose.gpu.yml ps

echo ""
echo "📝 最新日志:"
docker-compose -f docker-compose.gpu.yml logs --tail=20

echo ""
echo "✅ 服务已启动！"
echo "🌐 访问: http://localhost:5005/analyze/server-test"
EOF

chmod +x start_wsl.sh
```

### 创建停止脚本

```bash
cat > stop_wsl.sh << 'EOF'
#!/bin/bash

echo "🛑 停止GolfTracker GPU服务 (WSL)"

docker-compose -f docker-compose.gpu.yml down

echo "✅ 服务已停止"
EOF

chmod +x stop_wsl.sh
```

### 创建状态检查脚本

```bash
cat > check_wsl.sh << 'EOF'
#!/bin/bash

echo "📊 GolfTracker GPU服务状态检查 (WSL)"
echo ""

echo "=== Docker容器状态 ==="
docker-compose -f docker-compose.gpu.yml ps

echo ""
echo "=== GPU状态 ==="
nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv

echo ""
echo "=== 最新日志 ==="
docker-compose -f docker-compose.gpu.yml logs --tail=20
EOF

chmod +x check_wsl.sh
```

---

## 📋 日常使用

### 启动服务
```bash
cd ~/projects/MyGolfTracker
./start_wsl.sh
```

### 停止服务
```bash
cd ~/projects/MyGolfTracker
./stop_wsl.sh
```

### 查看状态
```bash
cd ~/projects/MyGolfTracker
./check_wsl.sh
```

### 查看实时日志
```bash
cd ~/projects/MyGolfTracker
docker-compose -f docker-compose.gpu.yml logs -f
```

### 重启服务
```bash
cd ~/projects/MyGolfTracker
docker-compose -f docker-compose.gpu.yml restart
```

### 完全重建
```bash
cd ~/projects/MyGolfTracker
docker-compose -f docker-compose.gpu.yml down
docker-compose -f docker-compose.gpu.yml up -d --build
```

---

## 🔧 WSL优化配置

### 配置WSL资源限制

创建或编辑 `C:\Users\你的用户名\.wslconfig`：

```ini
[wsl2]
# 内存限制
memory=16GB

# 处理器核心数
processors=8

# Swap空间
swap=4GB

# 启用GPU支持
nestedVirtualization=true
```

保存后，在PowerShell中重启WSL：
```powershell
wsl --shutdown
```

### 优化Docker性能

在WSL中编辑 `/etc/docker/daemon.json`：
```bash
sudo nano /etc/docker/daemon.json
```

添加：
```json
{
  "data-root": "/mnt/wsl/docker-data",
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

重启Docker（在Docker Desktop中）。

---

## 🔄 更新代码

### 从Git拉取更新
```bash
cd ~/projects/MyGolfTracker

# 拉取最新代码
git pull

# 如果有Git LFS文件更新
git lfs pull

# 重新构建并启动
docker-compose -f docker-compose.gpu.yml up -d --build
```

---

## 🌐 局域网访问配置

### 1. 查看Windows IP
在Windows PowerShell中：
```powershell
ipconfig
# 记下IPv4地址，例如：192.168.1.100
```

### 2. 配置Windows防火墙
在PowerShell（管理员）中：
```powershell
# 允许5005端口
New-NetFirewallRule -DisplayName "GolfTracker" -Direction Inbound -LocalPort 5005 -Protocol TCP -Action Allow
```

### 3. 从其他设备访问
```
http://192.168.1.100:5005/analyze/server-test
```

---

## 🐛 故障排除

### 问题1：Docker未运行
```bash
# WSL中Docker命令失败
# 解决：启动Windows上的Docker Desktop
```

### 问题2：GPU未识别
```bash
# 检查NVIDIA驱动
nvidia-smi

# 重新安装NVIDIA Container Toolkit
sudo apt-get purge -y nvidia-container-toolkit
# 然后重新执行步骤2的安装命令
```

### 问题3：端口冲突
```bash
# 查看端口占用
sudo lsof -i :5005

# 修改端口（编辑docker-compose.gpu.yml）
# 改为 "5006:5005"
```

### 问题4：WSL文件系统性能差
```bash
# 如果项目在 /mnt/c/ 或 /mnt/d/ 下
# 移动到Linux文件系统
cd ~
mv /mnt/d/MyGolfTracker ~/projects/
cd ~/projects/MyGolfTracker
```

### 问题5：模型文件缺失
```bash
# 检查模型文件
ls -lh data/best.pt

# 如果缺失，手动下载或从Mac复制
# 方法1：从Mac SCP复制
# scp user@mac-ip:/path/to/data/best.pt ~/projects/MyGolfTracker/data/

# 方法2：使用Git LFS
git lfs pull
```

---

## 📊 性能监控

### 实时监控GPU
```bash
# 每2秒刷新一次
watch -n 2 nvidia-smi

# 或者使用gpustat（需安装）
pip install gpustat
gpustat -i 2
```

### 监控Docker容器
```bash
# 查看资源使用
docker stats golftracker-service-gpu

# 查看详细信息
docker inspect golftracker-service-gpu
```

---

## 💡 WSL vs 原生Linux

| 特性 | WSL | 原生Linux |
|------|-----|-----------|
| GPU支持 | ✅ 完全支持 | ✅ 完全支持 |
| 性能 | ⚡ 95%+ | ⚡ 100% |
| 文件访问 | 🔄 可访问Windows | ❌ 独立文件系统 |
| 开发体验 | 🎯 最佳 | ✅ 良好 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**结论：WSL是Windows上最佳的部署方案！**

---

## 🎉 总结

使用WSL部署的优势：
- ✅ 原生Linux环境，兼容性好
- ✅ GPU加速完全支持
- ✅ 文件系统性能好（放在Linux路径）
- ✅ 可以直接访问Windows文件
- ✅ 开发调试方便

现在你可以：
1. 在WSL中 `git clone` 项目
2. 一键启动GPU加速服务
3. 享受原生Linux + Windows GUI的最佳体验

---

**Have fun with WSL + RTX 5090! 🚀**

