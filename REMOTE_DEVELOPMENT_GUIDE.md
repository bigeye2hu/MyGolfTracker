# 🌐 远程开发配置指南 - Mac开发，Windows运行

## 🎯 目标
- 在Mac的Cursor上编辑代码
- 代码实时同步到Windows
- Windows上运行GPU加速服务
- 无缝开发体验

---

## 方案1️⃣：Remote SSH（最推荐）⭐⭐⭐⭐⭐

### 优势
- ✅ 直接编辑Windows上的文件，零延迟
- ✅ 在Cursor中直接看到Windows文件系统
- ✅ 支持终端直接在Windows执行命令
- ✅ 代码补全、调试完全支持

### Windows端配置

#### 1. 启用OpenSSH服务器
在Windows PowerShell（管理员）中执行：
```powershell
# 安装OpenSSH服务器
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# 启动SSH服务
Start-Service sshd

# 设置自动启动
Set-Service -Name sshd -StartupType 'Automatic'

# 确认服务运行
Get-Service sshd

# 配置防火墙（如果需要）
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

#### 2. 查看Windows IP地址
```powershell
ipconfig
# 记下IPv4地址，例如：192.168.1.100
```

#### 3. 创建项目目录
```powershell
# 在Windows上创建项目目录
mkdir D:\MyGolfTracker
cd D:\MyGolfTracker
```

### Mac端配置

#### 1. 生成SSH密钥并复制到Windows
```bash
# 生成SSH密钥（如果还没有）
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 复制公钥到Windows（需要输入Windows密码）
# 方式A：使用ssh-copy-id（推荐）
ssh-copy-id 你的Windows用户名@192.168.1.100

# 方式B：手动复制
cat ~/.ssh/id_rsa.pub | ssh 你的Windows用户名@192.168.1.100 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# 测试SSH连接（不需要密码即成功）
ssh 你的Windows用户名@192.168.1.100
```

#### 2. 配置SSH快捷方式
编辑 `~/.ssh/config`：
```bash
nano ~/.ssh/config
```

添加以下内容：
```
Host windows-gpu
    HostName 192.168.1.100
    User 你的Windows用户名
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

保存后，可以简单地使用：
```bash
ssh windows-gpu
```

#### 3. 在Cursor中使用Remote SSH

**选项A：使用VS Code Remote SSH扩展**
1. 在Cursor中安装 "Remote - SSH" 扩展
2. 按 `Cmd+Shift+P`，输入 "Remote-SSH: Connect to Host"
3. 选择 "windows-gpu"
4. Cursor会连接到Windows，打开 `D:\MyGolfTracker` 文件夹
5. 现在你编辑的就是Windows上的文件！

**选项B：使用命令行同步（如果Remote SSH不支持）**
```bash
# 安装rsync（Mac上通常已安装）
brew install rsync

# 创建同步脚本（见下方"方案3"）
```

### 4. 开发流程

```bash
# 1. 在Cursor中连接到Windows
# 按 Cmd+Shift+P → Remote-SSH: Connect to Host → windows-gpu

# 2. 打开项目文件夹
# File → Open Folder → D:\MyGolfTracker

# 3. 在Cursor的终端中直接运行Windows命令
# Terminal → New Terminal（这是Windows的PowerShell）

# 启动服务
.\start_windows.ps1

# 查看日志
docker-compose -f docker-compose.gpu.yml logs -f

# 停止服务
.\stop_windows.ps1
```

---

## 方案2️⃣：SMB共享文件夹（最简单）⭐⭐⭐⭐

### Windows端配置

#### 1. 共享项目文件夹
```powershell
# 在PowerShell（管理员）中执行
$shareName = "MyGolfTracker"
$folderPath = "D:\MyGolfTracker"

# 创建共享
New-SmbShare -Name $shareName -Path $folderPath -FullAccess "Everyone"

# 设置权限
Grant-SmbShareAccess -Name $shareName -AccountName "Everyone" -AccessRight Full -Force
```

