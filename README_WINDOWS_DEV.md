# 🖥️ Mac + Windows 远程开发快速指南

## 🎯 开发模式
- **Mac（Cursor）**：编写代码
- **Windows（RTX 5090）**：运行GPU加速服务
- **自动同步**：代码实时同步

---

## 🚀 快速开始（3步）

### 步骤1：配置SSH连接（仅需一次）

#### 在Windows上启用SSH服务器
打开PowerShell（管理员）：
```powershell
# 安装OpenSSH服务器
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# 启动并设置自动启动
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'

# 查看IP地址（记下来）
ipconfig
```

#### 在Mac上运行自动配置
```bash
cd /Users/huxiaoran/Documents/xiaoranProjects/GolfTracker/MyGolfTracker

# 运行自动配置脚本
./setup_ssh.sh
```

脚本会提示你输入：
- Windows IP地址
- Windows用户名
- Windows密码（仅一次，之后使用密钥）

### 步骤2：同步项目到Windows

#### 在Windows上创建项目目录
打开PowerShell：
```powershell
mkdir D:\MyGolfTracker
```

#### 在Mac上首次同步
```bash
# 同步所有代码到Windows
./sync_to_windows.sh
```

### 步骤3：启动GPU服务

#### 方式A：自动部署（推荐）
```bash
# 一键同步 + 构建 + 启动
./quick_deploy.sh
```

#### 方式B：手动启动
```bash
# SSH到Windows
ssh windows-gpu

# 进入项目
cd D:\MyGolfTracker

# 启动服务
.\start_windows.ps1
```

✅ **完成！** 浏览器访问：http://你的Windows-IP:5005/analyze/server-test

---

## 📋 日常开发工作流

### 工作流程A：本地编辑 + 同步部署

```bash
# 1. 在Mac的Cursor中编辑代码
# （正常编辑，保存文件）

# 2. 同步到Windows
./sync_to_windows.sh

# 3. 重启Windows服务（可选）
./quick_deploy.sh
```

### 工作流程B：Remote SSH（推荐，零延迟）

```bash
# 1. 在Cursor中安装 "Remote - SSH" 扩展

# 2. 按 Cmd+Shift+P，输入 "Remote-SSH: Connect to Host"

# 3. 选择 "windows-gpu"

# 4. 打开文件夹：D:\MyGolfTracker

# 5. 直接在Cursor中编辑Windows上的文件（实时保存）

# 6. 在Cursor的终端中运行Windows命令
.\start_windows.ps1
```

---

## 🛠️ 常用命令

### 同步代码到Windows
```bash
./sync_to_windows.sh
```

### 一键部署并启动服务
```bash
./quick_deploy.sh
```

### 检查Windows服务状态
```bash
./check_windows_status.sh
```

### SSH连接到Windows
```bash
ssh windows-gpu
```

### 查看Windows服务日志
```bash
ssh windows-gpu
cd D:\MyGolfTracker
docker-compose -f docker-compose.gpu.yml logs -f
```

### 停止Windows服务
```bash
ssh windows-gpu
cd D:\MyGolfTracker
docker-compose -f docker-compose.gpu.yml down
```

---

## 📊 脚本说明

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `setup_ssh.sh` | 自动配置SSH | 首次设置 |
| `sync_to_windows.sh` | 同步代码 | 代码修改后 |
| `quick_deploy.sh` | 一键部署 | 完整部署 |
| `check_windows_status.sh` | 状态检查 | 监控服务 |

---

## 🔍 开发工具推荐

### 推荐：Cursor Remote SSH

**优势：**
- ✅ 直接编辑Windows文件，零延迟
- ✅ 代码补全、调试完全支持
- ✅ 终端直接在Windows执行命令
- ✅ 文件保存即生效，无需同步

**配置：**
1. 在Cursor中安装 "Remote - SSH" 扩展
2. 按 `Cmd+Shift+P`
3. 输入 "Remote-SSH: Connect to Host"
4. 选择 "windows-gpu"
5. 打开文件夹：`D:\MyGolfTracker`

### 备选：自动文件监控

使用`fswatch`自动监控文件变化并同步：

```bash
# 安装fswatch
brew install fswatch

# 创建监控脚本
cat > auto_sync.sh << 'EOF'
#!/bin/bash
echo "🔄 启动自动同步监控..."
fswatch -o . -e ".*\.pyc$" -e "__pycache__" -e "venv/" | while read f; do 
    echo "检测到文件变化，同步中..."
    ./sync_to_windows.sh
done
EOF

chmod +x auto_sync.sh

# 在新终端窗口运行
./auto_sync.sh
```

---

## 🐛 故障排除

### 问题1：SSH连接失败
```bash
# 检查Windows SSH服务
ssh windows-gpu

# 如果失败，重新运行配置
./setup_ssh.sh
```

### 问题2：同步失败
```bash
# 检查网络连接
ping 你的Windows-IP

# 检查SSH连接
ssh windows-gpu exit

# 重新同步
./sync_to_windows.sh
```

### 问题3：端口5005被占用
在Windows上：
```powershell
# 查找占用进程
netstat -ano | findstr :5005

# 结束进程
taskkill /PID <进程ID> /F

# 或修改端口
# 编辑 docker-compose.gpu.yml，改为 "5006:5005"
```

### 问题4：GPU未识别
在Windows上：
```powershell
# 检查NVIDIA驱动
nvidia-smi

# 检查Docker GPU支持
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

---

## 📁 文件结构

```
MyGolfTracker/
├── 📄 README_WINDOWS_DEV.md          # 本文档
├── 📄 REMOTE_DEVELOPMENT_GUIDE.md   # 详细开发指南
├── 📄 WINDOWS_DEPLOYMENT_GUIDE.md   # Windows部署指南
│
├── 🔧 setup_ssh.sh                  # SSH自动配置
├── 🔄 sync_to_windows.sh            # 代码同步脚本
├── 🚀 quick_deploy.sh               # 一键部署脚本
├── 📊 check_windows_status.sh       # 状态检查脚本
│
├── 💻 start_windows.ps1             # Windows启动脚本
├── 🛑 stop_windows.ps1              # Windows停止脚本
│
└── 🐳 docker-compose.gpu.yml        # GPU版Docker配置
```

---

## 🎯 最佳实践

### 1. 开发前
```bash
# 检查Windows服务状态
./check_windows_status.sh
```

### 2. 开发中
- 使用Cursor Remote SSH直接编辑Windows文件
- 或者本地编辑后运行 `./sync_to_windows.sh`

### 3. 测试
```bash
# 部署并启动
./quick_deploy.sh

# 浏览器访问
# http://你的Windows-IP:5005/analyze/server-test
```

### 4. 提交代码
```bash
# 提交到Git（版本控制）
git add .
git commit -m "实现新功能"
git push
```

---

## 🎉 效率提升

使用此开发模式后：
- ⚡ **开发效率**：Mac编辑器体验 + Windows GPU性能
- 🔄 **自动化**：一键同步、部署、监控
- 🎮 **GPU加速**：RTX 5090 处理速度提升6-10倍
- 💾 **版本控制**：代码安全，可随时回退

---

## 📞 帮助

遇到问题？
1. 查看详细指南：`REMOTE_DEVELOPMENT_GUIDE.md`
2. 检查服务状态：`./check_windows_status.sh`
3. 重新配置SSH：`./setup_ssh.sh`
4. 查看Windows日志：`ssh windows-gpu && cd D:\MyGolfTracker && docker-compose -f docker-compose.gpu.yml logs`

---

**享受高效的跨平台开发！** 🚀

