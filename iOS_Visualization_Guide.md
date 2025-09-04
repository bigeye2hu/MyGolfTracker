# GolfTracker iOS端可视化集成指南

## 🎯 功能概述

GolfTracker现在支持为iOS端提供可视化URL，让iOS端agent可以在浏览器中打开查看分析结果，包括：
- 📊 杆头轨迹可视化
- 🎬 逐帧播放控制
- 📄 完整JSON数据展示
- 💾 JSON文件下载功能

## 🔗 API设计说明

### 1. 分析接口增强

**端点**: `POST /analyze/analyze`

**响应格式**:
```json
{
  "golftrainer_analysis": {
    // ... 原有分析数据
  },
  "visualization_url": "/analyze/visualize/43a8d298-ddc7-4b1b-a1f2-4dd083976cb1"
}
```

**关键变化**:
- ✅ 在原有响应基础上添加了 `visualization_url` 字段
- ✅ 每个分析结果都有唯一的可视化URL
- ✅ URL格式: `/analyze/visualize/{result_id}`

### 2. 可视化页面端点

**端点**: `GET /analyze/visualize/{result_id}`

**功能**:
- 🎯 杆头轨迹Canvas可视化
- ⏯️ 逐帧播放控制（播放/暂停/上一帧/下一帧）
- 📊 实时显示当前帧的杆头位置坐标
- 📈 统计信息展示（检测率、总距离等）
- 📄 完整JSON数据展示
- 💾 JSON文件下载功能

## 📱 iOS端集成方案

### 方案1: 直接打开浏览器

```swift
// 在分析完成后获取可视化URL
func handleAnalysisResult(_ result: GolfTrackerResponse) {
    if let visualizationURL = result.visualizationUrl {
        // 构建完整URL
        let fullURL = "http://localhost:5005\(visualizationURL)"
        
        // 在Safari中打开
        if let url = URL(string: fullURL) {
            UIApplication.shared.open(url)
        }
    }
}
```

### 方案2: 内嵌WebView

```swift
import WebKit

class VisualizationViewController: UIViewController {
    @IBOutlet weak var webView: WKWebView!
    
    func loadVisualization(resultId: String) {
        let urlString = "http://localhost:5005/analyze/visualize/\(resultId)"
        if let url = URL(string: urlString) {
            let request = URLRequest(url: url)
            webView.load(request)
        }
    }
}
```

### 方案3: 获取URL供用户选择

```swift
func showVisualizationOptions(_ result: GolfTrackerResponse) {
    guard let visualizationURL = result.visualizationUrl else { return }
    
    let fullURL = "http://localhost:5005\(visualizationURL)"
    
    let alert = UIAlertController(
        title: "查看分析结果",
        message: "选择查看方式",
        preferredStyle: .actionSheet
    )
    
    alert.addAction(UIAlertAction(title: "在Safari中打开", style: .default) { _ in
        if let url = URL(string: fullURL) {
            UIApplication.shared.open(url)
        }
    })
    
    alert.addAction(UIAlertAction(title: "复制链接", style: .default) { _ in
        UIPasteboard.general.string = fullURL
    })
    
    alert.addAction(UIAlertAction(title: "取消", style: .cancel))
    
    present(alert, animated: true)
}
```

## 🔧 数据模型更新

### Swift数据模型

```swift
struct GolfTrackerResponse: Codable {
    let golftrainerAnalysis: GolfTrainerAnalysis
    let visualizationUrl: String?  // 新增字段
    
    enum CodingKeys: String, CodingKey {
        case golftrainerAnalysis = "golftrainer_analysis"
        case visualizationUrl = "visualization_url"
    }
}
```

### 使用示例

```swift
func analyzeVideo(videoURL: URL) async throws -> GolfTrackerResponse {
    let result = try await api.analyzeVideo(videoURL: videoURL)
    
    // 检查是否有可视化URL
    if let vizURL = result.visualizationUrl {
        print("可视化URL: http://localhost:5005\(vizURL)")
        
        // 可以选择立即打开或保存供后续使用
        DispatchQueue.main.async {
            self.showVisualizationButton(url: vizURL)
        }
    }
    
    return result
}
```

