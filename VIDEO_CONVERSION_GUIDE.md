# GolfTracker 视频格式转换完整指南

## 🎯 转换目标

将不兼容的视频格式（如FMP4编码的MOV/MP4文件）转换为H.264编码的MP4格式，以确保在GolfTracker中正常播放。

## 🛠️ 方法一：使用我们的转换工具（推荐）

### **安装和使用**

```bash
# 1. 确保已安装FFmpeg
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# 从 https://ffmpeg.org/download.html 下载

# 2. 使用我们的转换工具
python video_converter.py /path/to/your/video.mov

# 3. 批量转换
python video_converter.py /path/to/video/folder --batch

# 4. 高质量转换
python video_converter.py input.mov -q high -o output.mp4
```

### **转换选项**

| 参数 | 说明 | 示例 |
|------|------|------|
| `-q high` | 高质量转换（文件较大） | `python video_converter.py input.mov -q high` |
| `-q medium` | 中等质量转换（推荐） | `python video_converter.py input.mov -q medium` |
| `-q low` | 低质量转换（文件较小） | `python video_converter.py input.mov -q low` |
| `-o output.mp4` | 指定输出文件名 | `python video_converter.py input.mov -o converted.mp4` |
| `--batch` | 批量转换整个文件夹 | `python video_converter.py /videos --batch` |
| `--no-audio` | 不保留音频 | `python video_converter.py input.mov --no-audio` |

## 🌐 方法二：在线转换工具

### **推荐在线工具**

1. **CloudConvert** (https://cloudconvert.com/mov-to-mp4)
   - ✅ 支持多种格式
   - ✅ 高质量转换
   - ✅ 免费额度充足
   - ❌ 需要上传文件

2. **Convertio** (https://convertio.co/mov-mp4/)
   - ✅ 界面友好
   - ✅ 快速转换
   - ✅ 支持批量转换
   - ❌ 免费版有限制

3. **Online-Convert** (https://www.online-convert.com/)
   - ✅ 功能全面
   - ✅ 自定义设置
   - ❌ 广告较多

### **在线转换步骤**

1. **访问转换网站**
2. **上传视频文件**
3. **选择输出格式**：MP4
4. **设置编码格式**：H.264（如果可选）
5. **开始转换**
6. **下载转换后的文件**

## 💻 方法三：使用FFmpeg命令行

### **基本转换命令**

```bash
# 基本转换（推荐设置）
ffmpeg -i input.mov -c:v libx264 -preset medium -crf 23 -c:a aac output.mp4

# 高质量转换
ffmpeg -i input.mov -c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k output.mp4

# 快速转换（文件较大）
ffmpeg -i input.mov -c:v libx264 -preset fast -crf 28 -c:a aac output.mp4

# 网络优化（适合在线播放）
ffmpeg -i input.mov -c:v libx264 -preset medium -crf 23 -c:a aac -movflags +faststart output.mp4
```

### **参数说明**

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `-c:v libx264` | 视频编码器 | H.264 |
| `-preset` | 编码速度 | slow/medium/fast |
| `-crf` | 质量参数 | 18-28 (越小质量越好) |
| `-c:a aac` | 音频编码器 | AAC |
| `-b:a` | 音频比特率 | 128k-192k |
| `-movflags +faststart` | 网络优化 | 适合在线播放 |

## 📱 方法四：移动端转换

### **iOS应用**

1. **Video Converter** (App Store)
   - ✅ 支持多种格式
   - ✅ 简单易用
   - ❌ 付费应用

2. **Format Factory** (App Store)
   - ✅ 免费
   - ✅ 功能全面
   - ❌ 界面复杂

### **Android应用**

1. **Video Converter** (Google Play)
   - ✅ 免费
   - ✅ 支持H.264输出
   - ❌ 广告较多

2. **Media Converter** (Google Play)
   - ✅ 专业功能
   - ✅ 批量转换
   - ❌ 部分功能付费

## 🎬 方法五：视频编辑软件

### **专业软件**

1. **Adobe Premiere Pro**
   - 导出设置：H.264, MP4
   - 质量：高
   - 适合：专业用户

2. **Final Cut Pro** (Mac)
   - 导出设置：H.264, MP4
   - 质量：高
   - 适合：Mac用户

3. **DaVinci Resolve** (免费)
   - 导出设置：H.264, MP4
   - 质量：高
   - 适合：所有用户

### **简单软件**

1. **HandBrake** (免费)
   - ✅ 开源免费
   - ✅ 专业功能
   - ✅ 跨平台

2. **VLC Media Player**
   - 媒体 → 转换/保存
   - 选择H.264编码
   - 适合：简单转换

## 🔧 转换设置建议

### **GolfTracker优化设置**

```bash
# 针对GolfTracker优化的转换命令
ffmpeg -i input.mov \
  -c:v libx264 \
  -preset medium \
  -crf 23 \
  -c:a aac \
  -b:a 128k \
  -movflags +faststart \
  -vf "scale=720:1280" \
  output.mp4
```

### **质量对比**

| 设置 | 文件大小 | 质量 | 转换时间 | 推荐场景 |
|------|----------|------|----------|----------|
| `-crf 18` | 大 | 最高 | 长 | 存档/专业用途 |
| `-crf 23` | 中等 | 高 | 中等 | **推荐设置** |
| `-crf 28` | 小 | 中等 | 短 | 快速分享 |

## 📋 转换检查清单

### **转换前**
- [ ] 确认原视频文件完整
- [ ] 检查磁盘空间充足
- [ ] 选择合适的转换方法
- [ ] 备份原文件

### **转换中**
- [ ] 监控转换进度
- [ ] 确保网络稳定（在线转换）
- [ ] 不要关闭转换程序

### **转换后**
- [ ] 检查输出文件大小合理
- [ ] 播放测试转换后的视频
- [ ] 在GolfTracker中测试
- [ ] 确认兼容性

## 🚨 常见问题解决

### **转换失败**
1. **检查FFmpeg安装**：`ffmpeg -version`
2. **检查文件权限**：确保有读写权限
3. **检查磁盘空间**：确保有足够空间
4. **检查文件完整性**：原文件可能损坏

### **转换后无法播放**
1. **检查编码格式**：确认是H.264
2. **检查容器格式**：确认是MP4
3. **重新转换**：尝试不同参数
4. **使用其他工具**：尝试不同转换方法

### **文件过大**
1. **降低质量**：使用`-crf 28`
2. **降低分辨率**：使用`-vf "scale=480:854"`
3. **移除音频**：使用`-an`
4. **使用快速预设**：使用`-preset fast`

## 📞 技术支持

如果遇到转换问题，请提供以下信息：
1. 原视频文件信息（格式、大小、时长）
2. 使用的转换方法
3. 错误信息截图
4. 系统信息（操作系统、FFmpeg版本）

---

**版本**: v1.0  
**更新日期**: 2024年12月19日  
**状态**: 生产就绪 ✅
