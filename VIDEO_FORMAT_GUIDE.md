# GolfTracker 视频格式支持指南

## 🎥 支持的视频格式

### ✅ 推荐格式
- **MP4 (H.264编码)**: 最佳兼容性，推荐使用
- **MOV (H.264编码)**: 良好兼容性

### ⚠️ 可能有问题
- **MOV (FMP4编码)**: 在某些浏览器中可能显示异常
- **AVI**: 兼容性一般

## 🔧 视频格式问题解决方案

### 问题描述
- `00001.mov` (FMP4编码) 显示很小或异常
- `挥杆2.mp4` (H.264编码) 显示正常

### 解决方案

#### 方案1: 转换视频格式 (推荐)
使用 FFmpeg 将 MOV 转换为 MP4:

```bash
# 安装 FFmpeg (如果未安装)
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg

# 转换 MOV 到 MP4
ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4

# 针对高尔夫视频的优化转换
ffmpeg -i input.mov -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k output.mp4
```

#### 方案2: 使用在线转换工具
- CloudConvert
- Online-Convert
- Convertio

#### 方案3: 使用视频编辑软件
- Final Cut Pro
- Adobe Premiere Pro
- DaVinci Resolve

## 📱 iOS端录制建议

### 推荐设置
- **格式**: MP4
- **编码**: H.264
- **分辨率**: 720p 或 1080p
- **帧率**: 30fps 或 60fps
- **比特率**: 中等质量

### iOS录制代码示例
```swift
// 设置视频录制格式
let settings = AVCaptureVideoSettings()
settings.videoCodecType = .h264
settings.videoScalingMode = .resizeAspectFill
```

## 🔍 视频格式检测

### 使用 FFprobe 检测
```bash
ffprobe -v quiet -print_format json -show_format -show_streams video.mov
```

### 使用 Python 检测
```python
import cv2

cap = cv2.VideoCapture('video.mov')
if cap.isOpened():
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    fourcc_str = ''.join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
    
    print(f"分辨率: {width} × {height}")
    print(f"帧率: {fps} FPS")
    print(f"编码格式: {fourcc_str}")
    cap.release()
```

## 🛠️ 技术细节

### 编码格式对比
| 格式 | 编码 | 浏览器兼容性 | 文件大小 | 质量 |
|------|------|-------------|----------|------|
| MP4 | H.264 | ✅ 优秀 | 中等 | 高 |
| MOV | H.264 | ✅ 良好 | 中等 | 高 |
| MOV | FMP4 | ⚠️ 一般 | 小 | 中等 |
| AVI | 多种 | ⚠️ 一般 | 大 | 高 |

### 浏览器支持
- **Chrome**: 支持 H.264, VP8, VP9
- **Safari**: 主要支持 H.264
- **Firefox**: 支持 H.264, VP8, VP9
- **Edge**: 支持 H.264, VP8, VP9

## 📋 故障排除

### 视频显示很小
1. 检查视频编码格式
2. 尝试转换为 H.264 MP4
3. 检查视频元数据

### 视频无法播放
1. 检查文件格式
2. 检查浏览器支持
3. 尝试不同浏览器

### 检测框位置不准确
1. 确保视频尺寸正确
2. 检查Canvas叠加设置
3. 验证坐标映射

## 🎯 最佳实践

1. **统一使用 MP4 (H.264)** 格式
2. **保持合理的视频质量** (不要过度压缩)
3. **测试多种浏览器** 兼容性
4. **提供格式转换工具** 给用户
5. **添加格式检测** 和提示功能

---

**版本**: v1.0  
**更新日期**: 2024年12月19日  
**状态**: 生产就绪 ✅
