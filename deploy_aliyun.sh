#!/bin/bash

# 阿里云服务器部署脚本
echo "=== GolfTracker 阿里云部署脚本 ==="

# 检查参数
if [ $# -lt 2 ]; then
    echo "用法: $0 <服务器IP> <SSH密钥路径或密码> [用户名(默认ubuntu)]"
    echo "示例(密钥): $0 123.123.123.123 \"~/.ssh/id_rsa\" ubuntu"
    echo "示例(密码): $0 123.123.123.123 password root"
    exit 1
fi

SERVER_IP="$1"
SSH_AUTH="$2"
REMOTE_USER="${3:-ubuntu}"
if [ "$REMOTE_USER" = "root" ]; then
  REMOTE_HOME="/root"
else
  REMOTE_HOME="/home/${REMOTE_USER}"
fi

echo "目标服务器: $SERVER_IP, 用户: $REMOTE_USER"

# 组装待打包清单，忽略不存在的文件
FILES_TO_PACK=(app analyzer detector static data requirements.txt Dockerfile docker-compose.yml scripts)
TAR_LIST=()
for item in "${FILES_TO_PACK[@]}"; do
  if [ -e "$item" ]; then
    TAR_LIST+=("$item")
  fi
done
if [ -e docker-compose.override.yml ]; then
  TAR_LIST+=("docker-compose.override.yml")
fi

# 创建部署包
echo "创建部署包..."
tar -czf golftracker_deploy.tar.gz "${TAR_LIST[@]}"
echo "部署包已创建: golftracker_deploy.tar.gz"

# 规范化密钥权限，处理路径中的空格
if [[ -f $SSH_AUTH ]]; then
  chmod 400 "$SSH_AUTH" 2>/dev/null || true
fi

# 上传到服务器
echo "上传到服务器..."
if [[ -f $SSH_AUTH ]]; then
    # 使用SSH密钥
    scp -o StrictHostKeyChecking=no -i "$SSH_AUTH" golftracker_deploy.tar.gz ${REMOTE_USER}@${SERVER_IP}:${REMOTE_HOME}/
    SSH_CMD="ssh -o StrictHostKeyChecking=no -i \"$SSH_AUTH\" ${REMOTE_USER}@${SERVER_IP}"
else
    # 使用密码（需要服务器已允许密码登录）
    scp golftracker_deploy.tar.gz ${REMOTE_USER}@${SERVER_IP}:${REMOTE_HOME}/
    SSH_CMD="ssh ${REMOTE_USER}@${SERVER_IP}"
fi

echo "文件上传完成"

# 在服务器上执行部署
echo "在服务器上执行部署..."
eval $SSH_CMD << 'EOF'
set -e
cd ~

# 解压部署包
echo "解压部署包..."
tar -xzf golftracker_deploy.tar.gz

# 提升权限
if command -v sudo >/dev/null 2>&1; then
  SUDO=sudo
else
  SUDO=""
fi

# 安装Docker（如果没有）
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    $SUDO sh get-docker.sh
    $SUDO systemctl start docker || true
    $SUDO systemctl enable docker || true
fi

# 安装Docker Compose（如果没有）
if ! command -v docker-compose &> /dev/null; then
    echo "安装Docker Compose..."
    $SUDO curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    $SUDO chmod +x /usr/local/bin/docker-compose
fi

# 构建并启动服务
echo "构建Docker镜像..."
$SUDO docker-compose build --no-cache || $SUDO docker compose build --no-cache

echo "启动服务..."
$SUDO docker-compose up -d || $SUDO docker compose up -d

# 打开5005端口（若系统使用ufw）
if command -v ufw >/dev/null 2>&1; then
  $SUDO ufw allow 5005/tcp || true
fi

# 检查服务状态
echo "检查服务状态..."
sleep 8
$SUDO docker-compose ps || $SUDO docker compose ps
$SUDO docker-compose logs --tail=50 golftracker || $SUDO docker compose logs --tail=50 golftracker || true

echo "部署完成！"
EOF

echo "=== 部署完成(本地脚本执行结束) ==="
echo "请访问: http://$SERVER_IP:5005/analyze/server-test"
