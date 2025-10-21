# GolfTracker API 接口文档

## 服务器信息
- **本地服务器**: http://localhost:5005
- **远端服务器**: http://106.15.103.1:5005
- **API版本**: v0.1.0

## 基础接口

### 1. 健康检查
```
GET /health
```
**响应**:
```json
{
  "status": "ok"
}
```

## 视频分析接口

### 1. 快速分析（同步）
```
POST /analyze/analyze
```
**参数**:
- `file`: 视频文件 (multipart/form-data)
- `handed`: 持杆手型 ("right" 或 "left", 默认 "right")

**响应**:
```json
{
  "golftrainer_analysis": {
    "basic_info": {
      "version": 1.0,
      "num_frames": 150,
      "video_spec": {
        "height": 720,
        "width": 1280,
        "num_frames": 150,
        "fps": 30,
        "scale": 100,
        "rotate": ""
      }
    },
    "mp_result": {
      "landmarks": ["nose", "left_eye", ...],
      "landmarks_count": 33
    },
    "pose_result": {
      "poses": ["Address", "Backswing", ...],
      "handed": "RightHanded",
      "poses_count": 150
    },
    "club_head_result": {
      "trajectory_points": [[0.5, 0.3], [0.52, 0.28], ...],
      "valid_points_count": 120,
      "total_points_count": 150
    },
    "trajectory_analysis": {
      "x_range": {"min": 0.1, "max": 0.9},
      "y_range": {"min": 0.2, "max": 0.8},
      "total_distance": 2.5,
      "average_movement_per_frame": 0.016
    },
    "data_frames": {
      "mp_data_frame": {
        "shape": [150, 132],
        "columns_count": 132,
        "sample_data": [0.5, 0.3, 0.8, 1.0, ...]
      },
      "norm_data_frame": {
        "shape": [150, 66],
        "columns_count": 66,
        "sample_data": [0.5, 0.3, 0.4, 0.2, ...]
      }
    },
    "sample_trajectory": {
      "first_20_points": [[0.5, 0.3], [0.52, 0.28], ...]
    }
  },
  "visualization_url": "/analyze/visualize/{result_id}"
}
```

### 2. 高级分析（异步）
```
POST /analyze/video
```
**参数**:
- `video`: 视频文件 (multipart/form-data)
- `resolution`: 处理分辨率 ("480", "640", "720", 默认 "480")
- `confidence`: 检测置信度 ("0.01" 到 "1.0", 默认 "0.01")
- `iou`: IoU阈值 ("0.1" 到 "1.0", 默认 "0.7")
- `max_det`: 最大检测数 ("1" 到 "100", 默认 "10")
- `optimization_strategy`: 优化策略 ("auto_fill", "savitzky_golay", "kalman", 默认 "auto_fill")

**响应**:
```json
{
  "job_id": "uuid-string",
  "status": "queued",
  "compatibility": {
    "compatible": true,
    "video_info": {
      "width": 1280,
      "height": 720,
      "fps": 30,
      "frame_count": 150,
      "codec": "h264"
    }
  }
}
```

### 3. 查询分析状态
```
GET /analyze/video/status?job_id={job_id}
```
**响应**:
```json
{
  "job_id": "uuid-string",
  "status": "done", // "queued", "processing", "done", "error"
  "progress": 100,
  "result": {
    // 完整的分析结果，格式同快速分析
  }
}
```

### 4. 获取可视化页面
```
GET /analyze/visualize/{result_id}
```
**响应**: HTML页面，包含轨迹可视化

## 视频转换接口

### 1. 转换视频格式
```
POST /convert/video
```
**参数**:
- `video`: 视频文件 (multipart/form-data)
- `quality`: 转换质量 ("high", "medium", "low", 默认 "medium")

**响应**:
```json
{
  "job_id": "uuid-string",
  "status": "queued",
  "message": "视频转换任务已开始",
  "compatibility": {
    "compatible": false,
    "video_info": {
      "codec": "h265"
    }
  },
  "conversion_info": {
    "reason": "检测到不兼容的视频格式",
    "current_codec": "h265",
    "target_codec": "H.264",
    "estimated_time": "1-3分钟"
  }
}
```