## 🎨 可视化页面功能

### 1. 轨迹可视化
- **Canvas绘制**: 动态尺寸画布，保持视频宽高比
  - 横屏视频：最大800×600，按比例缩放
  - 竖屏视频：最大800×600，按比例缩放
- **网格背景**: 10x10网格便于坐标参考
- **轨迹线条**: 
  - 灰色线条：完整轨迹
  - 蓝色线条：已播放部分
  - 红色圆点：当前帧位置

### 2. 播放控制
- **逐帧播放**: 100ms间隔自动播放
- **手动控制**: 上一帧/下一帧按钮
- **播放/暂停**: 切换播放状态
- **实时信息**: 显示当前帧号和坐标

### 3. 数据展示
- **视频信息**: 文件名、分辨率、帧率、总帧数
- **统计卡片**: 轨迹点数、有效检测、检测率、总距离
- **JSON数据**: 完整分析结果，支持下载

## 🔍 调试和纠错

### 1. 轨迹问题排查
- **坐标范围**: 检查是否在[0.0, 1.0]范围内
- **连续性**: 观察轨迹是否平滑连续
- **异常点**: 识别(0,0)无效点位置
- **检测率**: 查看有效检测百分比

### 2. 常见问题
- **轨迹跳跃**: 可能是检测失败或快速移动
- **坐标异常**: 检查归一化计算是否正确
- **检测率低**: 视频质量或光照条件问题
- **显示画面奇怪**: 可能是视频尺寸问题
  - iOS端通常录制竖屏视频（如720×1280, 432×768）
  - 可视化页面会自动调整Canvas尺寸保持宽高比
  - 竖屏视频会显示为较窄的Canvas（如337×600）

### 3. 调试工具
- **逐帧检查**: 使用播放控制逐帧查看
- **坐标显示**: 实时显示当前帧坐标
- **JSON下载**: 获取完整数据进行深度分析

## 📋 iOS端集成清单

### ✅ 必需功能
- [ ] 解析 `visualization_url` 字段
- [ ] 构建完整URL（包含服务器地址）
- [ ] 提供打开可视化页面的方式
- [ ] 处理URL打开失败的情况

### 🔄 可选功能
- [ ] 内嵌WebView显示
- [ ] 可视化URL分享功能
- [ ] 结果历史记录管理
- [ ] 离线结果缓存

### 🛠️ 技术实现
- [ ] 更新数据模型添加 `visualizationUrl` 字段
- [ ] 实现URL构建和验证逻辑
- [ ] 添加用户界面元素（按钮、菜单等）
- [ ] 处理网络错误和超时

## 🚀 使用流程

### 1. iOS端调用分析API
```swift
let result = try await golfTrackerAPI.analyzeVideo(videoURL: videoURL)
```

### 2. 检查可视化URL
```swift
if let vizURL = result.visualizationUrl {
    // 有可视化URL，可以展示给用户
    showVisualizationOption(url: vizURL)
}
```

### 3. 用户选择查看方式
- **Safari打开**: 在系统浏览器中查看
- **内嵌显示**: 在应用内WebView中显示
- **复制链接**: 分享给其他人查看

### 4. 调试和纠错
- 在浏览器中逐帧检查轨迹
- 下载JSON数据进行深度分析
- 对比不同视频的分析结果

## 📞 技术支持

### 服务器地址配置
```swift
// 开发环境
let baseURL = "http://localhost:5005"

// 生产环境
let baseURL = "https://your-production-server.com"
```

### 错误处理
```swift
func handleVisualizationError(_ error: Error) {
    switch error {
    case GolfTrackerError.visualizationNotFound:
        // 可视化结果未找到或已过期
        showAlert("分析结果已过期，请重新分析")
    case GolfTrackerError.networkError:
        // 网络连接问题
        showAlert("网络连接失败，请检查网络设置")
    default:
        showAlert("打开可视化页面失败")
    }
}
```

---

**版本**: v1.6  
**更新日期**: 2024年12月19日  
**兼容性**: iOS 12.0+  
**状态**: 生产就绪 ✅
