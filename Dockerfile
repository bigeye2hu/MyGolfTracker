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

# 先拷贝本地 wheels（若存在，用于离线安装大包如 torch）
COPY wheels/ /wheels/ 2>/dev/null || mkdir -p /wheels

ARG TORCH_VERSION=2.8.0
ARG TORCHVISION_VERSION=0.19.0
COPY requirements.txt /app/requirements.txt
# 使用国内 PyPI 镜像加速，失败则回退官方
RUN set -ex; \
    # 强制先用本地 wheel 安装 torch/torchvision，不成功则直接失败，避免后续又从网络拉取
    pip install --no-cache-dir --no-index --find-links /wheels \
        "torch==${TORCH_VERSION}" || (echo "Missing torch wheel in /wheels" && exit 1); \
    if ls /wheels/torchvision*.whl >/dev/null 2>&1; then \
        pip install --no-cache-dir --no-index --find-links /wheels \
            "torchvision==${TORCHVISION_VERSION}"; \
    fi; \
    # 过滤掉 torch/torchvision/torchaudio，避免重复安装
    grep -viE '^(torch|torchvision|torchaudio)([<>= ]|$)' /app/requirements.txt > /app/requirements-cpu.txt; \
    (pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple \
        --trusted-host mirrors.aliyun.com --find-links /wheels -r /app/requirements-cpu.txt \
     || pip install --no-cache-dir --find-links /wheels -r /app/requirements-cpu.txt)

COPY app /app/app
COPY analyzer /app/analyzer
COPY detector /app/detector
COPY static /app/static
COPY data /app/data

EXPOSE 5005

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5005", "--log-level", "debug", "--timeout-keep-alive", "300"]