### 2. 查询转换状态
```
GET /convert/status/{job_id}
```
**响应**:
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "progress": 100,
  "message": "视频转换完成（H.264格式）",
  "download_url": "/convert/download/{job_id}",
  "output_filename": "converted_abc123.mp4"
}
```

### 3. 下载转换后的视频
```
GET /convert/download/{job_id}
```
**响应**: 视频文件下载

## 策略管理接口

### 1. 获取所有策略
```
GET /analyze/strategies
```
**响应**:
```json
{
  "strategies": [
    {
      "name": "auto_fill",
      "display_name": "自动补齐算法",
      "description": "自动检测并补齐缺失的轨迹点",
      "category": "interpolation"
    }
  ]
}
```

### 2. 按类别获取策略
```
GET /analyze/strategies/{category}
```
**响应**:
```json
{
  "strategies": [...],
  "category": "interpolation"
}
```

## 信息查询接口

### 1. 获取支持的视频格式
```
GET /analyze/supported-formats
```
**响应**:
```json
{
  "title": "GolfTracker 支持的视频格式",
  "compatible_formats": {
    "H.264": {
      "description": "最广泛支持的编码格式",
      "file_extensions": [".mp4", ".mov"],
      "browser_support": "优秀",
      "recommended": true
    }
  },
  "incompatible_formats": {
    "H.265": {
      "description": "新一代编码格式，浏览器支持有限",
      "solution": "需要转换为H.264"
    }
  }
}
```

### 2. 获取转换指导
```
GET /analyze/conversion-guide
```
**响应**: 详细的转换指导信息

## iOS App 推荐调用流程

### 方案1: 快速分析（推荐用于简单场景）
```swift
// 1. 上传视频进行快速分析
let url = URL(string: "http://106.15.103.1:5005/analyze/analyze")!
var request = URLRequest(url: url)
request.httpMethod = "POST"

let boundary = "Boundary-\(UUID().uuidString)"
request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

// 构建multipart数据
let body = NSMutableData()
body.append("--\(boundary)\r\n".data(using: .utf8)!)
body.append("Content-Disposition: form-data; name=\"file\"; filename=\"video.mp4\"\r\n".data(using: .utf8)!)
body.append("Content-Type: video/mp4\r\n\r\n".data(using: .utf8)!)
body.append(videoData)
body.append("\r\n--\(boundary)\r\n".data(using: .utf8)!)
body.append("Content-Disposition: form-data; name=\"handed\"\r\n\r\n".data(using: .utf8)!)
body.append("right".data(using: .utf8)!)
body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

request.httpBody = body as Data

// 发送请求
URLSession.shared.dataTask(with: request) { data, response, error in
    // 处理响应
}.resume()
```

### 方案2: 高级分析（推荐用于需要更多控制）
```swift
// 1. 上传视频开始分析
let uploadURL = URL(string: "http://106.15.103.1:5005/analyze/video")!
// ... 构建请求（类似上面）

// 2. 轮询查询状态
func pollAnalysisStatus(jobId: String) {
    let statusURL = URL(string: "http://106.15.103.1:5005/analyze/video/status?job_id=\(jobId)")!
    
    URLSession.shared.dataTask(with: statusURL) { data, response, error in
        if let data = data,
           let status = try? JSONDecoder().decode(AnalysisStatus.self, from: data) {
            
            if status.status == "done" {
                // 分析完成，处理结果
                handleAnalysisResult(status.result)
            } else if status.status == "error" {
                // 处理错误
                handleError(status.error)
            } else {
                // 继续轮询
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                    self.pollAnalysisStatus(jobId: jobId)
                }
            }
        }
    }.resume()
}
```

### 方案3: 视频转换 + 分析
```swift
// 1. 先转换视频格式
let convertURL = URL(string: "http://106.15.103.1:5005/convert/video")!
// ... 上传视频进行转换

// 2. 轮询转换状态
func pollConversionStatus(jobId: String) {
    let statusURL = URL(string: "http://106.15.103.1:5005/convert/status/\(jobId)")!
    
    URLSession.shared.dataTask(with: statusURL) { data, response, error in
        if let data = data,
           let status = try? JSONDecoder().decode(ConversionStatus.self, from: data) {
            
            if status.status == "completed" {
                // 转换完成，下载转换后的视频
                downloadConvertedVideo(downloadURL: status.download_url!)
            } else {
                // 继续轮询
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                    self.pollConversionStatus(jobId: jobId)
                }
            }
        }
    }.resume()
}

// 3. 下载转换后的视频并进行分析
func downloadAndAnalyze(downloadURL: String) {
    URLSession.shared.dataTask(with: URL(string: downloadURL)!) { data, response, error in
        // 下载完成后，使用转换后的视频进行分析
        // 调用方案1或方案2的分析接口
    }.resume()
}
```

## 数据模型

### 分析结果结构
```swift
struct GolfAnalysisResult: Codable {
    let golftrainerAnalysis: GolfTrainerAnalysis
    let visualizationUrl: String
    
    enum CodingKeys: String, CodingKey {
        case golftrainerAnalysis = "golftrainer_analysis"
        case visualizationUrl = "visualization_url"
    }
}

struct GolfTrainerAnalysis: Codable {
    let basicInfo: BasicInfo
    let mpResult: MPResult
    let poseResult: PoseResult
    let clubHeadResult: ClubHeadResult
    let trajectoryAnalysis: TrajectoryAnalysis
    let dataFrames: DataFrames
    let sampleTrajectory: SampleTrajectory
    
    enum CodingKeys: String, CodingKey {
        case basicInfo = "basic_info"
        case mpResult = "mp_result"
        case poseResult = "pose_result"
        case clubHeadResult = "club_head_result"
        case trajectoryAnalysis = "trajectory_analysis"
        case dataFrames = "data_frames"
        case sampleTrajectory = "sample_trajectory"
    }
}

struct ClubHeadResult: Codable {
    let trajectoryPoints: [[Double]]
    let validPointsCount: Int
    let totalPointsCount: Int
    
