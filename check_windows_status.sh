#!/bin/bash

# 📊 检查Windows GPU服务器状态

# ===== 配置区域 =====
WINDOWS_HOST="windows-gpu"
WINDOWS_PATH="/d/MyGolfTracker"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   📊 Windows GPU服务器状态检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查SSH连接
echo -e "${YELLOW}🔌 检查网络连接...${NC}"
if ! ssh -o ConnectTimeout=5 $WINDOWS_HOST exit 2>/dev/null; then
    echo -e "${RED}❌ 无法连接到Windows服务器${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 连接正常${NC}"
echo ""

# 远程执行检查
ssh $WINDOWS_HOST << 'ENDSSH'
# 颜色定义（在远程环境中）
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━ Docker容器状态 ━━━${NC}"
cd /d/MyGolfTracker
if [ -f "docker-compose.gpu.yml" ]; then
    docker-compose -f docker-compose.gpu.yml ps
else
    echo -e "${RED}未找到docker-compose.gpu.yml${NC}"
fi

echo ""
echo -e "${BLUE}━━━ GPU状态 ━━━${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv
else
    echo -e "${RED}nvidia-smi未找到${NC}"
fi

echo ""
echo -e "${BLUE}━━━ 系统资源 ━━━${NC}"
echo "CPU使用率:"
wmic cpu get loadpercentage 2>/dev/null || echo "无法获取CPU信息"

echo ""
echo "内存使用:"
wmic OS get FreePhysicalMemory,TotalVisibleMemorySize 2>/dev/null || echo "无法获取内存信息"

echo ""
echo -e "${BLUE}━━━ 网络端口 ━━━${NC}"
netstat -ano | findstr :5005 | head -n 5

echo ""
echo -e "${BLUE}━━━ 最新服务日志 ━━━${NC}"
cd /d/MyGolfTracker
if [ -f "docker-compose.gpu.yml" ]; then
    docker-compose -f docker-compose.gpu.yml logs --tail=15
else
    echo -e "${RED}无法获取日志${NC}"
fi
ENDSSH

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   检查完成${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

