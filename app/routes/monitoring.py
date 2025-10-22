from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import time
import psutil
import torch
from datetime import datetime, timedelta
import json

router = APIRouter()

# 从工具模块导入 metrics_history
from app.utils.metrics_store import get_metrics_history

@router.get("/monitoring/dashboard")
async def monitoring_dashboard():
    """监控仪表板页面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GolfTracker 监控仪表板</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
            .status-ok { background-color: #4CAF50; }
            .status-warning { background-color: #FF9800; }
            .status-error { background-color: #F44336; }
            .metric-value { font-size: 24px; font-weight: bold; color: #333; }
            .metric-label { color: #666; margin-bottom: 5px; }
            .chart-container { position: relative; height: 300px; }
            .refresh-btn { background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 20px; }
            .refresh-btn:hover { background: #5a6fd8; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏌️ GolfTracker 监控仪表板</h1>
                <p>实时系统状态和性能监控</p>
                <button class="refresh-btn" onclick="refreshData()">🔄 刷新数据</button>
            </div>
            
            <div class="grid">
                <!-- 系统状态卡片 -->
                <div class="card">
                    <h3>📊 系统状态</h3>
                    <div id="system-status">
                        <div class="metric-label">服务状态</div>
                        <div class="metric-value" id="service-status">检查中...</div>
                        
                        <div class="metric-label">CUDA 状态</div>
                        <div class="metric-value" id="cuda-status">检查中...</div>
                        
                        <div class="metric-label">模型状态</div>
                        <div class="metric-value" id="model-status">检查中...</div>
                    </div>
                </div>
                
                <!-- 性能指标卡片 -->
                <div class="card">
                    <h3>⚡ 性能指标</h3>
                    <div id="performance-metrics">
                        <div class="metric-label">CPU 使用率</div>
                        <div class="metric-value" id="cpu-usage">0%</div>
                        
                        <div class="metric-label">内存使用率</div>
                        <div class="metric-value" id="memory-usage">0%</div>
                        
                        <div class="metric-label">GPU 使用率</div>
                        <div class="metric-value" id="gpu-usage">0%</div>
                    </div>
                </div>
                
                <!-- 请求统计卡片 -->
                <div class="card">
                    <h3>📈 请求统计</h3>
                    <div id="request-stats">
                        <div class="metric-label">总请求数</div>
                        <div class="metric-value" id="total-requests">0</div>
                        
                        <div class="metric-label">平均响应时间</div>
                        <div class="metric-value" id="avg-response-time">0ms</div>
                        
                        <div class="metric-label">错误率</div>
                        <div class="metric-value" id="error-rate">0%</div>
                    </div>
                </div>
                
                <!-- 响应时间图表 -->
                <div class="card">
                    <h3>📊 响应时间趋势</h3>
                    <div class="chart-container">
                        <canvas id="responseTimeChart"></canvas>
                    </div>
                </div>
                
                <!-- 系统资源图表 -->
                <div class="card">
                    <h3>💻 系统资源使用</h3>
                    <div class="chart-container">
                        <canvas id="resourceChart"></canvas>
                    </div>
                </div>
                
                <!-- 请求分布图表 -->
                <div class="card">
                    <h3>🎯 请求分布</h3>
                    <div class="chart-container">
                        <canvas id="requestChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let responseTimeChart, resourceChart, requestChart;
            
            // 初始化图表
            function initCharts() {
                // 响应时间图表
                const responseCtx = document.getElementById('responseTimeChart').getContext('2d');
                responseTimeChart = new Chart(responseCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: '响应时间 (ms)',
                            data: [],
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
                
                // 系统资源图表
                const resourceCtx = document.getElementById('resourceChart').getContext('2d');
                resourceChart = new Chart(resourceCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['CPU', '内存', 'GPU'],
                        datasets: [{
                            data: [0, 0, 0],
                            backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
                
                // 请求分布图表
                const requestCtx = document.getElementById('requestChart').getContext('2d');
                requestChart = new Chart(requestCtx, {
                    type: 'bar',
                    data: {
                        labels: ['/healthz', '/metrics', '/health', '/monitoring'],
                        datasets: [{
                            label: '请求次数',
                            data: [0, 0, 0, 0],
                            backgroundColor: ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { 
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                display: true
                            }
                        }
                    }
                });
            }
            
            // 刷新数据
            async function refreshData() {
                try {
                    const response = await fetch('/monitoring/api/status');
                    const data = await response.json();
                    
                    // 更新系统状态
                    updateSystemStatus(data);
                    
                    // 更新图表
                    updateCharts(data);
                    
                } catch (error) {
                    console.error('刷新数据失败:', error);
                }
            }
            
            // 更新系统状态
            function updateSystemStatus(data) {
                document.getElementById('service-status').innerHTML = 
                    `<span class="status-indicator ${data.service_status === 'ok' ? 'status-ok' : 'status-warning'}"></span>${data.service_status}`;
                
                document.getElementById('cuda-status').innerHTML = 
                    `<span class="status-indicator ${data.cuda_available ? 'status-ok' : 'status-error'}"></span>${data.cuda_available ? '可用' : '不可用'}`;
                
                document.getElementById('model-status').innerHTML = 
                    `<span class="status-indicator ${data.model_loaded ? 'status-ok' : 'status-warning'}"></span>${data.model_loaded ? '已加载' : '未加载'}`;
                
                document.getElementById('cpu-usage').textContent = data.cpu_usage + '%';
                document.getElementById('memory-usage').textContent = data.memory_usage + '%';
                document.getElementById('gpu-usage').textContent = data.gpu_usage + '%';
                
                document.getElementById('total-requests').textContent = data.total_requests;
                document.getElementById('avg-response-time').textContent = data.avg_response_time + 'ms';
                document.getElementById('error-rate').textContent = data.error_rate + '%';
            }
            
            // 更新图表
            function updateCharts(data) {
                console.log('更新图表数据:', data);
                
                // 更新响应时间图表
                const now = new Date().toLocaleTimeString();
                responseTimeChart.data.labels.push(now);
                responseTimeChart.data.datasets[0].data.push(data.avg_response_time);
                
                if (responseTimeChart.data.labels.length > 20) {
                    responseTimeChart.data.labels.shift();
                    responseTimeChart.data.datasets[0].data.shift();
                }
                responseTimeChart.update();
                
                // 更新资源使用图表
                resourceChart.data.datasets[0].data = [
                    data.cpu_usage, 
                    data.memory_usage, 
                    data.gpu_usage
                ];
                resourceChart.update();
                
                // 更新请求分布图表
                const requestData = [
                    data.request_counts['/healthz'] || 0,
                    data.request_counts['/metrics'] || 0,
                    data.request_counts['/health'] || 0,
                    data.request_counts['/monitoring/api/status'] || 0
                ];
                console.log('请求分布数据:', requestData);
                requestChart.data.datasets[0].data = requestData;
                requestChart.update();
            }
            
            // 页面加载完成后初始化
            document.addEventListener('DOMContentLoaded', function() {
                initCharts();
                refreshData();
                
                // 每5秒自动刷新
                setInterval(refreshData, 5000);
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/monitoring/api/status")
async def get_monitoring_status():
    """获取监控状态数据"""
    try:
        # 获取系统信息
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # 获取GPU信息
        gpu_usage = 0
        if torch.cuda.is_available():
            try:
                gpu_usage = torch.cuda.utilization(0) if hasattr(torch.cuda, 'utilization') else 0
            except:
                gpu_usage = 0
        
        # 获取请求统计数据
        metrics_history = get_metrics_history()
        current_time = time.time()
        recent_requests = [req for req in metrics_history["requests"] if current_time - req["timestamp"] < 300]  # 最近5分钟
        
        total_requests = len(recent_requests)
        avg_response_time = sum(req["response_time"] for req in recent_requests) / max(total_requests, 1)
        error_count = sum(1 for req in recent_requests if req["status_code"] >= 400)
        error_rate = (error_count / max(total_requests, 1)) * 100
        
        # 请求分布统计
        request_counts = {}
        for req in recent_requests:
            endpoint = req["endpoint"]
            request_counts[endpoint] = request_counts.get(endpoint, 0) + 1
        
        return {
            "timestamp": current_time,
            "service_status": "ok",
            "cuda_available": torch.cuda.is_available(),
            "model_loaded": False,  # 这里应该检查实际的模型状态
            "cpu_usage": round(cpu_usage, 1),
            "memory_usage": round(memory_usage, 1),
            "gpu_usage": round(gpu_usage, 1),
            "total_requests": total_requests,
            "avg_response_time": round(avg_response_time, 1),
            "error_rate": round(error_rate, 1),
            "request_counts": request_counts
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": time.time(),
            "service_status": "error"
        }

# 中间件功能将在主应用中实现
