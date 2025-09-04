//
//  GolfTracker iOS集成示例
//  Created for iOS端agent测试
//

import Foundation
import UIKit

// MARK: - 数据模型
struct GolfTrackerResponse: Codable {
    let golftrainerAnalysis: GolfTrainerAnalysis
    
    enum CodingKeys: String, CodingKey {
        case golftrainerAnalysis = "golftrainer_analysis"
    }
}

struct GolfTrainerAnalysis: Codable {
    let basicInfo: BasicInfo
    let clubHeadResult: ClubHeadResult
    let poseResult: PoseResult
    let trajectoryAnalysis: TrajectoryAnalysis
    
    enum CodingKeys: String, CodingKey {
        case basicInfo = "basic_info"
        case clubHeadResult = "club_head_result"
        case poseResult = "pose_result"
        case trajectoryAnalysis = "trajectory_analysis"
    }
}

struct BasicInfo: Codable {
    let version: Double
    let numFrames: Int
    let videoSpec: VideoSpec
    
    enum CodingKeys: String, CodingKey {
        case version
        case numFrames = "num_frames"
        case videoSpec = "video_spec"
    }
}

struct VideoSpec: Codable {
    let height: Int
    let width: Int
    let numFrames: Int
    let fps: Int
    let scale: Int
    let rotate: String
    
    enum CodingKeys: String, CodingKey {
        case height, width, fps, scale, rotate
        case numFrames = "num_frames"
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

struct PoseResult: Codable {
    let poses: [String]
    let handed: String
    let posesCount: Int
    
    enum CodingKeys: String, CodingKey {
        case poses, handed
        case posesCount = "poses_count"
    }
}

struct TrajectoryAnalysis: Codable {
    let xRange: CoordinateRange
    let yRange: CoordinateRange
    let totalDistance: Double
    let averageMovementPerFrame: Double
    
    enum CodingKeys: String, CodingKey {
        case xRange = "x_range"
        case yRange = "y_range"
        case totalDistance = "total_distance"
        case averageMovementPerFrame = "average_movement_per_frame"
    }
}

struct CoordinateRange: Codable {
    let min: Double
    let max: Double
}

// MARK: - 错误类型
enum GolfTrackerError: Error {
    case networkError(Error)
    case serverError(Int, String)
    case invalidData
    case timeout
    case fileNotFound
}

// MARK: - API客户端
class GolfTrackerAPI {
    private let baseURL: String
    private let session: URLSession
    
    init(baseURL: String = "http://localhost:5005") {
        self.baseURL = baseURL
        
        // 配置URLSession
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 300  // 5分钟
        config.timeoutIntervalForResource = 600 // 10分钟
        self.session = URLSession(configuration: config)
    }
    
    // MARK: - 健康检查
    func checkHealth() async throws -> Bool {
        let url = URL(string: "\(baseURL)/health")!
        
        do {
            let (data, response) = try await session.data(from: url)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw GolfTrackerError.invalidData
            }
            
            if httpResponse.statusCode == 200 {
                let result = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                print("健康检查通过: \(result ?? [:])")
                return true
            } else {
                throw GolfTrackerError.serverError(httpResponse.statusCode, "健康检查失败")
            }
        } catch {
            throw GolfTrackerError.networkError(error)
        }
    }
    
    // MARK: - 视频分析
    func analyzeVideo(videoURL: URL, handed: String = "right") async throws -> GolfTrackerResponse {
        // 检查文件是否存在
        guard FileManager.default.fileExists(atPath: videoURL.path) else {
            throw GolfTrackerError.fileNotFound
        }
        
        let url = URL(string: "\(baseURL)/analyze/analyze")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        // 创建multipart/form-data请求体
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        let httpBody = try createMultipartBody(
            boundary: boundary,
            videoURL: videoURL,
            handed: handed
        )
        request.httpBody = httpBody
        
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw GolfTrackerError.invalidData
            }
            
            if httpResponse.statusCode == 200 {
                let result = try JSONDecoder().decode(GolfTrackerResponse.self, from: data)
                return result
            } else {
                let errorMessage = String(data: data, encoding: .utf8) ?? "未知错误"
                throw GolfTrackerError.serverError(httpResponse.statusCode, errorMessage)
            }
        } catch {
            if error is GolfTrackerError {
                throw error
            } else {
                throw GolfTrackerError.networkError(error)
            }
        }
    }
    
    // MARK: - 辅助方法
    private func createMultipartBody(boundary: String, videoURL: URL, handed: String) throws -> Data {
        var body = Data()
        
        // 添加视频文件
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(videoURL.lastPathComponent)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: video/mp4\r\n\r\n".data(using: .utf8)!)
        
        let videoData = try Data(contentsOf: videoURL)
        body.append(videoData)
        body.append("\r\n".data(using: .utf8)!)
        
        // 添加handed参数
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"handed\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(handed)\r\n".data(using: .utf8)!)
        
        // 结束边界
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        return body
    }
}

