#!/bin/bash

# 快速构建脚本 - 利用 Docker 缓存
echo "🚀 开始快速构建..."

# 检查是否有 --force 参数
if [ "$1" = "--force" ]; then
    echo "⚠️  强制重建，清除所有缓存..."
    docker-compose down --volumes --rmi all
    docker system prune -f
    docker-compose build --no-cache
else
    echo "📦 使用缓存构建（推荐）..."
    docker-compose build
fi

echo "✅ 构建完成，启动服务..."
docker-compose up -d

echo "🎉 服务已启动！"
echo "📊 监控面板: http://localhost:5005/monitoring/dashboard"
echo "🔍 健康检查: http://localhost:5005/healthz"