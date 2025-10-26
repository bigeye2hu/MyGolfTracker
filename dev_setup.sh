#!/bin/bash

echo "🚀 设置开发环境..."

# 检查是否在 WSL 中（可选检查）
echo "🔍 检测运行环境..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$python_version" != "3.10" ]]; then
    echo "📦 安装 Python 3.10..."
    sudo apt update
    sudo apt install -y python3.10 python3.10-dev python3.10-venv python3-pip
fi

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
python3.10 -m venv venv
source venv/bin/activate

# 升级 pip
echo "📦 升级 pip..."
pip install --upgrade pip setuptools wheel

# 安装 CUDA 版 PyTorch
echo "🎯 安装 PyTorch (CUDA 12.8)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 安装项目依赖
echo "📚 安装项目依赖..."
pip install -r requirements.txt

# 设置环境变量
echo "⚙️  设置环境变量..."
export CUDA_VISIBLE_DEVICES=0
export MODEL_PATH=data/1280p_yolo11x_5090_full.pt
export SERVICE_PORT=5005

echo "✅ 开发环境设置完成！"
echo ""
echo "🚀 启动开发服务器："
echo "   source venv/bin/activate"
echo "   python -m uvicorn app.main:app --host 0.0.0.0 --port 5005 --reload"
echo ""
echo "📊 访问地址："
echo "   本地: http://localhost:5005"
echo "   监控: http://localhost:5005/monitoring/dashboard"
