#!/bin/bash

echo "🚀 部署到生产环境..."

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down

# 构建并启动生产环境
echo "📦 构建生产镜像..."
docker-compose build

echo "🚀 启动生产服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
curl -s http://localhost:5005/healthz > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ 生产服务启动成功！"
    echo "📊 监控面板: http://localhost:5005/monitoring/dashboard"
    echo "🔍 健康检查: http://localhost:5005/healthz"
else
    echo "❌ 服务启动失败，请检查日志："
    echo "   docker logs golftracker-service"
fi
