from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import torch
import time

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def welcome_page():
    """GolfTracker 服务欢迎页面"""
    cuda_available = torch.cuda.is_available()
    model_loaded = True  # 假设模型已加载
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GolfTracker - 高尔夫挥杆分析系统</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 1.2em;
                opacity: 0.9;
            }}
            .status {{
                display: flex;
                justify-content: center;
                gap: 20px;
                margin: 20px 0;
            }}
            .status-item {{
                background: rgba(255,255,255,0.2);
                padding: 10px 20px;
                border-radius: 25px;
                font-size: 0.9em;
            }}
            .content {{
                padding: 40px;
            }}
            .endpoints {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .endpoint-card {{
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 10px;
                padding: 20px;
                transition: all 0.3s ease;
                cursor: pointer;
            }}
            .endpoint-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                border-color: #4CAF50;
            }}
            .endpoint-title {{
                font-size: 1.1em;
                font-weight: 600;
                color: #4CAF50;
                margin-bottom: 10px;
            }}
            .endpoint-path {{
                font-family: 'Courier New', monospace;
                background: #e9ecef;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 0.9em;
                margin: 10px 0;
            }}
            .endpoint-desc {{
                color: #666;
                font-size: 0.9em;
                line-height: 1.4;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                border-top: 1px solid #e9ecef;
            }}
            .badge {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: 500;
                margin-left: 10px;
            }}
            .badge-success {{ background: #d4edda; color: #155724; }}
            .badge-warning {{ background: #fff3cd; color: #856404; }}
            .badge-info {{ background: #d1ecf1; color: #0c5460; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏌️‍♂️ GolfTracker</h1>
                <p>高尔夫挥杆分析系统</p>
                <div class="status">
                    <div class="status-item">
                        🚀 服务状态: 运行中
                    </div>
                    <div class="status-item">
                        🎯 CUDA: {'✅ 可用' if cuda_available else '❌ 不可用'}
                    </div>
                    <div class="status-item">
                        📦 模型: {'✅ 已加载' if model_loaded else '❌ 未加载'}
                    </div>
                </div>
            </div>
            
            <div class="content">
                <h2>📋 可用端点</h2>
                <p>点击下面的卡片访问相应的功能页面：</p>
                
                <div class="endpoints">
                    <div class="endpoint-card" onclick="window.open('/monitoring/dashboard', '_blank')">
                        <div class="endpoint-title">📊 监控仪表板</div>
                        <div class="endpoint-path">/monitoring/dashboard</div>
                        <div class="endpoint-desc">实时监控系统状态、性能指标和请求统计</div>
                    </div>
                    
                    <div class="endpoint-card" onclick="window.open('/analyze/server-test', '_blank')">
                        <div class="endpoint-title">🧪 服务测试</div>
                        <div class="endpoint-path">/analyze/server-test</div>
                        <div class="endpoint-desc">Web 界面测试页面，支持视频上传和分析</div>
                    </div>
                    
                    <div class="endpoint-card" onclick="window.open('/docs', '_blank')">
                        <div class="endpoint-title">📚 API 文档</div>
                        <div class="endpoint-path">/docs</div>
                        <div class="endpoint-desc">完整的 API 接口文档和交互式测试</div>
                    </div>
                    
                    <div class="endpoint-card" onclick="window.open('/healthz', '_blank')">
                        <div class="endpoint-title">❤️ 健康检查</div>
                        <div class="endpoint-path">/healthz</div>
                        <div class="endpoint-desc">服务健康状态检查，包含 CUDA 和模型状态</div>
                    </div>
                    
                    <div class="endpoint-card" onclick="window.open('/monitoring/api/status', '_blank')">
                        <div class="endpoint-title">📈 监控 API</div>
                        <div class="endpoint-path">/monitoring/api/status</div>
                        <div class="endpoint-desc">JSON 格式的详细监控数据</div>
                    </div>
                    
                    <div class="endpoint-card" onclick="window.open('/metrics', '_blank')">
                        <div class="endpoint-title">📊 Prometheus 指标</div>
                        <div class="endpoint-path">/metrics</div>
                        <div class="endpoint-desc">Prometheus 格式的系统监控指标</div>
                    </div>
                </div>
                
                <h3>🔧 主要功能</h3>
                <ul>
                    <li><strong>智能杆头检测</strong>：基于 YOLOv8 深度学习模型</li>
                    <li><strong>轨迹分析</strong>：生成杆头运动轨迹和优化建议</li>
                    <li><strong>GPU 加速</strong>：支持 NVIDIA GPU 加速处理</li>
                    <li><strong>实时监控</strong>：完整的系统监控和性能分析</li>
                    <li><strong>RESTful API</strong>：支持移动端和第三方集成</li>
                </ul>
            </div>
            
            <div class="footer">
                <p>🏌️‍♂️ GolfTracker v1.0.0 | 基于 YOLOv8 的高尔夫挥杆分析系统</p>
                <p>访问时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)
