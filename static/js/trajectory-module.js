// 轨迹图表模块
class TrajectoryModule {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // 监听结果更新事件
        document.addEventListener('resultsUpdated', (event) => {
            setTimeout(() => {
                this.createTrajectoryChart(event.detail);
            }, 300);
        });
    }

    createTrajectoryChart(data) {
        const clubHeadInfo = document.getElementById('clubHeadInfo');
        if (!clubHeadInfo) {
            console.log('等待clubHeadInfo创建...');
            setTimeout(() => this.createTrajectoryChart(data), 200);
            return;
        }

        console.log('创建轨迹图表:', { clubHeadInfo, exists: !!clubHeadInfo });

        // 检查是否已存在轨迹图表
        if (document.getElementById('trajectoryChart')) {
            return;
        }

        const trajectoryChart = document.createElement('div');
        trajectoryChart.className = 'trajectory-chart';
        trajectoryChart.id = 'trajectoryChart';
        trajectoryChart.innerHTML = `
            <canvas id="trajectoryCanvas" width="800" height="400"></canvas>
        `;

        clubHeadInfo.appendChild(trajectoryChart);
        console.log('轨迹图表创建完成:', trajectoryChart);

        // 绘制轨迹
        this.drawTrajectoryChart(data);
    }

    drawTrajectoryChart(data) {
        const canvas = document.getElementById('trajectoryCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // 清除画布
        ctx.clearRect(0, 0, width, height);

        // 过滤掉零值坐标
        const validPoints = data.club_head_trajectory.filter(point => point[0] > 0 && point[1] > 0);
        
        if (validPoints.length === 0) {
            ctx.fillStyle = '#666';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('没有有效的轨迹数据', width / 2, height / 2);
            return;
        }

        // 计算坐标范围
        const xCoords = validPoints.map(point => point[0]);
        const yCoords = validPoints.map(point => point[1]);
        
        const minX = Math.min(...xCoords);
        const maxX = Math.max(...xCoords);
        const minY = Math.min(...yCoords);
        const maxY = Math.max(...yCoords);

        console.log('轨迹坐标范围:', { minX, maxX, minY, maxY });

        // 计算缩放比例
        const padding = 40;
        const scaleX = (width - padding * 2) / (maxX - minX);
        const scaleY = (height - padding * 2) / (maxY - minY);

        // 绘制坐标轴
        ctx.strokeStyle = '#ccc';
        ctx.lineWidth = 1;
        
        // X轴
        ctx.beginPath();
        ctx.moveTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();
        
        // Y轴
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.stroke();

        // 绘制轨迹点
        ctx.strokeStyle = '#4facfe';
        ctx.lineWidth = 2;
        ctx.beginPath();

        validPoints.forEach((point, index) => {
            const x = padding + (point[0] - minX) * scaleX;
            const y = height - padding - (point[1] - minY) * scaleY;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        // 绘制关键点
        ctx.fillStyle = '#ff4757';
        validPoints.forEach((point, index) => {
            const x = padding + (point[0] - minX) * scaleX;
            const y = height - padding - (point[1] - minY) * scaleY;
            
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, 2 * Math.PI);
            ctx.fill();
        });

        // 添加轴标签
        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        
        // X轴标签
        ctx.fillText('X坐标 (像素)', width / 2, height - 10);
        
        // Y轴标签
        ctx.save();
        ctx.translate(20, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('Y坐标 (像素)', 0, 0);
        ctx.restore();
    }
}

// 创建全局实例
window.trajectoryModule = new TrajectoryModule();
console.log('✅ trajectoryModule 已创建并加载到全局作用域');