#### 2. 查看共享路径
```powershell
Get-SmbShare -Name MyGolfTracker
# 共享路径: \\你的电脑名\MyGolfTracker
```

### Mac端配置

#### 1. 挂载Windows共享文件夹

**方式A：使用Finder（图形界面）**
1. 打开Finder
2. 按 `Cmd+K`
3. 输入：`smb://192.168.1.100/MyGolfTracker`
4. 输入Windows用户名和密码
5. 共享文件夹会挂载到 `/Volumes/MyGolfTracker`

**方式B：使用命令行**
```bash
# 创建挂载点
mkdir -p ~/WindowsProjects/MyGolfTracker

# 挂载
mount_smbfs //你的Windows用户名:密码@192.168.1.100/MyGolfTracker ~/WindowsProjects/MyGolfTracker
```

#### 2. 在Cursor中打开挂载的文件夹
```bash
# 打开Cursor
cursor ~/WindowsProjects/MyGolfTracker
# 或
cursor /Volumes/MyGolfTracker
```

#### 3. 开发流程
```bash
# 1. 在Cursor中直接编辑文件
# 文件会实时同步到Windows

# 2. 在Mac的终端中SSH到Windows运行命令
ssh windows-gpu
cd D:\MyGolfTracker
.\start_windows.ps1
```

---

## 方案3️⃣：Git + 自动同步脚本⭐⭐⭐⭐

### 创建自动同步脚本

在Mac的项目目录下创建 `sync_to_windows.sh`：

```bash
#!/bin/bash

# 配置
WINDOWS_HOST="windows-gpu"
WINDOWS_PATH="/d/MyGolfTracker"
LOCAL_PATH="/Users/huxiaoran/Documents/xiaoranProjects/GolfTracker/MyGolfTracker"

echo "🔄 开始同步到Windows..."

# 方式1：使用rsync（推荐）
rsync -avz --exclude 'venv/' \
           --exclude '__pycache__/' \
           --exclude '*.pyc' \
           --exclude '*.log' \
           --exclude '.git/' \
           --exclude '*.tar.gz' \
           "$LOCAL_PATH/" "$WINDOWS_HOST:$WINDOWS_PATH/"

# 方式2：使用Git
# cd "$LOCAL_PATH"
# git add .
# git commit -m "Auto sync $(date '+%Y-%m-%d %H:%M:%S')"
# git push
# ssh $WINDOWS_HOST "cd $WINDOWS_PATH && git pull"

echo "✅ 同步完成！"

# 可选：自动重启Windows上的服务
# ssh $WINDOWS_HOST "cd $WINDOWS_PATH && docker-compose -f docker-compose.gpu.yml up -d --build"
```

使脚本可执行：
```bash
chmod +x sync_to_windows.sh
```

### 使用方式

```bash
# 手动同步
./sync_to_windows.sh

# 或者配置文件监控自动同步（使用fswatch）
brew install fswatch

# 创建自动监控脚本
cat > auto_sync.sh << 'EOF'
#!/bin/bash
fswatch -o . -e ".*\.pyc$" -e "__pycache__" -e "venv/" | while read f; do 
    echo "检测到文件变化，开始同步..."
    ./sync_to_windows.sh
done
EOF

chmod +x auto_sync.sh

# 运行自动监控（在新终端窗口）
./auto_sync.sh
```

---

## 方案4️⃣：VS Code Tasks自动同步⭐⭐⭐

