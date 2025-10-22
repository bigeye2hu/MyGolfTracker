# 项目规则 - 构建与启动规范

## 构建与启动（团队约定）

- 快速构建（默认优先）
  - 命令：`./quick_build.sh`
  - 适用：仅代码改动，依赖未变

- 强制重建（依赖或镜像层变更）
  - 命令：`./quick_build.sh --force`
  - 适用：修改了 `requirements.txt`、`Dockerfile*`、CUDA/PyTorch 版本

- 开发模式（本地开发调试）
  - 命令：`./dev_start.sh`
  - 特性：代码目录挂载，改代码后重启即生效（`docker-compose -f docker-compose.dev.yml restart`）

- RTX 5090 优化版本（生产环境）
  - 命令：`docker-compose -f docker-compose.gpu.yml up -d`
  - 特性：使用 CUDA 12.8 + PyTorch cu128，支持 RTX 5090

## 构建与缓存策略

- 生产环境使用 `docker-compose.gpu.yml`（RTX 5090 优化）
- 开发环境使用 `docker-compose.dev.yml`（代码挂载）
- `.dockerignore` 已优化构建上下文，不随意添加大文件
- 避免不必要的 `docker system prune`，除非磁盘压力或缓存异常

## 运行环境约定

- 平台：Windows 主机 + WSL Ubuntu + Docker（所有命令在 WSL 内执行）
- 端口：`http://localhost:5005`

## 健康检查与监控

- 健康检查：`GET /healthz`
- Prometheus 指标：`GET /metrics`
- 可视化监控：`GET /monitoring/dashboard`

## 沟通与确认

- 存在多种构建/启动选项时，默认采用“快速构建”；你若指定其他方式则按指定执行
- 每次变更先由使用者验证，再决定是否入库（不主动 git 提交）
