#!/bin/bash
# 开发模式启动脚本

echo "🔧 启动开发模式..."

# 使用开发配置启动
docker-compose -f docker-compose.dev.yml up -d

echo "✅ 开发模式启动完成！"
echo "📊 监控仪表板: http://localhost:5005/monitoring/dashboard"
echo "🔍 健康检查: http://localhost:5005/healthz"
echo ""
echo "💡 开发模式特点："
echo "   - 代码目录已挂载，修改代码后重启容器即可"
echo "   - 使用优化的 Dockerfile，构建更快"
echo "   - 数据目录只读挂载，保护模型文件"
echo ""
echo "🔄 重启服务: docker-compose -f docker-compose.dev.yml restart"
echo "🛑 停止服务: docker-compose -f docker-compose.dev.yml down"
