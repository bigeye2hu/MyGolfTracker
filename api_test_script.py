#!/usr/bin/env python3
"""
GolfTracker API测试脚本 - 供iOS端agent使用
"""

import requests
import json
import time
import os

class GolfTrackerAPITester:
    def __init__(self, base_url="http://localhost:5005"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 300  # 5分钟超时
    
    def test_health(self):
        """测试健康检查接口"""
        print("🔍 测试健康检查接口...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 健康检查通过: {result}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    def test_analysis(self, video_path, handed="right"):
        """测试视频分析接口"""
        print(f"🎥 测试视频分析接口: {video_path}")
        
        if not os.path.exists(video_path):
            print(f"❌ 视频文件不存在: {video_path}")
            return None
        
        try:
            url = f"{self.base_url}/analyze/analyze"
            
            with open(video_path, 'rb') as f:
                files = {'file': (os.path.basename(video_path), f, 'video/mp4')}
                data = {'handed': handed}
                
                print("📤 发送分析请求...")
                start_time = time.time()
                
                response = self.session.post(url, files=files, data=data)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 分析成功! 处理时间: {processing_time:.2f}秒")
                    
                    # 验证结果结构
                    if self.validate_result(result):
                        return result
                    else:
                        print("❌ 结果验证失败")
                        return None
                else:
                    print(f"❌ 分析失败: {response.status_code}")
                    print(f"错误信息: {response.text}")
                    return None
                    
        except requests.exceptions.Timeout:
            print("⏰ 请求超时")
            return None
        except Exception as e:
            print(f"❌ 分析异常: {e}")
            return None
    
    def validate_result(self, result):
        """验证分析结果格式"""
        print("🔍 验证结果格式...")
        
        # 检查根节点
        if "golftrainer_analysis" not in result:
            print("❌ 缺少golftrainer_analysis根节点")
            return False
        
        analysis = result["golftrainer_analysis"]
        
        # 检查必需字段
        required_fields = ["basic_info", "club_head_result", "pose_result", "trajectory_analysis"]
        for field in required_fields:
            if field not in analysis:
                print(f"❌ 缺少必需字段: {field}")
                return False
        
        # 检查轨迹数据
        club_result = analysis["club_head_result"]
        if "trajectory_points" not in club_result:
            print("❌ 缺少trajectory_points字段")
            return False
        
        trajectory = club_result["trajectory_points"]
        if not isinstance(trajectory, list) or len(trajectory) == 0:
            print("❌ trajectory_points格式错误")
            return False
        
        # 验证坐标范围
        valid_points = 0
        for point in trajectory:
            if isinstance(point, list) and len(point) == 2:
                x, y = point
                if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                    valid_points += 1
                elif x != 0.0 or y != 0.0:  # 允许(0,0)作为无效点
                    print(f"❌ 坐标超出范围: [{x}, {y}]")
                    return False
        
        print(f"✅ 格式验证通过")
        print(f"   - 总帧数: {len(trajectory)}")
        print(f"   - 有效点数: {valid_points}")
        print(f"   - 检测率: {valid_points/len(trajectory)*100:.1f}%")
        
        return True
    
    def get_sample_data(self, result):
        """获取示例数据用于iOS端测试"""
        if not result:
            return None
        
        analysis = result["golftrainer_analysis"]
        club_result = analysis["club_head_result"]
        trajectory = club_result["trajectory_points"]
        
        # 获取前10个轨迹点作为示例
        sample_points = trajectory[:10]
        
        # 获取视频信息
        basic_info = analysis["basic_info"]
        video_spec = basic_info["video_spec"]
        
        sample_data = {
            "video_info": {
                "width": video_spec["width"],
                "height": video_spec["height"],
                "fps": video_spec["fps"],
                "total_frames": video_spec["num_frames"]
            },
            "trajectory_sample": sample_points,
            "detection_stats": {
                "total_points": club_result["total_points_count"],
                "valid_points": club_result["valid_points_count"],
                "detection_rate": club_result["valid_points_count"] / club_result["total_points_count"] * 100
            },
            "coordinate_ranges": analysis["trajectory_analysis"]["x_range"],
            "y_ranges": analysis["trajectory_analysis"]["y_range"]
        }
        
        return sample_data
    
    def run_full_test(self, video_path=None):
        """运行完整测试"""
        print("🚀 开始GolfTracker API完整测试")
        print("=" * 50)
        
        # 1. 健康检查
        if not self.test_health():
            print("❌ 健康检查失败，停止测试")
            return False
        
        # 2. 视频分析测试
        if video_path:
            result = self.test_analysis(video_path)
            if result:
                # 3. 获取示例数据
                sample_data = self.get_sample_data(result)
                if sample_data:
                    print("\n📊 示例数据 (供iOS端使用):")
                    print(json.dumps(sample_data, indent=2, ensure_ascii=False))
                    
                    # 保存完整结果
                    output_file = "api_test_result.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    print(f"\n💾 完整结果已保存到: {output_file}")
                    
                    return True
        
        print("\n❌ 测试失败")
        return False

def main():
    """主函数"""
    import sys
    
    # 默认测试视频路径
    default_video = "/Users/huxiaoran/Desktop/高尔夫测试视频/挥杆2.mp4"
    
    # 检查命令行参数
    video_path = sys.argv[1] if len(sys.argv) > 1 else default_video
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5005"
    
    print(f"🎯 测试配置:")
    print(f"   服务器: {base_url}")
    print(f"   视频文件: {video_path}")
    print()
    
    # 创建测试器并运行测试
    tester = GolfTrackerAPITester(base_url)
    success = tester.run_full_test(video_path)
    
    if success:
        print("\n🎉 所有测试通过！API可以正常使用。")
        exit(0)
    else:
        print("\n💥 测试失败！请检查服务器状态。")
        exit(1)

if __name__ == "__main__":
    main()
