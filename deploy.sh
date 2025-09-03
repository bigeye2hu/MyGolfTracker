#!/bin/bash

echo "🚀 开始部署 MyGolfTracker..."

# 检查必要文件
if [ ! -f "Dockerfile" ] || [ ! -f "docker-compose.yml" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ 缺少必要文件，请检查项目完整性"
    exit 1
fi

# 1. 创建部署包
echo "📦 创建部署包..."
tar -czf MyGolfTracker_deployment.tar.gz \
    app/ analyzer/ detector/ data/ \
    Dockerfile docker-compose.yml requirements.txt \
    scripts/ README.md

if [ $? -ne 0 ]; then
    echo "❌ 创建部署包失败"
    exit 1
fi

echo "✅ 部署包创建成功: MyGolfTracker_deployment.tar.gz"

# 2. 上传到服务器
echo "📤 上传到服务器..."
scp MyGolfTracker_deployment.tar.gz root@143.244.211.22:/tmp/

if [ $? -ne 0 ]; then
    echo "❌ 上传失败，请检查网络连接和服务器状态"
    exit 1
fi

echo "✅ 部署包上传成功"

# 3. 远程部署
echo "🔧 开始远程部署..."
sshpass -p '27Yk*a-k#R￼' ssh -o StrictHostKeyChecking=no root@143.244.211.22 << 'REMOTE_EOF'
echo "🔄 在服务器上开始部署..."

# 解压部署包
cd /tmp
tar -xzf MyGolfTracker_deployment.tar.gz

# 清理旧项目
rm -rf /www/wwwroot/golf_golftracker
mkdir -p /www/wwwroot/golf_golftracker

# 复制新项目
cp -r * /www/wwwroot/golf_golftracker/

# 设置权限
cd /www/wwwroot/golf_golftracker
chmod +x scripts/*.sh

# 启动服务
echo "🚀 启动服务..."
./scripts/start_service.sh

echo "✅ 服务器端部署完成"
REMOTE_EOF

if [ $? -ne 0 ]; then
    echo "❌ 远程部署失败"
    exit 1
fi

echo "✅ 部署完成！"
echo "🌐 服务地址: http://143.244.211.22:5005"
echo "🔍 健康检查: http://143.244.211.22:5005/health"

# 清理本地部署包
rm -f MyGolfTracker_deployment.tar.gz
echo "🧹 本地部署包已清理"
