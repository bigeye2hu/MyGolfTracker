#!/bin/bash

echo "🐍 本地测试 GolfTracker 服务..."

python3 --version

echo "📦 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

echo "🔧 安装依赖..."
pip install -r requirements.txt

echo "🚀 启动服务..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 5005 --reload
