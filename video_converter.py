#!/usr/bin/env python3
"""
GolfTracker 视频格式转换工具
将不兼容的视频格式转换为H.264编码的MP4格式
"""

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path
import argparse
import ffmpeg

class VideoConverter:
    def __init__(self):
        self.supported_input_formats = ['.mov', '.mp4', '.avi', '.mkv', '.wmv', '.flv', '.webm']
        self.output_format = '.mp4'
        self.target_codec = 'libx264'
        
    def check_ffmpeg(self):
        """检查FFmpeg是否可用"""
        try:
            # 尝试使用ffmpeg-python
            ffmpeg.probe('dummy')  # 这会触发ffmpeg检查
            print("✅ FFmpeg 可用")
            return True
        except Exception:
            try:
                # 回退到命令行检查
                result = subprocess.run(['ffmpeg', '-version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print("✅ FFmpeg 已安装")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        print("❌ FFmpeg 不可用")
        print("\n📥 安装 FFmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  CentOS/RHEL: sudo yum install ffmpeg")
        print("  Windows: 从 https://ffmpeg.org/download.html 下载")
        print("  或者安装ffmpeg-python: pip install ffmpeg-python")
        return False
    
    def get_video_info(self, video_path):
        """获取视频信息"""
        try:
            # 使用ffmpeg-python获取视频信息
            probe = ffmpeg.probe(video_path)
            
            # 查找视频流
            video_stream = None
            for stream in probe.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if video_stream:
                # 计算帧率
                fps_str = video_stream.get('r_frame_rate', '30/1')
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    fps = float(num) / float(den) if float(den) != 0 else 30.0
                else:
                    fps = float(fps_str)
                
                return {
                    'width': video_stream.get('width', 0),
                    'height': video_stream.get('height', 0),
                    'codec': video_stream.get('codec_name', 'unknown'),
                    'fps': fps,
                    'duration': float(probe.get('format', {}).get('duration', 0)),
                    'size': int(probe.get('format', {}).get('size', 0))
                }
        except Exception as e:
            print(f"⚠️ 无法获取视频信息: {e}")
        
        return None
    
    def is_compatible(self, video_path):
        """检查视频是否兼容"""
        info = self.get_video_info(video_path)
        if not info:
            return False, "无法获取视频信息"
        
        compatible_codecs = ['h264', 'avc1']
        is_compatible = info['codec'].lower() in compatible_codecs
        
        return is_compatible, info
    
    def convert_video(self, input_path, output_path=None, quality='medium', 
                     preserve_audio=True, optimize_for_web=True):
        """转换视频格式"""
        if not self.check_ffmpeg():
            return False
        
        if not os.path.exists(input_path):
            print(f"❌ 输入文件不存在: {input_path}")
            return False
        
        # 检查是否需要转换
        is_compatible, info = self.is_compatible(input_path)
        if is_compatible:
            print(f"✅ 视频已经是兼容格式 ({info['codec']})，无需转换")
            return True
        
        # 生成输出文件名
        if output_path is None:
            input_file = Path(input_path)
            output_path = input_file.parent / f"{input_file.stem}_converted{self.output_format}"
        
        print(f"🔄 转换视频: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
        print(f"   编码格式: {info['codec']} -> H.264")
        print(f"   分辨率: {info['width']} × {info['height']}")
        print(f"   时长: {info['duration']:.1f}秒")
        
        # 使用ffmpeg-python构建转换流
        try:
            print("⏳ 开始转换...")
            
            # 创建输入流
            input_stream = ffmpeg.input(input_path)
            
            # 视频编码设置
            quality_settings = {
                'high': {'preset': 'slow', 'crf': 18},
                'medium': {'preset': 'medium', 'crf': 23},
                'low': {'preset': 'fast', 'crf': 28}
            }
            
            video_settings = quality_settings.get(quality, quality_settings['medium'])
            
            # 构建视频流
            video = input_stream.video.filter('scale', -2, -2)  # 保持宽高比
            video = ffmpeg.output(
                video,
                output_path,
                vcodec='libx264',
                preset=video_settings['preset'],
                crf=video_settings['crf']
            )
            
            # 音频设置
            if preserve_audio:
                audio = input_stream.audio
                video = ffmpeg.output(
                    video,
                    audio,
                    output_path,
                    vcodec='libx264',
                    preset=video_settings['preset'],
                    crf=video_settings['crf'],
                    acodec='aac',
                    audio_bitrate='128k'
                )
            
            # 网络优化
            if optimize_for_web:
                video = video.global_args('-movflags', '+faststart')
            
            # 执行转换
            ffmpeg.run(video, overwrite_output=True, quiet=True)
            
            print(f"✅ 转换成功: {output_path}")
            
            # 显示文件信息
            input_size = os.path.getsize(input_path)
            output_size = os.path.getsize(output_path)
            compression_ratio = (1 - output_size / input_size) * 100
            
            print(f"📊 转换结果:")
            print(f"   输入文件大小: {input_size / 1024 / 1024:.1f} MB")
            print(f"   输出文件大小: {output_size / 1024 / 1024:.1f} MB")
            print(f"   压缩率: {compression_ratio:.1f}%")
            
            return True
            
        except ffmpeg.Error as e:
            print(f"❌ 转换失败:")
            print(f"   错误信息: {e.stderr.decode() if e.stderr else str(e)}")
            return False
        except Exception as e:
            print(f"❌ 转换出错: {e}")
            return False
    
    def batch_convert(self, input_dir, output_dir=None, quality='medium'):
        """批量转换视频"""
        if not os.path.exists(input_dir):
            print(f"❌ 输入目录不存在: {input_dir}")
            return
        
        if output_dir is None:
            output_dir = os.path.join(input_dir, 'converted')
        
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"📁 批量转换目录: {input_dir}")
        print(f"📁 输出目录: {output_dir}")
        
        converted_count = 0
        total_count = 0
        
        for filename in os.listdir(input_dir):
            if any(filename.lower().endswith(ext) for ext in self.supported_input_formats):
                total_count += 1
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, f"{Path(filename).stem}_converted{self.output_format}")
                
                print(f"\n📹 处理文件 {total_count}: {filename}")
                if self.convert_video(input_path, output_path, quality):
                    converted_count += 1
        
        print(f"\n🎉 批量转换完成!")
        print(f"   总文件数: {total_count}")
        print(f"   成功转换: {converted_count}")
        print(f"   失败数量: {total_count - converted_count}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GolfTracker 视频格式转换工具')
    parser.add_argument('input', help='输入视频文件或目录路径')
    parser.add_argument('-o', '--output', help='输出文件或目录路径')
    parser.add_argument('-q', '--quality', choices=['high', 'medium', 'low'], 
                       default='medium', help='转换质量 (默认: medium)')
    parser.add_argument('-b', '--batch', action='store_true', 
                       help='批量转换模式')
    parser.add_argument('--no-audio', action='store_true', 
                       help='不保留音频')
    parser.add_argument('--no-web-optimize', action='store_true', 
                       help='不进行网络优化')
    
    args = parser.parse_args()
    
    converter = VideoConverter()
    
    print("🎥 GolfTracker 视频格式转换工具")
    print("=" * 50)
    
    if args.batch:
        # 批量转换模式
        converter.batch_convert(args.input, args.output, args.quality)
    else:
        # 单文件转换模式
        success = converter.convert_video(
            args.input, 
            args.output, 
            args.quality,
            preserve_audio=not args.no_audio,
            optimize_for_web=not args.no_web_optimize
        )
        
        if success:
            print(f"\n🎉 转换完成!")
            print(f"现在可以在GolfTracker中使用转换后的视频文件")
        else:
            print(f"\n❌ 转换失败，请检查错误信息")

if __name__ == "__main__":
    main()
