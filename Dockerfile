FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖（很少变化，放在前面）
RUN apt-get update && apt-get install -y \
    python3.10 python3.10-dev python3-pip \
    ffmpeg libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# 创建python软链接
RUN ln -sf /usr/bin/python3.10 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.10 /usr/bin/python && \
    python -m pip install --upgrade pip setuptools wheel

WORKDIR /app

# ===== 安装 GPU 版 PyTorch (CUDA 12.8) =====
# 直接安装支持RTX 5090的cu128版本（很少变化，放在前面）
# 固定版本号确保一致性
RUN pip install --no-cache-dir torch==2.9.0+cu128 torchvision==0.24.0+cu128 torchaudio==2.9.0+cu128 --index-url https://download.pytorch.org/whl/cu128

# ===== 安装项目依赖 =====
# 先复制 requirements.txt（这样只有依赖变化时才重新安装）
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple \
    --trusted-host mirrors.aliyun.com -r /app/requirements.txt || \
    pip install --no-cache-dir -r /app/requirements.txt

# ===== 拷贝源码（经常变化，放在最后） =====
COPY app /app/app
COPY analyzer /app/analyzer
COPY detector /app/detector
COPY static /app/static
COPY data /app/data

EXPOSE 5005

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5005", "--log-level", "debug", "--timeout-keep-alive", "300"]