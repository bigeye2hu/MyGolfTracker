# 🚀 Windows快速部署指南（使用Git）

## 前提条件
- ✅ Windows 10/11
- ✅ 已安装 [Git for Windows](https://git-scm.com/download/win)
- ✅ 已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- ✅ NVIDIA RTX 5090显卡 + 最新驱动

## 📦 方式1：从远程仓库克隆（推荐）

### 步骤1：克隆项目
在Windows PowerShell中：
```powershell
# 进入工作目录
cd D:\Projects  # 或任意你喜欢的位置

# 克隆项目
git clone <你的仓库地址> MyGolfTracker

# 进入项目
cd MyGolfTracker
```

### 步骤2：安装NVIDIA Docker支持
```powershell
# 启动WSL2
wsl

# 在WSL中执行
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo service docker restart
exit
```

### 步骤3：启动服务
```powershell
# 方法A：使用启动脚本（推荐）
.\start_windows.ps1

# 方法B：手动启动
docker-compose -f docker-compose.gpu.yml up -d --build
```

### 步骤4：验证
浏览器访问：http://localhost:5005/analyze/server-test

---

## 📦 方式2：本地推送到远程，然后克隆

### 在Mac上（当前项目目录）

#### 步骤1：初始化Git仓库（如果还没有）
```bash
cd /Users/huxiaoran/Documents/xiaoranProjects/GolfTracker/MyGolfTracker

# 检查是否已有Git仓库
git status

# 如果没有，初始化
git init
git add .
git commit -m "Initial commit for cross-platform deployment"
```

#### 步骤2：创建远程仓库并推送
```bash
# 方式A：GitHub
# 1. 在GitHub上创建新仓库：MyGolfTracker
# 2. 添加远程并推送
git remote add origin https://github.com/<你的用户名>/MyGolfTracker.git
git branch -M main
git push -u origin main

# 方式B：Gitee（国内速度快）
# 1. 在Gitee上创建新仓库：MyGolfTracker
# 2. 添加远程并推送
git remote add origin https://gitee.com/<你的用户名>/MyGolfTracker.git
git branch -M main
git push -u origin main
```

#### 步骤3：处理大文件（模型文件）
```bash
# data/best.pt 文件109MB，建议用Git LFS
brew install git-lfs  # Mac上安装Git LFS
git lfs install
git lfs track "data/*.pt"
git add .gitattributes
git commit -m "Track model files with Git LFS"
git push
```

### 在Windows上

```powershell
# 克隆仓库
cd D:\
git clone https://github.com/<你的用户名>/MyGolfTracker.git
# 或 Gitee
git clone https://gitee.com/<你的用户名>/MyGolfTracker.git

cd MyGolfTracker

# 安装Git LFS（如果有大文件）
git lfs install
git lfs pull

# 启动服务
.\start_windows.ps1
```

---

## 🔄 后续更新流程

### Mac上修改代码后：
```bash
git add .
git commit -m "Update detection algorithm"
git push
```

### Windows上同步更新：
```powershell
cd D:\MyGolfTracker
git pull

# 重新构建并启动
docker-compose -f docker-compose.gpu.yml up -d --build
```

---

## 📁 项目结构（Git管理的文件）

```
MyGolfTracker/
├── .git/                          # Git仓库（自动创建）
├── .gitignore                     # Git忽略规则
├── app/                          # ✅ 纳入版本控制
├── analyzer/                     # ✅ 纳入版本控制
├── detector/                     # ✅ 纳入版本控制
├── static/                       # ✅ 纳入版本控制
├── data/
│   └── best.pt                   # ⚠️ 大文件，建议Git LFS
├── docker-compose.gpu.yml        # ✅ 纳入版本控制
├── Dockerfile.gpu                # ✅ 纳入版本控制
├── requirements.txt              # ✅ 纳入版本控制
├── start_windows.ps1            # ✅ 纳入版本控制
├── venv/                        # ❌ .gitignore忽略
├── *.log                        # ❌ .gitignore忽略
└── *.tar.gz                     # ❌ .gitignore忽略
```

---

## 🎯 推荐的Git托管平台

### GitHub
- ✅ 最流行，生态最好
- ✅ 免费私有仓库
- ❌ 国内访问较慢
- 🔗 https://github.com

### Gitee（码云）
- ✅ 国内速度快
- ✅ 免费私有仓库
- ✅ 适合国内团队
- 🔗 https://gitee.com

### GitLab
- ✅ 功能强大
- ✅ 可自建服务器
- 🔗 https://gitlab.com

---

## 🔧 常用Git命令速查

```powershell
# 查看状态
git status

# 拉取最新代码
git pull

# 查看修改
git diff

# 提交修改
git add .
git commit -m "描述"
git push

# 查看日志
git log --oneline

# 回退版本
git checkout <commit-id>

# 创建分支
git checkout -b feature/new-feature

# 切换分支
git checkout main

# 合并分支
git merge feature/new-feature
```

---

## 🐛 故障排除

### 问题1：克隆速度慢
**解决方案：**
```powershell
# 方法1：使用Gitee镜像
# 方法2：配置Git代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy https://127.0.0.1:7890

# 方法3：浅克隆（只克隆最新版本）
git clone --depth 1 <仓库地址>
```

### 问题2：大文件推送失败
**解决方案：**
```bash
# 使用Git LFS
git lfs install
git lfs track "data/*.pt"
git add .gitattributes
git commit -m "Use Git LFS for model files"
git push
```

### 问题3：认证失败
**解决方案：**
```powershell
# GitHub现在需要使用Personal Access Token
# 1. 访问 GitHub Settings → Developer settings → Personal access tokens
# 2. 生成新token
# 3. 使用token代替密码
```

---

## ✨ 最佳实践建议

1. **提交前检查**：`git status` 和 `git diff`
2. **频繁提交**：小步提交，便于回退
3. **有意义的提交信息**：描述清楚改了什么
4. **使用分支**：功能开发在独立分支，完成后合并
5. **定期推送**：避免代码只在本地
6. **.gitignore完善**：避免提交不必要的文件

---

## 🎉 完成！

现在你可以：
- ✅ 在Mac上开发，推送到远程
- ✅ 在Windows上拉取，使用GPU运行
- ✅ 版本控制，随时回退
- ✅ 团队协作，代码共享