    enum CodingKeys: String, CodingKey {
        case trajectoryPoints = "trajectory_points"
        case validPointsCount = "valid_points_count"
        case totalPointsCount = "total_points_count"
    }
}
```

## 坐标映射（网页同款算法，iOS可直接复用）

本文档复现前端 `static/js/video-player-module.js` 的绘制逻辑，iOS 端按此实现即可与网页显示位置一致。

### 数据选择规则（与网页一致）
- 当前帧索引：`currentFrame = floor(currentTime * fps)`，其中 `fps = result.video_info.fps`（缺省则用 30）
- 优先在 `right_frame_detections` 查找该帧；若无，则在 `frame_detections` 查找。

示例（伪代码）：
```js
const fps = analysis.video_info?.fps || 30;
const currentFrame = Math.floor(video.currentTime * fps);
const detection = analysis.right_frame_detections?.find(d => d.frame === currentFrame)
               || analysis.frame_detections?.find(d => d.frame === currentFrame);
```

### 归一化坐标与像素坐标
- 服务端每帧同时返回像素坐标 `x, y`（基于原视频像素）与归一化坐标 `norm_x, norm_y`（0~1）。
- 网页实际使用的是像素坐标 `x, y`。若只有归一化坐标，先还原：
  - `x_px = norm_x * video_info.width`
  - `y_px = norm_y * video_info.height`

### 原视频像素坐标 → 展示层坐标（关键缩放逻辑）
网页在 `<video>` 上方叠加同尺寸 `<canvas>`，将原视频像素按线性缩放映射到画布坐标：
- 取 `<video>` 的渲染尺寸（网页用 `getBoundingClientRect()`）：
  - `canvasWidth`, `canvasHeight`
- 计算缩放系数：
  - `scaleX = canvasWidth / video_info.width`
  - `scaleY = canvasHeight / video_info.height`
- 最终显示坐标：
  - `x_draw = x_px * scaleX`
  - `y_draw = y_px * scaleY`

对应前端源码片段（摘自 `video-player-module.js`）：
```js
const videoWidth = analysis.video_info.width;
const videoHeight = analysis.video_info.height;
const canvasWidth = overlayCanvas.width;
const canvasHeight = overlayCanvas.height;
const scaleX = canvasWidth / videoWidth;
const scaleY = canvasHeight / videoHeight;
const x = detection.x * scaleX;
const y = detection.y * scaleY;
```

### iOS 参考实现（Swift 伪代码）
```swift
struct VideoInfo {
    let width: CGFloat
    let height: CGFloat
    let fps: Double
}

struct Detection {
    let frame: Int
    let x: CGFloat?     // 像素坐标，优先使用
    let y: CGFloat?
    let normX: CGFloat? // 备用：仅有归一化时使用
    let normY: CGFloat?
    let detected: Bool
}

func currentFrame(currentTime: Double, fps: Double?) -> Int {
    let f = fps ?? 30.0
    return Int(floor(currentTime * f))
}

func mapToDisplayPoint(d: Detection,
                       video: VideoInfo,
                       displaySize: CGSize) -> CGPoint? {
    guard d.detected else { return nil }

    // 1) 准备原视频像素坐标
    let xPx: CGFloat
    let yPx: CGFloat
    if let x = d.x, let y = d.y {
        xPx = x; yPx = y
    } else if let nx = d.normX, let ny = d.normY {
        xPx = nx * video.width
        yPx = ny * video.height
    } else {
        return nil
    }

    // 2) 线性缩放到展示层（与网页一致）
    let scaleX = displaySize.width / video.width
    let scaleY = displaySize.height / video.height
    return CGPoint(x: xPx * scaleX, y: yPx * scaleY)
}
```

### 关于旋转与内容模式
- 网页不做额外旋转/信封(letterbox)处理，直接用 `video_info.width/height` 与渲染尺寸做线性缩放。
- iOS 播放控件若使用等比显示（建议），则上式即可对齐网页显示。
- 若在 iOS 端启用了额外旋转或不同内容模式（如 aspectFill），请先将坐标转换到最终渲染坐标系后再绘制。


## 错误处理

### 常见错误码
- `400`: 请求参数错误
- `404`: 资源未找到
- `500`: 服务器内部错误
- `503`: 服务暂时不可用

### 错误响应格式
```json
{
  "detail": "错误描述信息"
}
```

## 注意事项

1. **文件大小限制**: 建议视频文件不超过100MB
2. **处理时间**: 快速分析通常需要10-30秒，高级分析可能需要1-3分钟
3. **并发限制**: 服务器限制同时处理的任务数量
4. **视频格式**: 推荐使用H.264编码的MP4文件
5. **网络超时**: 建议设置适当的网络超时时间（30-60秒）
6. **结果存储**: 分析结果会临时存储，建议及时保存重要数据

## 测试接口

### 服务器测试页面
```
GET /analyze/server-test
```
返回完整的测试页面，包含上传和分析功能

### 转换服务测试页面
```
GET /convert/test-page
```
返回视频转换测试页面
