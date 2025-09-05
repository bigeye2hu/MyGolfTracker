// 挥杆状态可视化模块
class SwingVisualizationModule {
    constructor() {
        this.currentAnalysisData = null;
        this.currentVideoFile = null;
    }

    init() {
        console.log('初始化挥杆状态可视化模块...');
        this.bindEvents();
    }

    bindEvents() {
        // 监听分析完成事件
        document.addEventListener('analysisComplete', (event) => {
            console.log('收到分析完成事件，开始渲染挥杆状态可视化');
            this.renderSwingVisualization(event.detail);
        });
    }

    renderSwingVisualization(data) {
        console.log('渲染挥杆状态可视化:', data);
        
        if (!data || !data.result) {
            console.error('没有分析数据');
            return;
        }

        this.currentAnalysisData = data.result;
        
        // 创建可视化区域
        this.createVisualizationArea();
        
        // 渲染轨迹图
        this.renderTrajectoryChart();
        
        // 渲染状态统计
        this.renderStateStatistics();
        
        // 渲染帧级信息
        this.renderFrameDetails();
    }

    createVisualizationArea() {
        const resultsSection = document.getElementById('resultsSection');
        
        // 检查是否已存在可视化区域
        let visualizationArea = document.getElementById('swingVisualization');
        if (!visualizationArea) {
            visualizationArea = document.createElement('div');
            visualizationArea.id = 'swingVisualization';
            visualizationArea.className = 'result-card';
            resultsSection.appendChild(visualizationArea);
        }

        visualizationArea.innerHTML = `
            <h3>🎯 挥杆状态可视化</h3>
            <div class="visualization-container">
                <div class="trajectory-chart-container">
                    <canvas id="trajectoryChart" width="800" height="300"></canvas>
                </div>
                <div class="state-statistics">
                    <h4>状态分布统计</h4>
                    <div id="stateStats"></div>
                </div>
                <div class="frame-details">
                    <h4>帧级详细信息</h4>
                    <div id="frameDetails"></div>
                </div>
            </div>
        `;
    }

