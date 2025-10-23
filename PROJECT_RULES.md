# 项目规则 - 构建与启动规范

## 构建与启动（团队约定）

- 标准构建（推荐）
  - 命令：`docker-compose build --no-cache && docker-compose up -d`
  - 适用：完整构建，支持 RTX 5090

- 快速构建（使用缓存）
  - 命令：`docker-compose build && docker-compose up -d`
  - 适用：仅代码改动，依赖未变

- 开发模式（本地开发调试）
  - 命令：`docker-compose -f docker-compose.dev.yml up -d`
  - 特性：代码目录挂载，改代码后重启即生效

## 构建与缓存策略

- 生产环境使用 `docker-compose.yml`（统一配置）
- 开发环境使用 `docker-compose.dev.yml`（代码挂载）
- `.dockerignore` 已优化构建上下文，不随意添加大文件
- 避免不必要的 `docker system prune`，除非磁盘压力或缓存异常

## 运行环境约定

- 平台：Windows 主机 + WSL Ubuntu + Docker（所有命令在 WSL 内执行）
- 端口：`http://localhost:5005`
- GPU：RTX 5090 + CUDA 12.8 + PyTorch 2.9.0+cu128

## 健康检查与监控

- 健康检查：`GET /healthz`
- Prometheus 指标：`GET /metrics`
- 可视化监控：`GET /monitoring/dashboard`

## 沟通与确认

- 存在多种构建/启动选项时，默认采用"标准构建"；你若指定其他方式则按指定执行
- 每次变更先由使用者验证，再决定是否入库（不主动 git 提交）