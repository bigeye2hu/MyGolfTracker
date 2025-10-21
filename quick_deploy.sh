#!/bin/bash

# 🚀 一键部署到Windows GPU服务器
# 同步代码 + 重启服务

# ===== 配置区域 =====
WINDOWS_HOST="windows-gpu"
WINDOWS_PATH="/d/MyGolfTracker"
WINDOWS_IP="192.168.1.100"  # 修改为你的Windows IP

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   🚀 快速部署到Windows GPU服务器${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 步骤1: 同步代码
echo -e "${YELLOW}步骤 1/3: 同步代码到Windows...${NC}"
./sync_to_windows.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 同步失败，终止部署${NC}"
    exit 1
fi
echo ""

# 步骤2: 停止旧服务
echo -e "${YELLOW}步骤 2/3: 停止旧服务...${NC}"
ssh $WINDOWS_HOST << 'ENDSSH'
cd /d/MyGolfTracker
if [ -f "docker-compose.gpu.yml" ]; then
    docker-compose -f docker-compose.gpu.yml down
    echo "旧服务已停止"
else
    echo "未找到旧服务，跳过"
fi
ENDSSH
echo ""

# 步骤3: 构建并启动新服务
echo -e "${YELLOW}步骤 3/3: 构建并启动GPU服务...${NC}"
ssh $WINDOWS_HOST << 'ENDSSH'
cd /d/MyGolfTracker

echo "🔨 构建Docker镜像..."
docker-compose -f docker-compose.gpu.yml build --no-cache

echo "🚀 启动服务..."
docker-compose -f docker-compose.gpu.yml up -d

echo "⏳ 等待服务启动..."
sleep 10

echo ""
echo "📊 服务状态:"
docker-compose -f docker-compose.gpu.yml ps

echo ""
echo "🎮 GPU状态:"
nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used --format=csv,noheader

echo ""
echo "📝 最新日志:"
docker-compose -f docker-compose.gpu.yml logs --tail=20
ENDSSH

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   ✅ 部署完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}🌐 访问地址:${NC}"
echo "   主页面: http://$WINDOWS_IP:5005/analyze/server-test"
echo "   健康检查: http://$WINDOWS_IP:5005/health"
echo "   转换服务: http://$WINDOWS_IP:5005/convert/test-page"
echo ""
echo -e "${BLUE}📊 查看日志:${NC}"
echo "   ssh $WINDOWS_HOST"
echo "   cd $WINDOWS_PATH"
echo "   docker-compose -f docker-compose.gpu.yml logs -f"
echo ""

# 可选：自动打开浏览器
read -p "是否自动打开浏览器? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "http://$WINDOWS_IP:5005/analyze/server-test"
fi