    renderTrajectoryChart() {
        const canvas = document.getElementById('trajectoryChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const data = this.currentAnalysisData;
        
        if (!data.swing_phases || !data.club_head_trajectory) {
            console.error('缺少挥杆状态或轨迹数据');
            return;
        }

        // 清空画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 设置画布样式
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 绘制网格
        this.drawGrid(ctx, canvas.width, canvas.height);

        // 绘制轨迹
        this.drawTrajectory(ctx, data.club_head_trajectory, data.swing_phases, canvas.width, canvas.height);

        // 绘制图例
        this.drawLegend(ctx, canvas.width, canvas.height);
    }

    drawGrid(ctx, width, height) {
        ctx.strokeStyle = '#e9ecef';
        ctx.lineWidth = 1;

        // 绘制水平网格线
        for (let i = 0; i <= 10; i++) {
            const y = (height - 40) * i / 10 + 20;
            ctx.beginPath();
            ctx.moveTo(40, y);
            ctx.lineTo(width - 20, y);
            ctx.stroke();
        }

        // 绘制垂直网格线
        for (let i = 0; i <= 10; i++) {
            const x = (width - 60) * i / 10 + 40;
            ctx.beginPath();
            ctx.moveTo(x, 20);
            ctx.lineTo(x, height - 20);
            ctx.stroke();
        }
    }

    drawTrajectory(ctx, trajectory, phases, width, height) {
        if (!trajectory || trajectory.length === 0) return;

        const padding = 40;
        const chartWidth = width - padding - 20;
        const chartHeight = height - padding - 20;

        // 状态颜色映射
        const stateColors = {
            'Address': '#28a745',
            'Backswing': '#007bff',
            'Transition': '#ffc107',
            'Downswing': '#dc3545',
            'Impact': '#6f42c1',
            'FollowThrough': '#fd7e14',
            'Finish': '#20c997',
            'Unknown': '#6c757d'
        };

        // 绘制轨迹点
        for (let i = 0; i < trajectory.length; i++) {
            const point = trajectory[i];
            if (!point || point.length < 2) continue;

            const x = padding + point[0] * chartWidth;
            const y = padding + (1 - point[1]) * chartHeight; // 翻转Y轴

            const phase = phases[i] || 'Unknown';
            const color = stateColors[phase] || '#6c757d';

            // 绘制点
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fill();

            // 绘制帧号（每5帧显示一次）
            if (i % 5 === 0) {
                ctx.fillStyle = '#495057';
                ctx.font = '10px Arial';
                ctx.fillText(i.toString(), x - 5, y - 8);
            }
        }

        // 绘制连接线
        ctx.strokeStyle = '#6c757d';
        ctx.lineWidth = 1;
        ctx.beginPath();
        
        let firstPoint = true;
        for (let i = 0; i < trajectory.length; i++) {
            const point = trajectory[i];
            if (!point || point.length < 2) continue;

            const x = padding + point[0] * chartWidth;
            const y = padding + (1 - point[1]) * chartHeight;

            if (firstPoint) {
                ctx.moveTo(x, y);
                firstPoint = false;
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();
    }

    drawLegend(ctx, width, height) {
        const stateColors = {
            'Address': '#28a745',
            'Backswing': '#007bff',
            'Transition': '#ffc107',
            'Downswing': '#dc3545',
            'Impact': '#6f42c1',
            'FollowThrough': '#fd7e14',
            'Finish': '#20c997',
            'Unknown': '#6c757d'
        };

        const legendX = width - 150;
        const legendY = 20;
        const itemHeight = 20;

        ctx.font = '12px Arial';
        let y = legendY;

        Object.entries(stateColors).forEach(([state, color]) => {
            // 绘制颜色方块
            ctx.fillStyle = color;
            ctx.fillRect(legendX, y - 10, 12, 12);

            // 绘制状态名称
            ctx.fillStyle = '#495057';
            ctx.fillText(state, legendX + 20, y);

            y += itemHeight;
        });
    }

    renderStateStatistics() {
        const container = document.getElementById('stateStats');
        if (!container) return;

        const data = this.currentAnalysisData;
        if (!data.swing_phases) return;

        // 统计各状态数量
        const stateCounts = {};
        data.swing_phases.forEach(phase => {
            stateCounts[phase] = (stateCounts[phase] || 0) + 1;
        });

        const totalFrames = data.swing_phases.length;
        
        container.innerHTML = `
            <div class="state-stats-grid">
                ${Object.entries(stateCounts).map(([state, count]) => {
                    const percentage = ((count / totalFrames) * 100).toFixed(1);
                    return `
                        <div class="state-stat-item">
                            <div class="state-color" style="background-color: ${this.getStateColor(state)}"></div>
                            <div class="state-name">${state}</div>
                            <div class="state-count">${count}帧</div>
                            <div class="state-percentage">${percentage}%</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    renderFrameDetails() {
        const container = document.getElementById('frameDetails');
        if (!container) return;

        const data = this.currentAnalysisData;
        if (!data.swing_phases || !data.club_head_trajectory) return;

        // 只显示前20帧的详细信息
        const maxFrames = Math.min(20, data.swing_phases.length);
        
        container.innerHTML = `
            <div class="frame-details-list">
                ${Array.from({length: maxFrames}, (_, i) => {
                    const phase = data.swing_phases[i];
                    const point = data.club_head_trajectory[i];
                    const x = point ? point[0].toFixed(3) : 'N/A';
                    const y = point ? point[1].toFixed(3) : 'N/A';
                    
                    return `
                        <div class="frame-detail-item">
                            <div class="frame-number">帧${i + 1}</div>
                            <div class="frame-state" style="color: ${this.getStateColor(phase)}">${phase}</div>
                            <div class="frame-coords">(${x}, ${y})</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    getStateColor(state) {
        const stateColors = {
            'Address': '#28a745',
            'Backswing': '#007bff',
            'Transition': '#ffc107',
            'Downswing': '#dc3545',
            'Impact': '#6f42c1',
            'FollowThrough': '#fd7e14',
            'Finish': '#20c997',
            'Unknown': '#6c757d'
        };
        return stateColors[state] || '#6c757d';
    }
}

// 创建全局实例
window.swingVisualizationModule = new SwingVisualizationModule();
