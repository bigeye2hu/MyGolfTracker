#!/bin/bash

# 🔄 Mac到Windows自动同步脚本
# 使用前配置SSH快捷方式（见REMOTE_DEVELOPMENT_GUIDE.md）

# ===== 配置区域 =====
WINDOWS_HOST="windows-gpu"  # 修改为你的Windows SSH别名或IP
WINDOWS_PATH="/d/MyGolfTracker"  # Windows上的项目路径（WSL格式）
LOCAL_PATH="$(pwd)"  # 当前目录

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 开始同步到Windows GPU服务器...${NC}"
echo "本地路径: $LOCAL_PATH"
echo "远程主机: $WINDOWS_HOST"
echo "远程路径: $WINDOWS_PATH"
echo ""

# 检查SSH连接
echo -e "${BLUE}检查SSH连接...${NC}"
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes $WINDOWS_HOST exit 2>/dev/null; then
    echo -e "${RED}❌ 无法连接到Windows服务器！${NC}"
    echo "请确保："
    echo "1. Windows已启用OpenSSH服务器"
    echo "2. SSH配置正确（~/.ssh/config）"
    echo "3. 网络连接正常"
    exit 1
fi
echo -e "${GREEN}✅ SSH连接正常${NC}"
echo ""

# 使用rsync同步文件
echo -e "${BLUE}开始同步文件...${NC}"
rsync -avz --progress \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '*.pyo' \
    --exclude '*.log' \
    --exclude '.git/' \
    --exclude '.vscode/' \
    --exclude '.idea/' \
    --exclude '*.tar.gz' \
    --exclude 'golftracker_deploy.tar.gz' \
    --exclude 'golftracker_gpu_deploy.tar.gz' \
    --exclude 'MyGolfTracker_deployment.tar.gz' \
    --exclude 'test_video.mp4' \
    --exclude '.DS_Store' \
    "$LOCAL_PATH/" "$WINDOWS_HOST:$WINDOWS_PATH/"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 同步完成！${NC}"
    echo ""
    echo "下一步："
    echo "  1. SSH到Windows: ssh $WINDOWS_HOST"
    echo "  2. 启动服务: cd $WINDOWS_PATH && ./start_windows.ps1"
    echo "  或运行: ./quick_deploy.sh 一键部署并启动"
else
    echo -e "${RED}❌ 同步失败！${NC}"
    exit 1
fi

