from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import time
import psutil
import torch
from datetime import datetime, timedelta
import json
import subprocess
import os

router = APIRouter()

# 从工具模块导入 metrics_history
from app.utils.metrics_store import get_metrics_history
from app.utils.metrics_persistence import metrics_persistence

def get_gpu_info():
    """获取 GPU 信息"""
    gpu_info = {
        "available": False,
        "device_name": "N/A",
        "memory_total": 0,
        "memory_used": 0,
        "memory_free": 0,
        "utilization": 0,
        "temperature": 0,
        "power_usage": 0
    }
    
    try:
        # 检查 CUDA 是否可用
        if torch.cuda.is_available():
            gpu_info["available"] = True
            gpu_info["device_name"] = torch.cuda.get_device_name(0)
            
            # 获取 GPU 内存信息
            memory_total = torch.cuda.get_device_properties(0).total_memory
            memory_allocated = torch.cuda.memory_allocated(0)
            memory_cached = torch.cuda.memory_reserved(0)
            
            gpu_info["memory_total"] = memory_total / (1024**3)  # GB
            gpu_info["memory_used"] = memory_allocated / (1024**3)  # GB
            gpu_info["memory_free"] = (memory_total - memory_allocated) / (1024**3)  # GB
            
            # 尝试使用 nvidia-smi 获取更详细的信息
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu,power.draw', '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if lines and lines[0]:
                        parts = lines[0].split(', ')
                        if len(parts) >= 3:
                            gpu_info["utilization"] = float(parts[0])
                            gpu_info["temperature"] = float(parts[1])
                            gpu_info["power_usage"] = float(parts[2])
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                pass
                
    except Exception as e:
        print(f"获取 GPU 信息失败: {e}")
    
    return gpu_info

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
                
                <!-- GPU 详细信息卡片 -->
                <div class="card">
                    <h3>🎮 GPU 状态 (RTX 5090)</h3>
                    <div id="gpu-details">
                        <div class="metric-label">设备名称</div>
                        <div class="metric-value" id="gpu-device">检查中...</div>
                        
                        <div class="metric-label">GPU 使用率</div>
                        <div class="metric-value" id="gpu-utilization">0%</div>
                        
                        <div class="metric-label">显存使用</div>
                        <div class="metric-value" id="gpu-memory">0GB / 0GB</div>
                        
                        <div class="metric-label">温度</div>
                        <div class="metric-value" id="gpu-temperature">0°C</div>
                        
                        <div class="metric-label">功耗</div>
                        <div class="metric-value" id="gpu-power">0W</div>
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
                
                <!-- GPU使用率时间曲线 -->
                <div class="card">
                    <h3>🎮 GPU使用率趋势</h3>
                    <div class="chart-container">
                        <canvas id="gpuUsageChart"></canvas>
                    </div>
                </div>
                
                <!-- 请求分布时间曲线 -->
                <div class="card">
                    <h3>📈 请求分布趋势 (每5秒增量)</h3>
                    <div class="chart-container">
                        <canvas id="requestTrendChart"></canvas>
                    </div>
                </div>
                
                <!-- 请求分布饼图 -->
                <div class="card">
                    <h3>🎯 请求分布（当前）</h3>
                    <div class="chart-container">
                        <canvas id="requestChart"></canvas>
                    </div>
                </div>
                
                <!-- App 端点统计 -->
                <div class="card">
                    <h3>📱 App 端点统计</h3>
                    <div id="appEndpointStats">
                        <p>加载中...</p>
                    </div>
                </div>
                
                <!-- 端点性能详情 -->
                <div class="card">
                    <h3>📈 端点性能详情</h3>
                    <div id="endpointDetails">
                        <p>加载中...</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let responseTimeChart, resourceChart, requestChart, gpuUsageChart, requestTrendChart;
            
            // 历史数据存储
            let gpuUsageHistory = [];
            let requestTrendHistory = [];
            let lastRequestCounts = {}; // 存储上次的请求计数
            
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
                
                // 请求分布图表（饼图）
                const requestCtx = document.getElementById('requestChart').getContext('2d');
                requestChart = new Chart(requestCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['视频分析', '快速分析', '状态查询', '健康检查', '监控状态'],
                        datasets: [{
                            data: [0, 0, 0, 0, 0],
                            backgroundColor: ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#E91E63']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'bottom'
                            }
                        }
                    }
                });
                
                // GPU使用率时间曲线
                const gpuUsageCtx = document.getElementById('gpuUsageChart').getContext('2d');
                gpuUsageChart = new Chart(gpuUsageCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'GPU使用率 (%)',
                            data: [],
                            borderColor: '#FF6B6B',
                            backgroundColor: 'rgba(255, 107, 107, 0.1)',
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { 
                                beginAtZero: true,
                                max: 100,
                                ticks: {
                                    callback: function(value) {
                                        return value + '%';
                                    }
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
                
                // 请求分布时间曲线
                const requestTrendCtx = document.getElementById('requestTrendChart').getContext('2d');
                requestTrendChart = new Chart(requestTrendCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [
                            {
                                label: '视频分析 (增量)',
                                data: [],
                                borderColor: '#4CAF50',
                                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: '快速分析 (增量)',
                                data: [],
                                borderColor: '#2196F3',
                                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: '状态查询 (增量)',
                                data: [],
                                borderColor: '#FF9800',
                                backgroundColor: 'rgba(255, 152, 0, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: '健康检查 (增量)',
                                data: [],
                                borderColor: '#9C27B0',
                                backgroundColor: 'rgba(156, 39, 176, 0.1)',
                                tension: 0.4
                            }
                        ]
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
                document.getElementById('gpu-usage').textContent = data.gpu_info?.utilization || 0 + '%';
                
                // 更新 GPU 详细信息
                if (data.gpu_info) {
                    document.getElementById('gpu-device').textContent = data.gpu_info.device_name || 'N/A';
                    document.getElementById('gpu-utilization').textContent = data.gpu_info.utilization + '%';
                    document.getElementById('gpu-memory').textContent = 
                        `${data.gpu_info.memory_used.toFixed(1)}GB / ${data.gpu_info.memory_total.toFixed(1)}GB`;
                    document.getElementById('gpu-temperature').textContent = data.gpu_info.temperature + '°C';
                    document.getElementById('gpu-power').textContent = data.gpu_info.power_usage + 'W';
                }
                
                document.getElementById('total-requests').textContent = data.total_requests;
                document.getElementById('avg-response-time').textContent = data.avg_response_time + 'ms';
                document.getElementById('error-rate').textContent = data.error_rate + '%';
            }
            
            // 更新图表
            function updateCharts(data) {
                console.log('更新图表数据:', data);
                
                const now = new Date().toLocaleTimeString();
                
                // 更新响应时间图表
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
                
                // 更新GPU使用率时间曲线
                gpuUsageChart.data.labels.push(now);
                gpuUsageChart.data.datasets[0].data.push(data.gpu_info.utilization || 0);
                
                if (gpuUsageChart.data.labels.length > 20) {
                    gpuUsageChart.data.labels.shift();
                    gpuUsageChart.data.datasets[0].data.shift();
                }
                gpuUsageChart.update();
                
                // 更新请求分布时间曲线 - 计算增量
                requestTrendChart.data.labels.push(now);
                
                // 计算各端点的请求增量
                const currentVideoRequests = data.request_counts['/analyze/video'] || 0;
                const currentAnalyzeRequests = data.request_counts['/analyze/analyze'] || 0;
                const currentStatusRequests = data.request_counts['/analyze/video/status'] || 0;
                const currentHealthRequests = data.request_counts['/healthz'] || 0;
                
                const lastVideoRequests = lastRequestCounts['/analyze/video'] || 0;
                const lastAnalyzeRequests = lastRequestCounts['/analyze/analyze'] || 0;
                const lastStatusRequests = lastRequestCounts['/analyze/video/status'] || 0;
                const lastHealthRequests = lastRequestCounts['/healthz'] || 0;
                
                // 计算增量（每5秒的请求数）
                const videoIncrement = Math.max(0, currentVideoRequests - lastVideoRequests);
                const analyzeIncrement = Math.max(0, currentAnalyzeRequests - lastAnalyzeRequests);
                const statusIncrement = Math.max(0, currentStatusRequests - lastStatusRequests);
                const healthIncrement = Math.max(0, currentHealthRequests - lastHealthRequests);
                
                requestTrendChart.data.datasets[0].data.push(videoIncrement);
                requestTrendChart.data.datasets[1].data.push(analyzeIncrement);
                requestTrendChart.data.datasets[2].data.push(statusIncrement);
                requestTrendChart.data.datasets[3].data.push(healthIncrement);
                
                // 更新上次的请求计数
                lastRequestCounts['/analyze/video'] = currentVideoRequests;
                lastRequestCounts['/analyze/analyze'] = currentAnalyzeRequests;
                lastRequestCounts['/analyze/video/status'] = currentStatusRequests;
                lastRequestCounts['/healthz'] = currentHealthRequests;
                
                if (requestTrendChart.data.labels.length > 20) {
                    requestTrendChart.data.labels.shift();
                    requestTrendChart.data.datasets.forEach(dataset => {
                        dataset.data.shift();
                    });
                }
                requestTrendChart.update();
                
                // 更新请求分布饼图 - 包含 App 主要端点
                const requestData = [
                    currentVideoRequests,
                    currentAnalyzeRequests,
                    currentStatusRequests,
                    currentHealthRequests,
                    data.request_counts['/monitoring/api/status'] || 0
                ];
                console.log('请求分布数据:', requestData);
                requestChart.data.datasets[0].data = requestData;
                requestChart.update();
                
                // 更新 App 端点统计
                updateAppEndpointStats(data);
            }
            
            // 更新 App 端点统计
            function updateAppEndpointStats(data) {
                if (!data.app_endpoint_stats) return;
                
                const statsContainer = document.getElementById('appEndpointStats');
                let html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">';
                
                // 按类别显示统计
                const categories = {};
                Object.entries(data.app_endpoint_stats).forEach(([endpoint, stats]) => {
                    if (!categories[stats.category]) {
                        categories[stats.category] = [];
                    }
                    categories[stats.category].push({endpoint, ...stats});
                });
                
                Object.entries(categories).forEach(([category, endpoints]) => {
                    const categoryNames = {
                        'analysis': '📊 分析服务',
                        'status': '📈 状态查询',
                        'health': '❤️ 健康检查',
                        'monitoring': '📱 监控服务',
                        'conversion': '🔄 转换服务',
                        'config': '⚙️ 配置服务'
                    };
                    
                    html += `<div style="border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: #f9f9f9;">`;
                    html += `<h4 style="margin: 0 0 10px 0; color: #333;">${categoryNames[category] || category}</h4>`;
                    
                    endpoints.forEach(endpoint => {
                        const statusColor = endpoint.error_rate > 10 ? '#f44336' : endpoint.error_rate > 5 ? '#ff9800' : '#4caf50';
                        const lastRequest = endpoint.last_request ? 
                            new Date(endpoint.last_request * 1000).toLocaleTimeString() : '无';
                        
                        html += `<div style="margin-bottom: 8px; padding: 5px; background: white; border-radius: 4px;">`;
                        html += `<div style="font-weight: bold; color: #333;">${endpoint.name}</div>`;
                        html += `<div style="font-size: 11px; color: #888; font-family: monospace; background: #f5f5f5; padding: 2px 4px; border-radius: 3px; margin: 2px 0;">${endpoint.endpoint}</div>`;
                        html += `<div style="font-size: 12px; color: #666;">请求: ${endpoint.request_count} | 响应: ${endpoint.avg_response_time}ms</div>`;
                        html += `<div style="font-size: 12px; color: ${statusColor};">错误率: ${endpoint.error_rate}% | 最后: ${lastRequest}</div>`;
                        html += `</div>`;
                    });
                    
                    html += `</div>`;
                });
                
                html += '</div>';
                statsContainer.innerHTML = html;
                
                // 更新端点性能详情
                updateEndpointDetails(data);
            }
            
            // 更新端点性能详情
            function updateEndpointDetails(data) {
                if (!data.app_endpoint_stats) return;
                
                const detailsContainer = document.getElementById('endpointDetails');
                let html = '<div style="overflow-x: auto;">';
                html += '<table style="width: 100%; border-collapse: collapse; font-size: 12px;">';
                html += '<thead><tr style="background: #f5f5f5;">';
                html += '<th style="padding: 8px; border: 1px solid #ddd;">端点</th>';
                html += '<th style="padding: 8px; border: 1px solid #ddd;">类型</th>';
                html += '<th style="padding: 8px; border: 1px solid #ddd;">请求数</th>';
                html += '<th style="padding: 8px; border: 1px solid #ddd;">平均响应(ms)</th>';
                html += '<th style="padding: 8px; border: 1px solid #ddd;">最小/最大(ms)</th>';
                html += '<th style="padding: 8px; border: 1px solid #ddd;">错误数</th>';
                html += '<th style="padding: 8px; border: 1px solid #ddd;">错误率</th>';
                html += '<th style="padding: 8px; border: 1px solid #ddd;">状态码</th>';
                html += '</tr></thead><tbody>';
                
                Object.entries(data.app_endpoint_stats).forEach(([endpoint, stats]) => {
                    if (stats.request_count > 0) {
                        const statusCodes = Object.entries(stats.status_codes)
                            .map(([code, count]) => `${code}(${count})`)
                            .join(', ');
                        
                        html += '<tr>';
                        html += `<td style="padding: 8px; border: 1px solid #ddd;">
                            <div style="font-weight: bold;">${stats.name}</div>
                            <div style="font-size: 10px; color: #666; font-family: monospace; background: #f5f5f5; padding: 2px 4px; border-radius: 3px; margin-top: 2px;">${endpoint}</div>
                        </td>`;
                        html += `<td style="padding: 8px; border: 1px solid #ddd;">${stats.type}</td>`;
                        html += `<td style="padding: 8px; border: 1px solid #ddd;">${stats.request_count}</td>`;
                        html += `<td style="padding: 8px; border: 1px solid #ddd;">${stats.avg_response_time}</td>`;
                        html += `<td style="padding: 8px; border: 1px solid #ddd;">${stats.min_response_time}/${stats.max_response_time}</td>`;
                        html += `<td style="padding: 8px; border: 1px solid #ddd; color: ${stats.error_count > 0 ? '#f44336' : '#4caf50'};">${stats.error_count}</td>`;
                        html += `<td style="padding: 8px; border: 1px solid #ddd; color: ${stats.error_rate > 10 ? '#f44336' : stats.error_rate > 5 ? '#ff9800' : '#4caf50'};">${stats.error_rate}%</td>`;
                        html += `<td style="padding: 8px; border: 1px solid #ddd; font-size: 10px;">${statusCodes}</td>`;
                        html += '</tr>';
                    }
                });
                
                html += '</tbody></table></div>';
                detailsContainer.innerHTML = html;
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
        gpu_info = get_gpu_info()
        
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
        
        # App 主要端点详细统计
        app_endpoints = {
            "/analyze/video": {"name": "视频分析(异步)", "type": "POST", "category": "analysis"},
            "/analyze/analyze": {"name": "快速分析(同步)", "type": "POST", "category": "analysis"},
            "/analyze/video/status": {"name": "分析状态查询", "type": "GET", "category": "status"},
            "/healthz": {"name": "健康检查", "type": "GET", "category": "health"},
            "/monitoring/api/status": {"name": "监控状态", "type": "GET", "category": "monitoring"},
            "/convert/convert": {"name": "视频转换", "type": "POST", "category": "conversion"},
            "/analyze/strategies": {"name": "策略查询", "type": "GET", "category": "config"}
        }
        
        # 分析每个 App 端点的详细统计
        app_endpoint_stats = {}
        for endpoint, info in app_endpoints.items():
            endpoint_requests = [req for req in recent_requests if req["endpoint"] == endpoint]
            if endpoint_requests:
                response_times = [req["response_time"] for req in endpoint_requests]
                status_codes = [req["status_code"] for req in endpoint_requests]
                errors = [req for req in endpoint_requests if req["status_code"] >= 400]
                
                app_endpoint_stats[endpoint] = {
                    "name": info["name"],
                    "type": info["type"],
                    "category": info["category"],
                    "request_count": len(endpoint_requests),
                    "avg_response_time": round(sum(response_times) / len(response_times), 1),
                    "min_response_time": round(min(response_times), 1),
                    "max_response_time": round(max(response_times), 1),
                    "error_count": len(errors),
                    "error_rate": round((len(errors) / len(endpoint_requests)) * 100, 1),
                    "status_codes": {str(code): status_codes.count(code) for code in set(status_codes)},
                    "last_request": max([req["timestamp"] for req in endpoint_requests]) if endpoint_requests else None
                }
            else:
                app_endpoint_stats[endpoint] = {
                    "name": info["name"],
                    "type": info["type"],
                    "category": info["category"],
                    "request_count": 0,
                    "avg_response_time": 0,
                    "min_response_time": 0,
                    "max_response_time": 0,
                    "error_count": 0,
                    "error_rate": 0,
                    "status_codes": {},
                    "last_request": None
                }
        
        # 按类别统计
        category_stats = {}
        for endpoint, stats in app_endpoint_stats.items():
            category = stats["category"]
            if category not in category_stats:
                category_stats[category] = {
                    "total_requests": 0,
                    "total_errors": 0,
                    "avg_response_time": 0,
                    "endpoints": []
                }
            category_stats[category]["total_requests"] += stats["request_count"]
            category_stats[category]["total_errors"] += stats["error_count"]
            category_stats[category]["endpoints"].append(endpoint)
        
        # 计算类别平均响应时间
        for category, stats in category_stats.items():
            if stats["total_requests"] > 0:
                total_time = sum(app_endpoint_stats[ep]["avg_response_time"] * app_endpoint_stats[ep]["request_count"] 
                               for ep in stats["endpoints"] if app_endpoint_stats[ep]["request_count"] > 0)
                stats["avg_response_time"] = round(total_time / stats["total_requests"], 1)
                stats["error_rate"] = round((stats["total_errors"] / stats["total_requests"]) * 100, 1)
        
        # 构建返回数据
        status_data = {
            "timestamp": current_time,
            "service_status": "ok",
            "cuda_available": torch.cuda.is_available(),
            "model_loaded": False,  # 这里应该检查实际的模型状态
            "cpu_usage": round(cpu_usage, 1),
            "memory_usage": round(memory_usage, 1),
            "gpu_info": gpu_info,
            "total_requests": total_requests,
            "avg_response_time": round(avg_response_time, 1),
            "error_rate": round(error_rate, 1),
            "request_counts": request_counts,
            "app_endpoint_stats": app_endpoint_stats,
            "category_stats": category_stats
        }
        
        # 保存监控数据到持久化存储
        try:
            metrics_persistence.save_metrics(status_data)
            # 每天清理一次旧数据（避免频繁清理）
            import datetime
            current_hour = datetime.datetime.now().hour
            if current_hour == 0:  # 每天凌晨0点清理
                metrics_persistence.cleanup_old_data()
        except Exception as e:
            # 数据保存失败不影响API响应
            print(f"保存监控数据失败: {e}")
        
        return status_data
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": time.time(),
            "service_status": "error"
        }

@router.get("/monitoring/api/history")
async def get_historical_metrics(days: int = 7):
    """获取历史监控数据"""
    try:
        historical_data = metrics_persistence.load_historical_metrics(days)
        return {
            "success": True,
            "days": days,
            "data_points": len(historical_data),
            "data": historical_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/monitoring/api/summary")
async def get_metrics_summary(days: int = 7):
    """获取监控数据摘要"""
    try:
        summary = metrics_persistence.get_metrics_summary(days)
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# 中间件功能将在主应用中实现
