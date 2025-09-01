#!/bin/bash

echo "🏌️ 启动 GolfTracker 服务..."

if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

echo "🔨 构建 Docker 镜像..."
docker-compose up --build -d

echo "⏳ 等待服务启动..."
sleep 10

echo "🔍 健康检查..."
if curl -f http://localhost:5005/health > /dev/null 2>&1; then
    echo "✅ 服务启动成功！"
    echo "🌐 服务地址: http://localhost:5005"
    echo "📊 健康检查: http://localhost:5005/health"
else
    echo "❌ 服务启动失败，查看日志:"
    docker-compose logs
    exit 1
