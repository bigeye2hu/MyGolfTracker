#!/bin/bash

# 🔧 SSH快速配置脚本
# 自动设置SSH连接到Windows

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   🔧 SSH连接配置向导${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 获取Windows信息
echo -e "${YELLOW}请输入Windows电脑信息：${NC}"
read -p "Windows IP地址 (例如 192.168.1.100): " WINDOWS_IP
read -p "Windows用户名 (例如 xiaoran): " WINDOWS_USER

# 检查SSH密钥
echo ""
echo -e "${BLUE}检查SSH密钥...${NC}"
if [ ! -f ~/.ssh/id_rsa ]; then
    echo -e "${YELLOW}未找到SSH密钥，正在生成...${NC}"
    ssh-keygen -t rsa -b 4096 -C "golftracker@mac" -f ~/.ssh/id_rsa -N ""
    echo -e "${GREEN}✅ SSH密钥已生成${NC}"
else
    echo -e "${GREEN}✅ SSH密钥已存在${NC}"
fi

# 复制公钥到Windows
echo ""
echo -e "${BLUE}复制公钥到Windows...${NC}"
echo "请输入Windows密码："
ssh-copy-id -i ~/.ssh/id_rsa.pub ${WINDOWS_USER}@${WINDOWS_IP}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 公钥复制成功${NC}"
else
    echo -e "${RED}❌ 公钥复制失败${NC}"
    echo "请确保Windows已启用OpenSSH服务器"
    exit 1
fi

# 配置SSH快捷方式
echo ""
echo -e "${BLUE}配置SSH快捷方式...${NC}"
mkdir -p ~/.ssh
SSH_CONFIG=~/.ssh/config

# 检查是否已存在配置
if grep -q "Host windows-gpu" "$SSH_CONFIG" 2>/dev/null; then
    echo -e "${YELLOW}配置已存在，正在更新...${NC}"
    # 删除旧配置
    sed -i.bak '/Host windows-gpu/,/^$/d' "$SSH_CONFIG"
fi

# 添加新配置
cat >> "$SSH_CONFIG" << EOF

# GolfTracker Windows GPU服务器
Host windows-gpu
    HostName $WINDOWS_IP
    User $WINDOWS_USER
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
    Compression yes
EOF

echo -e "${GREEN}✅ SSH配置已添加${NC}"

# 测试连接
echo ""
echo -e "${BLUE}测试SSH连接...${NC}"
if ssh -o ConnectTimeout=5 windows-gpu exit 2>/dev/null; then
    echo -e "${GREEN}✅ SSH连接成功！${NC}"
else
    echo -e "${RED}❌ SSH连接失败${NC}"
    exit 1
fi

# 更新脚本配置
echo ""
echo -e "${BLUE}更新同步脚本配置...${NC}"
if [ -f "sync_to_windows.sh" ]; then
    sed -i.bak "s/WINDOWS_HOST=.*/WINDOWS_HOST=\"windows-gpu\"/" sync_to_windows.sh
    echo -e "${GREEN}✅ sync_to_windows.sh 已更新${NC}"
fi

if [ -f "quick_deploy.sh" ]; then
    sed -i.bak "s/WINDOWS_IP=.*/WINDOWS_IP=\"$WINDOWS_IP\"/" quick_deploy.sh
    sed -i.bak "s/WINDOWS_HOST=.*/WINDOWS_HOST=\"windows-gpu\"/" quick_deploy.sh
    echo -e "${GREEN}✅ quick_deploy.sh 已更新${NC}"
fi

if [ -f "check_windows_status.sh" ]; then
    sed -i.bak "s/WINDOWS_HOST=.*/WINDOWS_HOST=\"windows-gpu\"/" check_windows_status.sh
    echo -e "${GREEN}✅ check_windows_status.sh 已更新${NC}"
fi

# 使脚本可执行
chmod +x sync_to_windows.sh quick_deploy.sh check_windows_status.sh 2>/dev/null

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   ✅ 配置完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}现在可以使用以下命令：${NC}"
echo ""
echo "  ssh windows-gpu           # 连接到Windows"
echo "  ./sync_to_windows.sh      # 同步代码到Windows"
echo "  ./quick_deploy.sh         # 一键部署并启动服务"
echo "  ./check_windows_status.sh # 检查Windows服务状态"
echo ""
echo -e "${YELLOW}下一步：${NC}"
echo "  在Windows上准备项目目录："
echo "  ssh windows-gpu"
echo "  mkdir -p /d/MyGolfTracker"
echo ""

