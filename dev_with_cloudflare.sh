#!/bin/bash

echo "🚀 启动开发环境 + Cloudflare Tunnel..."

# 检查是否在 WSL 中
if [[ ! -f /proc/version ]] || ! grep -q Microsoft /proc/version; then
    echo "⚠️  请在 WSL Ubuntu 中运行此脚本"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 设置环境变量
export CUDA_VISIBLE_DEVICES=0
export MODEL_PATH=data/best.pt
export SERVICE_PORT=5005

echo "📡 启动 FastAPI 开发服务器..."
echo "   本地访问: http://localhost:5005"
echo "   外部访问: https://swingapp.mygolfai.com.cn"
echo ""

# 在后台启动 FastAPI 服务器
python -m uvicorn app.main:app --host 0.0.0.0 --port 5005 --reload --log-level debug &
FASTAPI_PID=$!

# 等待服务器启动
echo "⏳ 等待服务器启动..."
sleep 5

# 检查服务器是否启动成功
if curl -s http://localhost:5005/healthz > /dev/null; then
    echo "✅ FastAPI 服务器启动成功！"
    
    # 启动 Cloudflare Tunnel
    echo "🌐 启动 Cloudflare Tunnel..."
    echo "   外部访问地址: https://swingapp.mygolfai.com.cn"
    echo "   按 Ctrl+C 停止所有服务"
    echo ""
    
    # 设置 Cloudflare Token
    export TUNNEL_TOKEN="eyJhIjoiYjI3MWFkZDVhMTFmNzc1NDJiZTgzY2U3ZGIwMDgxYWQiLCJ0IjoiZDhmN2RlMzAtNDA1NS00M2ZlLTkxYTktOGI5YmZmMDBhZTljIiwicyI6Ik1ETTVZelJpWlRVdFpHTTBPUzAwTWpBNExUa3hOVGd0T1RRMk1tVXpOR0ZpT1RNeSJ9"
    
    # 启动 Cloudflare Tunnel
    cloudflared tunnel --no-autoupdate run
    
else
    echo "❌ FastAPI 服务器启动失败"
    kill $FASTAPI_PID 2>/dev/null
    exit 1
fi

# 清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill $FASTAPI_PID 2>/dev/null
    echo "✅ 服务已停止"
    exit 0
}

# 捕获 Ctrl+C 信号
trap cleanup SIGINT SIGTERM

# 等待
wait
