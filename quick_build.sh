#!/bin/bash
# 快速构建脚本

echo "🚀 开始快速构建 GolfTracker 服务..."

# 检查是否有代码变化
if [ "$1" = "--force" ]; then
    echo "🔄 强制重新构建..."
    docker-compose -f docker-compose.gpu.yml down
    docker-compose -f docker-compose.gpu.yml build --no-cache
    docker-compose -f docker-compose.gpu.yml up -d
else
    echo "⚡ 增量构建（使用缓存）..."
    docker-compose -f docker-compose.gpu.yml down
    docker-compose -f docker-compose.gpu.yml build
    docker-compose -f docker-compose.gpu.yml up -d
fi

echo "✅ 构建完成！"
echo "📊 监控仪表板: http://localhost:5005/monitoring/dashboard"
echo "🔍 健康检查: http://localhost:5005/healthz"
