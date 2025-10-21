# 🚀 WSL克隆项目快速指南

## 📋 准备工作（Windows上）

### 1. 启动WSL Ubuntu
在Windows中按 `Win + X`，选择 "Windows终端" 或 "PowerShell"，然后输入：
```powershell
wsl
```

## 🎯 在WSL中克隆项目（3步）

### 步骤1：安装Git LFS
```bash
# 更新包管理器
sudo apt update

# 安装Git和Git LFS
sudo apt install -y git git-lfs

# 初始化Git LFS
git lfs install
```

### 步骤2：克隆项目
```bash
# 进入home目录
cd ~

# 创建项目文件夹
mkdir -p projects
cd projects

# 克隆项目（使用HTTPS）
git clone https://github.com/bigeye2hu/MyGolfTracker.git

# 进入项目
cd MyGolfTracker

# 拉取大文件（模型文件）
git lfs pull
```

**⚠️ 重要提示：**
- 模型文件较大（best.pt: 114MB, ClubDetection_1000P_50R.pt: 136MB）
- `git lfs pull` 会自动下载这些文件
- 第一次克隆可能需要几分钟

### 步骤3：验证文件完整性
```bash
# 检查模型文件
ls -lh data/

# 应该看到：
# -rw-r--r-- 1 user user 136M ... ClubDetection_1000P_50R.pt
# -rw-r--r-- 1 user user 114M ... best.pt

# 查看项目结构
tree -L 2 -I 'venv|__pycache__|*.pyc'
# 或
ls -la
```

## 🐳 Docker环境配置

### 安装NVIDIA Container Toolkit
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

# 验证GPU支持
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

如果看到GPU信息，说明配置成功！

## 🚀 启动服务

### 方式1：使用提供的脚本（推荐）
```bash
# 赋予脚本执行权限
chmod +x *.sh

# 启动服务
./start_wsl.sh

# 查看状态
./check_wsl.sh

# 停止服务
./stop_wsl.sh
```

**等等！** 如果你看到提示"start_wsl.sh不存在"，请先创建它：

```bash
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

### 方式2：手动启动
```bash
# 构建Docker镜像
docker-compose -f docker-compose.gpu.yml build

# 启动服务
docker-compose -f docker-compose.gpu.yml up -d

# 查看日志
docker-compose -f docker-compose.gpu.yml logs -f
```

## 🌐 访问服务

在Windows浏览器中打开：
```
http://localhost:5005/analyze/server-test
```

主要endpoints：
- 主页面：http://localhost:5005/analyze/server-test
- 健康检查：http://localhost:5005/health
- 视频转换：http://localhost:5005/convert/test-page
- API文档：查看 API_DOCUMENTATION.md

## 📊 验证GPU工作

```bash
# 查看GPU状态
nvidia-smi

# 查看Docker容器是否使用GPU
docker exec -it golftracker-service-gpu python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"
```

应该显示：
```
CUDA: True
GPU: NVIDIA GeForce RTX 5090
```

## 🔄 日常使用

### 查看日志
```bash
cd ~/projects/MyGolfTracker
docker-compose -f docker-compose.gpu.yml logs -f
```

### 重启服务
```bash
docker-compose -f docker-compose.gpu.yml restart
```

### 停止服务
```bash
docker-compose -f docker-compose.gpu.yml down
```

### 更新代码
```bash
cd ~/projects/MyGolfTracker
git pull
git lfs pull  # 如果有模型文件更新
docker-compose -f docker-compose.gpu.yml up -d --build
```

## 🐛 常见问题

### Q1: git lfs pull 很慢或失败
```bash
# 方法1：使用代理
git config --global http.proxy http://127.0.0.1:7890

# 方法2：手动从Mac复制模型文件
# 在Mac上：
# scp data/best.pt user@windows-ip:/path/to/wsl/projects/MyGolfTracker/data/
```

### Q2: Docker命令提示权限错误
```bash
# 将当前用户添加到docker组
sudo usermod -aG docker $USER

# 重新登录WSL
exit
# 然后在Windows重新打开WSL
wsl
```

### Q3: 端口5005被占用
```bash
# 查看占用
sudo lsof -i :5005

# 停止占用进程或修改端口
# 编辑 docker-compose.gpu.yml，改为 "5006:5005"
```

### Q4: GPU未识别
```bash
# 检查Windows NVIDIA驱动
# 在Windows PowerShell中运行：
# nvidia-smi

# 在WSL中检查
nvidia-smi

# 重新安装NVIDIA Container Toolkit（参考上面的安装步骤）
```

## 📁 项目位置

- **WSL路径**：`~/projects/MyGolfTracker` 或 `/home/你的用户名/projects/MyGolfTracker`
- **Windows路径**：`\\wsl$\Ubuntu\home\你的用户名\projects\MyGolfTracker`

**提示：** 在Windows文件资源管理器地址栏输入 `\\wsl$` 可以访问WSL文件系统

## 🎯 性能优化建议

1. **使用Linux文件系统**
   - ✅ 推荐：`~/projects/MyGolfTracker`（性能好）
   - ❌ 避免：`/mnt/c/` 或 `/mnt/d/`（性能差）

2. **配置WSL资源**
   - 编辑 `C:\Users\你的用户名\.wslconfig`
   - 增加内存到16GB
   - 增加CPU核心数

3. **Docker优化**
   - 在Docker Desktop中分配足够的资源
   - 启用WSL2集成

## ✅ 完成清单

- [ ] WSL Ubuntu已安装
- [ ] Docker Desktop已安装并启动
- [ ] Git和Git LFS已安装
- [ ] 项目已克隆到 `~/projects/MyGolfTracker`
- [ ] 模型文件已下载（git lfs pull）
- [ ] NVIDIA Container Toolkit已安装
- [ ] GPU支持已验证
- [ ] 服务已启动
- [ ] 浏览器可以访问 http://localhost:5005

## 🎉 下一步

现在你可以：
1. 上传视频测试高尔夫挥杆分析
2. 使用GPU加速，速度提升6-10倍
3. 查看详细部署文档：`WSL_DEPLOYMENT_GUIDE.md`
4. 配置远程开发：`REMOTE_DEVELOPMENT_GUIDE.md`

**享受RTX 5090的强大性能！** 🚀

