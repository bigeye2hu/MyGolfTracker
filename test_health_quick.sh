#!/bin/bash
# 快速测试健康检查端点的脚本

echo "🚀 测试 GolfTracker 服务健康检查端点"
echo "=================================="

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 3

# 测试 /healthz 端点
echo ""
echo "🔍 测试 /healthz 端点:"
curl -s http://localhost:5005/healthz | python3 -m json.tool 2>/dev/null || echo "❌ /healthz 端点不可用"

# 测试 /metrics 端点
echo ""
echo "🔍 测试 /metrics 端点:"
curl -s http://localhost:5005/metrics | head -20

# 测试原有 /health 端点
echo ""
echo "🔍 测试原有 /health 端点:"
curl -s http://localhost:5005/health | python3 -m json.tool 2>/dev/null || echo "❌ /health 端点不可用"

echo ""
echo "✅ 测试完成"
