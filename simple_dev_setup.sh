#!/bin/bash

echo "🚀 简化开发环境设置..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "📦 当前 Python 版本: $python_version"

# 检查是否已安装必要的包
echo "🔍 检查依赖包..."
if ! python3 -c "import torch" 2>/dev/null; then
    echo "📦 安装 PyTorch (CUDA 12.8)..."
    python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
else
    echo "✅ PyTorch 已安装"
fi

# 安装项目依赖
echo "📚 安装项目依赖..."
python3 -m pip install -r requirements.txt

# 设置环境变量
echo "⚙️  设置环境变量..."
export CUDA_VISIBLE_DEVICES=0
export MODEL_PATH=data/best.pt
export SERVICE_PORT=5005

echo "✅ 开发环境设置完成！"
echo ""
echo "🚀 启动开发服务器："
echo "   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 5005 --reload"
echo ""
echo "📊 访问地址："
echo "   本地: http://localhost:5005"
echo "   监控: http://localhost:5005/monitoring/dashboard"
