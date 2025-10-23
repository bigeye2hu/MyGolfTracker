#!/bin/bash

echo "🚀 启动开发服务器..."

# 激活虚拟环境
source venv/bin/activate

# 设置环境变量
export CUDA_VISIBLE_DEVICES=0
export MODEL_PATH=data/best.pt
export SERVICE_PORT=5005

# 启动开发服务器（支持热重载）
echo "📡 启动 FastAPI 开发服务器..."
echo "   修改代码后会自动重启"
echo "   按 Ctrl+C 停止服务器"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 5005 --reload --log-level debug