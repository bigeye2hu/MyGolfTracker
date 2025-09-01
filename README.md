## GolfTracker Service (Docker + FastAPI)

### 运行方式（Docker）

1. 准备模型文件（主机路径）：
   - 将训练好的 YOLOv8 模型放在主机的 `/data/ClubDetection_1000P_50R.pt`

2. 构建镜像：
```
docker build -t golftracker-service:latest .
```

3. 通过 docker-compose 启动（推荐，自动挂载 /data）：
```
docker compose up -d
```

4. 健康检查：
```
curl http://127.0.0.1:5005/health
```

5. 分析接口（示例）：
```
curl -X POST "http://127.0.0.1:5005/analyze" \
  -F "file=@/absolute/path/to/sample.mp4" \
  -F "handed=right"
```

### 环境变量（可选）
- `MODEL_PATH`：模型路径（默认 `/data/ClubDetection_1000P_50R.pt`）
- `SERVICE_PORT`：服务端口（默认 `5005`）

### 注意
- 当前 `/analyze` 为占位实现，返回兼容 iOS 的关键字段（pose_result.handed, poses_count）。
- 下一步将集成 YOLOv8 并产出真实杆头轨迹与相位。


