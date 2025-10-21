FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 写入国内 Debian 源（自动识别 $VERSION_CODENAME），并安装系统依赖
RUN . /etc/os-release && echo "deb https://mirrors.ustc.edu.cn/debian/ $VERSION_CODENAME main contrib non-free non-free-firmware\n\
deb https://mirrors.ustc.edu.cn/debian/ $VERSION_CODENAME-updates main contrib non-free non-free-firmware\n\
deb https://mirrors.ustc.edu.cn/debian/ $VERSION_CODENAME-backports main contrib non-free non-free-firmware\n\
deb https://mirrors.ustc.edu.cn/debian-security $VERSION_CODENAME-security main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    rm -f /etc/apt/sources.list.d/* /etc/apt/sources.list.d/debian.sources 2>/dev/null || true && \
    apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=30 update && \
    apt-get install -y --no-install-recommends ffmpeg libgl1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 创建 wheels 目录
RUN mkdir -p /wheels

ARG TORCH_VERSION=2.1.0+cu118
ARG TORCHVISION_VERSION=0.16.0+cu118
COPY requirements.txt /app/requirements.txt
# 使用国内 PyPI 镜像加速，失败则回退官方
RUN set -ex; \
    # 安装GPU版本的torch和torchvision
    pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple \
        --trusted-host mirrors.aliyun.com \
        "torch==${TORCH_VERSION}" "torchvision==${TORCHVISION_VERSION}" \
        --extra-index-url https://download.pytorch.org/whl/cu118 || \
    pip install --no-cache-dir \
        "torch==${TORCH_VERSION}" "torchvision==${TORCHVISION_VERSION}" \
        --extra-index-url https://download.pytorch.org/whl/cu118; \
    # 安装其他依赖
    pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple \
        --trusted-host mirrors.aliyun.com -r /app/requirements.txt || \
    pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY analyzer /app/analyzer
COPY detector /app/detector
COPY static /app/static
COPY data /app/data

EXPOSE 5005

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5005", "--log-level", "debug", "--timeout-keep-alive", "300"]