在项目根目录创建 `.vscode/tasks.json`：

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Sync to Windows",
            "type": "shell",
            "command": "rsync",
            "args": [
                "-avz",
                "--exclude", "venv/",
                "--exclude", "__pycache__/",
                "--exclude", "*.pyc",
                "--exclude", ".git/",
                "${workspaceFolder}/",
                "windows-gpu:/d/MyGolfTracker/"
            ],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Sync and Restart Service",
            "type": "shell",
            "dependsOn": "Sync to Windows",
            "command": "ssh",
            "args": [
                "windows-gpu",
                "cd /d/MyGolfTracker && docker-compose -f docker-compose.gpu.yml up -d --build"
            ],
            "group": "build"
        }
    ]
}
```

使用方式：
- 按 `Cmd+Shift+P`
- 输入 "Tasks: Run Task"
- 选择 "Sync to Windows" 或 "Sync and Restart Service"

或者配置快捷键 `.vscode/keybindings.json`：
```json
[
    {
        "key": "cmd+shift+s",
        "command": "workbench.action.tasks.runTask",
        "args": "Sync to Windows"
    }
]
```

---

## 🎯 推荐工作流程

### 日常开发流程

#### 方式A：Remote SSH（最佳体验）
```bash
# 1. 启动Cursor，连接到Windows
# Cmd+Shift+P → Remote-SSH: Connect to Host → windows-gpu

# 2. 打开项目文件夹 D:\MyGolfTracker

# 3. 编辑代码（实时保存到Windows）

# 4. 在Cursor的终端中运行
.\start_windows.ps1

# 5. 浏览器访问 http://localhost:5005/analyze/server-test
```

#### 方式B：本地编辑 + 同步
```bash
# 1. 在Mac的Cursor中编辑代码

# 2. 保存后，运行同步
./sync_to_windows.sh

# 3. SSH到Windows运行服务
ssh windows-gpu
cd D:\MyGolfTracker
.\start_windows.ps1

# 4. 在Mac浏览器访问 http://192.168.1.100:5005/analyze/server-test
```

---

## 🔧 实用脚本集合

### quick_deploy.sh（一键部署到Windows）
```bash
#!/bin/bash
echo "🚀 快速部署到Windows GPU服务器"

# 同步代码
./sync_to_windows.sh

# 远程重启服务
echo "🔄 重启Windows服务..."
ssh windows-gpu << 'ENDSSH'
cd /d/MyGolfTracker
docker-compose -f docker-compose.gpu.yml down
docker-compose -f docker-compose.gpu.yml up -d --build
docker-compose -f docker-compose.gpu.yml logs --tail=20
ENDSSH

echo "✅ 部署完成！"
echo "🌐 访问: http://192.168.1.100:5005/analyze/server-test"
```

### check_windows_status.sh（检查Windows服务状态）
```bash
#!/bin/bash
echo "📊 检查Windows GPU服务状态"

ssh windows-gpu << 'ENDSSH'
echo "=== Docker 容器状态 ==="
docker-compose -f /d/MyGolfTracker/docker-compose.gpu.yml ps

echo ""
echo "=== GPU 状态 ==="
nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv

echo ""
echo "=== 最新日志 ==="
docker-compose -f /d/MyGolfTracker/docker-compose.gpu.yml logs --tail=10
ENDSSH
```

### 使脚本可执行
```bash
chmod +x quick_deploy.sh
chmod +x check_windows_status.sh
chmod +x sync_to_windows.sh
```

---

## 📝 总结对比

| 方案 | 延迟 | 配置难度 | 自动化 | 推荐场景 |
|------|------|----------|--------|----------|
| Remote SSH | 无 | 中 | ⭐⭐⭐⭐⭐ | 日常开发 |
| SMB共享 | 低 | 低 | ⭐⭐⭐ | 简单场景 |
| Git自动同步 | 中 | 中 | ⭐⭐⭐⭐ | 版本控制 |
| rsync同步 | 低 | 高 | ⭐⭐⭐⭐ | 高级用户 |

## 🎉 我的推荐

**最佳组合：Remote SSH + Git版本控制**
1. 日常开发使用Remote SSH直接编辑Windows文件
2. 重要节点使用Git提交版本
3. 保持代码在GitHub/Gitee备份

这样既有实时编辑的便捷性，又有版本控制的安全性！