// MARK: - 使用示例
class GolfTrackerViewController: UIViewController {
    private let api = GolfTrackerAPI()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
    }
    
    private func setupUI() {
        // 设置UI元素
        let analyzeButton = UIButton(type: .system)
        analyzeButton.setTitle("分析视频", for: .normal)
        analyzeButton.addTarget(self, action: #selector(analyzeButtonTapped), for: .touchUpInside)
        
        // 添加到视图...
    }
    
    @objc private func analyzeButtonTapped() {
        Task {
            await performAnalysis()
        }
    }
    
    private func performAnalysis() async {
        do {
            // 1. 健康检查
            let isHealthy = try await api.checkHealth()
            guard isHealthy else {
                await showError("服务器不健康")
                return
            }
            
            // 2. 选择视频文件
            guard let videoURL = await selectVideoFile() else {
                await showError("未选择视频文件")
                return
            }
            
            // 3. 执行分析
            await showLoading(true)
            let result = try await api.analyzeVideo(videoURL: videoURL, handed: "right")
            await showLoading(false)
            
            // 4. 处理结果
            await handleAnalysisResult(result)
            
        } catch {
            await showLoading(false)
            await handleError(error)
        }
    }
    
    private func handleAnalysisResult(_ result: GolfTrackerResponse) async {
        let analysis = result.golftrainerAnalysis
        
        // 显示基本信息
        print("分析完成!")
        print("视频规格: \(analysis.basicInfo.videoSpec.width)x\(analysis.basicInfo.videoSpec.height)")
        print("总帧数: \(analysis.basicInfo.numFrames)")
        print("检测率: \(analysis.clubHeadResult.validPointsCount)/\(analysis.clubHeadResult.totalPointsCount)")
        
        // 显示轨迹数据
        let trajectory = analysis.clubHeadResult.trajectoryPoints
        print("轨迹点数: \(trajectory.count)")
        
        // 显示前5个点作为示例
        let samplePoints = Array(trajectory.prefix(5))
        print("前5个轨迹点: \(samplePoints)")
        
        // 显示坐标范围
        print("X范围: \(analysis.trajectoryAnalysis.xRange.min) - \(analysis.trajectoryAnalysis.xRange.max)")
        print("Y范围: \(analysis.trajectoryAnalysis.yRange.min) - \(analysis.trajectoryAnalysis.yRange.max)")
        
        // 在主线程更新UI
        await MainActor.run {
            // 更新UI显示结果
            showAnalysisResult(analysis)
        }
    }
    
    private func handleError(_ error: Error) async {
        let message: String
        
        switch error {
        case GolfTrackerError.networkError(let networkError):
            message = "网络错误: \(networkError.localizedDescription)"
        case GolfTrackerError.serverError(let code, let description):
            message = "服务器错误 (\(code)): \(description)"
        case GolfTrackerError.invalidData:
            message = "数据格式错误"
        case GolfTrackerError.timeout:
            message = "请求超时"
        case GolfTrackerError.fileNotFound:
            message = "视频文件未找到"
        default:
            message = "未知错误: \(error.localizedDescription)"
        }
        
        await showError(message)
    }
    
    // MARK: - UI辅助方法
    private func selectVideoFile() async -> URL? {
        // 实现视频文件选择逻辑
        return nil
    }
    
    private func showLoading(_ show: Bool) async {
        await MainActor.run {
            // 显示/隐藏加载指示器
        }
    }
    
    private func showError(_ message: String) async {
        await MainActor.run {
            // 显示错误消息
            print("错误: \(message)")
        }
    }
    
    private func showAnalysisResult(_ analysis: GolfTrainerAnalysis) {
        // 显示分析结果
        print("分析结果已显示")
    }
}

// MARK: - 测试用例
class GolfTrackerTests {
    private let api = GolfTrackerAPI()
    
    func testHealthCheck() async {
        do {
            let isHealthy = try await api.checkHealth()
            assert(isHealthy, "健康检查应该通过")
            print("✅ 健康检查测试通过")
        } catch {
            print("❌ 健康检查测试失败: \(error)")
        }
    }
    
    func testVideoAnalysis() async {
        // 使用测试视频文件
        guard let videoURL = Bundle.main.url(forResource: "test_video", withExtension: "mp4") else {
            print("❌ 测试视频文件未找到")
            return
        }
        
        do {
            let result = try await api.analyzeVideo(videoURL: videoURL)
            
            // 验证结果
            assert(!result.golftrainerAnalysis.clubHeadResult.trajectoryPoints.isEmpty, "轨迹点不应为空")
            assert(result.golftrainerAnalysis.basicInfo.numFrames > 0, "帧数应大于0")
            
            print("✅ 视频分析测试通过")
            print("   轨迹点数: \(result.golftrainerAnalysis.clubHeadResult.trajectoryPoints.count)")
            print("   检测率: \(result.golftrainerAnalysis.clubHeadResult.validPointsCount)/\(result.golftrainerAnalysis.clubHeadResult.totalPointsCount)")
            
        } catch {
            print("❌ 视频分析测试失败: \(error)")
        }
    }
    
    func runAllTests() async {
        print("🧪 开始运行所有测试...")
        
        await testHealthCheck()
        await testVideoAnalysis()
        
        print("🏁 测试完成")
    }
}
