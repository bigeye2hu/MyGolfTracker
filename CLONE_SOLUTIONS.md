# 🔧 WSL克隆超时解决方案

## ❌ 问题：克隆时超时

**原因：** 模型文件较大（best.pt: 114MB, ClubDetection_1000P_50R.pt: 136MB），Git LFS下载时容易超时

## ✅ 解决方案（按推荐顺序）

### 方案1️⃣：先克隆代码，后下载模型（推荐）⭐⭐⭐⭐⭐

```bash
# 在WSL中执行

# 1. 设置Git不自动下载LFS文件
export GIT_LFS_SKIP_SMUDGE=1

# 2. 克隆项目（只下载代码，不下载大文件）
cd ~/projects
git clone https://github.com/bigeye2hu/MyGolfTracker.git
cd MyGolfTracker

# 3. 增加Git超时时间
git config --global http.postBuffer 524288000
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999

# 4. 单独下载模型文件（可重试）
git lfs install
git lfs pull

# 如果还是超时，可以单独下载每个文件
git lfs pull --include="data/best.pt"
# 等成功后再下载另一个
git lfs pull --include="data/ClubDetection_1000P_50R.pt"
```

### 方案2️⃣：从Mac直接传输模型文件⭐⭐⭐⭐

**在Mac上：**
```bash
cd /Users/huxiaoran/Documents/xiaoranProjects/GolfTracker/MyGolfTracker

# 找到Windows的IP（或用localhost）
# 假设Windows用户名是 xiaoran，IP是 192.168.1.100

# 通过SCP传输模型文件到WSL
scp data/best.pt xiaoran@192.168.1.100:/tmp/
scp data/ClubDetection_1000P_50R.pt xiaoran@192.168.1.100:/tmp/
```

**在Windows WSL中：**
```bash
# 先克隆项目（不含大文件）
export GIT_LFS_SKIP_SMUDGE=1
cd ~/projects
git clone https://github.com/bigeye2hu/MyGolfTracker.git
cd MyGolfTracker

# 从Windows临时目录复制模型文件
cp /mnt/c/Users/你的Windows用户名/Downloads/best.pt data/
cp /mnt/c/Users/你的Windows用户名/Downloads/ClubDetection_1000P_50R.pt data/

# 或从tmp复制
# sudo cp /tmp/best.pt data/
# sudo cp /tmp/ClubDetection_1000P_50R.pt data/
```

### 方案3️⃣：使用浅克隆⭐⭐⭐

```bash
# 只克隆最近的提交，减少数据量
cd ~/projects
git clone --depth 1 https://github.com/bigeye2hu/MyGolfTracker.git
cd MyGolfTracker

# 增加超时配置
git config http.postBuffer 524288000
git config http.lowSpeedLimit 0

# 下载模型文件
git lfs install
git lfs pull
```

### 方案4️⃣：分步下载⭐⭐⭐

```bash
# 1. 克隆时跳过LFS
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/bigeye2hu/MyGolfTracker.git
cd MyGolfTracker

# 2. 安装Git LFS
sudo apt install -y git-lfs
git lfs install

# 3. 只下载一个必需的模型文件（best.pt是主要的）
git lfs pull --include="data/best.pt"

# 4. 先用这个模型测试服务是否能启动
# 等需要时再下载另一个
# git lfs pull --include="data/ClubDetection_1000P_50R.pt"
```

### 方案5️⃣：使用代理或镜像⭐⭐

**如果有代理：**
```bash
# 配置Git代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy https://127.0.0.1:7890

# 然后正常克隆
git clone https://github.com/bigeye2hu/MyGolfTracker.git
```

**使用Gitee镜像（如果有）：**
```bash
# 如果你把项目也推送到了Gitee
git clone https://gitee.com/你的用户名/MyGolfTracker.git
```

## 🎯 推荐流程（最稳妥）

### 步骤1：先获取代码
```bash
cd ~/projects
export GIT_LFS_SKIP_SMUDGE=1
git clone https://github.com/bigeye2hu/MyGolfTracker.git
cd MyGolfTracker
```

### 步骤2：从Mac复制模型文件

**方法A：通过Windows共享文件夹**
1. 在Mac上把 `data/best.pt` 和 `data/ClubDetection_1000P_50R.pt` 复制到U盘或网络共享
2. 在Windows上下载这两个文件
3. 在WSL中复制：
```bash
cp /mnt/c/Users/你的用户名/Downloads/*.pt ~/projects/MyGolfTracker/data/
```

**方法B：通过SSH/SCP**
```bash
# 在Mac上执行
scp data/*.pt 你的Windows用户名@你的Windows-IP:/tmp/

# 在WSL中执行
cp /tmp/*.pt ~/projects/MyGolfTracker/data/
```

### 步骤3：验证文件
```bash
cd ~/projects/MyGolfTracker
ls -lh data/

# 应该看到：
# best.pt (约114M)
# ClubDetection_1000P_50R.pt (约136M)
```

### 步骤4：启动服务
```bash
docker-compose -f docker-compose.gpu.yml up -d --build
```

## 💡 临时方案：只用主模型

如果实在下载不下来，可以先只用 `best.pt`：

```bash
# 只下载主模型
git lfs pull --include="data/best.pt"

# 删除另一个模型的引用
rm -f data/ClubDetection_1000P_50R.pt

# 启动服务（只使用best.pt）
docker-compose -f docker-compose.gpu.yml up -d --build
```

服务主要使用 `best.pt`，`ClubDetection_1000P_50R.pt` 是备用模型。

## 🔍 验证克隆是否成功

```bash
cd ~/projects/MyGolfTracker

# 检查代码文件
ls -la app/ analyzer/ detector/

# 检查模型文件大小
ls -lh data/
# best.pt 应该是 114M 左右
# ClubDetection_1000P_50R.pt 应该是 136M 左右

# 如果显示的是几KB，说明是LFS指针文件，需要执行git lfs pull
```

## ⚡ 快速诊断

```bash
# 检查是否是LFS指针文件
file data/best.pt

# 如果显示 "ASCII text"，说明还没下载真实文件
# 如果显示 "data"，说明是二进制文件，下载成功了
```

## 📞 还是不行？

可以直接从Mac上打包发送：

```bash
# 在Mac上
cd /Users/huxiaoran/Documents/xiaoranProjects/GolfTracker/MyGolfTracker
tar -czf models.tar.gz data/*.pt

# 通过U盘或其他方式传到Windows

# 在WSL中解压
cd ~/projects/MyGolfTracker
tar -xzf /mnt/c/Users/你的用户名/Downloads/models.tar.gz
```

选择最适合你的方案！推荐先试**方案1**，不行就用**方案2**（从Mac直接复制）。

