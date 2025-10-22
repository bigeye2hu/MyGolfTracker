# GolfTracker 服务自检可观测化设置

## 概述

本次更新为 GolfTracker 服务添加了完整的健康检查和监控功能，确保容器启动后能够被正确探活和监控。

## 新增功能

### 1. 健康检查端点 `/healthz`

- **用途**: Kubernetes 健康检查探活
- **响应格式**:
```json
{
  "status": "ok|degraded",
  "cuda": true|false,
  "model_loaded": true|false,
  "timestamp": 1234567890.123
}
```

- **状态说明**:
  - `ok`: 服务完全正常，模型已加载
  - `degraded`: 服务运行但模型未加载
  - `cuda`: CUDA GPU 可用性
  - `model_loaded`: 模型是否成功加载

### 2. Prometheus 监控端点 `/metrics`

- **用途**: Prometheus 指标收集
- **包含指标**:
  - HTTP 请求总数 (`http_requests_total`)
  - HTTP 请求持续时间 (`http_request_duration_seconds`)
  - 其他 FastAPI 应用指标

### 3. 模型预热功能

- **启动时预热**: 容器启动时自动加载和预热模型
- **GPU 优化**: 自动检测 CUDA 可用性并优化设备配置
- **半精度推理**: 在 GPU 上启用半精度以提升性能
- **资源清理**: 服务关闭时自动清理 GPU 内存

### 4. 应用生命周期管理

- **启动阶段**: 模型加载、预热、设备配置
- **运行阶段**: 健康检查、指标收集
- **关闭阶段**: 资源清理、内存释放

## 技术实现

### 核心文件修改

1. **`app/main.py`**:
   - 添加 `lifespan` 上下文管理器
   - 实现 `/healthz` 端点
   - 集成 Prometheus 监控
   - 模型预热逻辑

2. **`requirements.txt`**:
   - 添加 `prometheus-fastapi-instrumentator==7.0.0`

### 依赖项

```txt
prometheus-fastapi-instrumentator==7.0.0
```

## 测试方法

### 1. 快速测试 (Windows)

```powershell
.\test_health_quick.ps1
```

### 2. 详细测试 (Python)

```bash
python test_health_endpoints.py
```

### 3. 手动测试

```bash
# 健康检查
curl http://localhost:5005/healthz

# Prometheus 指标
curl http://localhost:5005/metrics

# 原有健康检查
curl http://localhost:5005/health
```

## 预期响应

### `/healthz` 端点响应示例

```json
{
  "status": "ok",
  "cuda": true,
  "model_loaded": true,
  "timestamp": 1703123456.789
}
```

### `/metrics` 端点响应示例

```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/healthz"} 1.0
http_requests_total{method="GET",endpoint="/metrics"} 1.0
```

## 部署说明

1. **重新构建容器**:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

2. **验证部署**:
   ```bash
   curl -s http://localhost:5005/healthz
   ```

3. **监控集成**:
   - 配置 Prometheus 抓取 `/metrics` 端点
   - 设置 Kubernetes 健康检查使用 `/healthz` 端点

## 故障排除

### 常见问题

1. **模型加载失败**:
   - 检查 `data/best.pt` 文件是否存在
   - 验证模型文件完整性

2. **CUDA 不可用**:
   - 检查 GPU 驱动安装
   - 验证 Docker GPU 支持配置

3. **Prometheus 端点不可用**:
   - 检查 `prometheus-fastapi-instrumentator` 安装
   - 查看服务启动日志

### 日志查看

```bash
docker logs golftracker-service
```

## 性能影响

- **启动时间**: 增加 5-10 秒（模型预热）
- **内存使用**: 增加约 100-200MB（模型常驻内存）
- **响应时间**: 无影响（预热后性能相同）

## 下一步优化建议

1. **指标自定义**: 添加业务相关指标（检测次数、处理时间等）
2. **告警配置**: 设置基于指标的告警规则
3. **日志结构化**: 使用结构化日志便于分析
4. **资源限制**: 配置容器资源限制和健康检查超时
